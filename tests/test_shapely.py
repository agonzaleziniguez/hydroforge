"""Shapely behaviour that HydroForge relies on.

If one of these tests fails after a Shapely update, review the HydroForge code
that depends on it.
"""

# Shapely's type hints are partial. Ignore unknown types from its vectorized functions.
# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportAny=false

import numpy as np
import pytest
import shapely

# The reference square has corners (0, 0), (10, 0), (10, 10) and (0, 10).
REFERENCE = shapely.box(0, 0, 10, 10)
TOLERANCE = 1.0


def test_snap_moves_vertices_to_reference_vertices() -> None:
    moving = shapely.box(10.5, 0, 20, 10)

    snapped = shapely.snap(moving, REFERENCE, TOLERANCE)

    assert snapped.equals_exact(shapely.box(10, 0, 20, 10), 0)


def test_snap_inserts_reference_vertices_into_edges() -> None:
    moving = shapely.box(10.5, -5, 20, 15)

    snapped = shapely.snap(moving, REFERENCE, TOLERANCE)

    expected = shapely.Polygon(
        [(20, -5), (20, 15), (10.5, 15), (10, 10), (10, 0), (10.5, -5), (20, -5)]
    )
    assert snapped.equals_exact(expected, 0)


@pytest.mark.parametrize(
    "moving",
    [shapely.box(11, 0, 20, 10), shapely.box(11, -5, 20, 15)],
    ids=["move-vertices", "insert-vertices"],
)
def test_snap_ignores_distance_equal_to_tolerance(moving: shapely.Polygon) -> None:
    """Snapping needs distance < tolerance. HydroForge adds 1 mm to include equality."""
    snapped = shapely.snap(moving, REFERENCE, TOLERANCE)

    assert snapped.equals_exact(moving, 0)


def test_snap_onto_several_reference_polygons() -> None:
    """One part can snap onto edges from several polygons in one call."""
    east = shapely.box(20, 0, 30, 10)
    reference = shapely.MultiLineString([REFERENCE.exterior, east.exterior])
    moving = shapely.box(10.5, 0, 19.5, 10)

    snapped = shapely.snap(moving, reference, TOLERANCE)

    assert snapped.equals_exact(shapely.box(10, 0, 20, 10), 0)


@pytest.mark.parametrize("reverse", [False, True], ids=["in-order", "reversed"])
def test_snap_picks_the_closest_reference_vertex(reverse: bool) -> None:
    """The corner (10.3, 10.5) is 0.58 from (10, 10) and 0.42 from (10, 10.8)."""
    above = shapely.box(0, 10.8, 10, 20)
    rings = [REFERENCE.exterior, above.exterior]
    reference = shapely.MultiLineString(rings[::-1] if reverse else rings)
    moving = shapely.box(10.3, 9.6, 20, 10.5)

    snapped = shapely.snap(moving, reference, TOLERANCE)

    expected = shapely.Polygon([(20, 9.6), (20, 10.5), (10, 10.8), (10, 10), (20, 9.6)])
    assert snapped.equals_exact(expected, 0)


def test_snap_tie_depends_on_reference_order() -> None:
    """The vertex (10.4, 10.5) is 0.64 from both (10, 10) and (10, 11).

    The same reference order always gives the same result, but swapping the order
    changes which point the vertex snaps to.
    """
    moving = shapely.LineString([(10.4, 10.5), (20, 10.5)])
    first = shapely.MultiPoint([(10, 10), (10, 11)])
    second = shapely.MultiPoint([(10, 11), (10, 10)])

    results = [
        shapely.snap(moving, reference, TOLERANCE) for reference in (first, second)
    ]

    assert results[0].equals_exact(shapely.snap(moving, first, TOLERANCE), 0)
    assert not results[0].equals_exact(results[1], 0)
    assert {result.coords[0] for result in results} == {(10, 10), (10, 11)}


def test_snap_does_not_move_vertices_onto_edge_middles() -> None:
    """HydroForge adds its own projection step for this case."""
    moving = shapely.box(10.5, 3, 20, 7)

    snapped = shapely.snap(moving, REFERENCE, TOLERANCE)

    assert snapped.equals_exact(moving, 0)


def project(point: tuple[float, float], edges: shapely.Geometry) -> tuple[float, float]:
    """Return the closest point of the edges, using the end of the shortest line."""
    line = shapely.shortest_line(shapely.Point(point), edges)
    x, y = shapely.get_coordinates(line)[1]
    return float(x), float(y)


def test_shortest_line_projects_onto_straight_edge_exactly() -> None:
    assert project((10.5, 3), REFERENCE.boundary) == (10, 3)


def test_shortest_line_projects_outside_corner_onto_the_corner() -> None:
    assert project((10.4, 10.3), REFERENCE.boundary) == (10, 10)


def test_shortest_line_projects_onto_slanted_edge_only_approximately() -> None:
    """Points on a slanted edge often cannot be stored exactly.

    The projected point is within 1e-9 of the edge, but not on it. HydroForge must
    add these vertices to the reference so both edges match exactly.
    """
    x, y = 440000, 4470000
    edge = shapely.LineString([(x, y), (x + 10, y + 3)])

    end = shapely.Point(project((x + 5.2, y + 1), edge))

    assert 0 < shapely.distance(end, edge) < 1e-9


def test_get_and_set_coordinates_keep_rings_holes_and_parts() -> None:
    with_hole = shapely.Polygon(
        REFERENCE.exterior.coords, [shapely.box(2, 2, 4, 4).exterior.coords]
    )
    geometries = np.array(
        [shapely.MultiPolygon([with_hole, shapely.box(20, 0, 30, 10)]), REFERENCE]
    )
    before = geometries.copy()

    coordinates, index = shapely.get_coordinates(geometries, return_index=True)
    result = shapely.set_coordinates(geometries.copy(), coordinates + 1)

    assert index.tolist() == [0] * 15 + [1] * 5
    for original, moved in zip(before, result, strict=True):
        assert moved.equals_exact(shapely.affinity.translate(original, 1, 1), 0)
    assert all(a is b for a, b in zip(geometries, before, strict=True))


def test_set_coordinates_replaces_array_items_in_place() -> None:
    """The geometries are not changed, but the array is. Pass a copy."""
    geometries = np.array([REFERENCE])

    result = shapely.set_coordinates(
        geometries, shapely.get_coordinates(geometries) + 1
    )

    assert result is geometries
    assert geometries[0].equals_exact(shapely.box(1, 1, 11, 11), 0)
    assert REFERENCE.equals_exact(shapely.box(0, 0, 10, 10), 0)
