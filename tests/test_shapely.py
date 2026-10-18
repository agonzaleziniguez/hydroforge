"""Shapely behaviour that HydroForge relies on.

If one of these tests fails after a Shapely update, review the HydroForge code
that depends on it.
"""

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
