"""Checks for polygon coverages.

A coverage is a set of polygons that do not overlap and share exact edges
with their neighbours.
"""

from collections.abc import Hashable
from dataclasses import dataclass
from typing import cast

import geopandas as gpd
import shapely
from shapely.geometry.base import BaseGeometry


@dataclass(frozen=True)
class Problem:
    """A broken guarantee.

    Attributes
    ----------
    guarantee
        The guarantee code, for example ``"G2"``.
    message
        A short description of the problem.
    geometry
        Where the problem is, if known.
    """

    guarantee: str
    message: str
    geometry: BaseGeometry | None = None


def _to_rows(polygons: gpd.GeoSeries) -> list[tuple[Hashable, BaseGeometry | None]]:
    """Return the rows as (label, geometry) pairs with known types.

    Parameters
    ----------
    polygons
        The polygons to read.

    Returns
    -------
    list[tuple[Hashable, BaseGeometry | None]]
        One (index label, geometry) pair per row, in order.
    """
    labels = cast(list[Hashable], polygons.index.to_list())
    geometries = cast(list[BaseGeometry | None], polygons.to_list())
    return list(zip(labels, geometries, strict=True))


def check_valid_polygons(polygons: gpd.GeoSeries) -> list[Problem]:
    """Check that every geometry is one valid, non-empty polygon (G7).

    Parameters
    ----------
    polygons
        The polygons to check.

    Returns
    -------
    list[Problem]
        One problem for each empty, non-polygon or invalid geometry.
    """
    problems: list[Problem] = []
    for label, geometry in _to_rows(polygons):
        if geometry is None or geometry.is_empty:
            problems.append(Problem("G7", f"Row {label} is empty."))
        elif geometry.geom_type != "Polygon":
            message = f"Row {label} is a {geometry.geom_type}."
            problems.append(Problem("G7", message, geometry))
        elif not geometry.is_valid:
            problems.append(Problem("G7", f"Row {label} is invalid.", geometry))
    return problems


def check_no_gaps(polygons: gpd.GeoSeries, area: BaseGeometry) -> list[Problem]:
    """Check that the polygons cover the whole area (G1).

    Parameters
    ----------
    polygons
        The polygons to check.
    area
        The area the polygons must cover.

    Returns
    -------
    list[Problem]
        One problem with the gaps, or an empty list.
    """
    gaps = area.difference(polygons.union_all())
    if gaps.is_empty:
        return []
    return [Problem("G1", "Part of the area is not covered.", gaps)]


def check_no_overlaps(polygons: gpd.GeoSeries) -> list[Problem]:
    """Check that no two polygons overlap (G2).

    Polygons that only touch along an edge do not overlap.

    Parameters
    ----------
    polygons
        The polygons to check.

    Returns
    -------
    list[Problem]
        One problem for each overlapping pair, with the shared area.
    """
    rows = _to_rows(polygons)
    query = polygons.sindex.query(polygons, predicate="intersects")
    first, second = cast(list[list[int]], query.tolist())
    problems: list[Problem] = []
    for i, j in zip(first, second, strict=True):
        (label_a, a), (label_b, b) = rows[i], rows[j]
        if i >= j or a is None or b is None:
            continue
        # "T********": the interiors intersect. Touching edges are fine.
        if a.relate_pattern(b, "T********"):
            message = f"Rows {label_a} and {label_b} overlap."
            problems.append(Problem("G2", message, a.intersection(b)))
    return problems


def check_shared_edges(polygons: gpd.GeoSeries) -> list[Problem]:
    """Check that neighbours have the same vertices along shared edges (G4).

    Parameters
    ----------
    polygons
        The polygons to check.

    Returns
    -------
    list[Problem]
        One problem for each polygon with edges that do not match.
    """
    rows = _to_rows(polygons)
    # The Shapely stubs leave `**kwargs` untyped.
    invalid = shapely.coverage_invalid_edges(  # pyright: ignore[reportUnknownMemberType]
        [geometry for _, geometry in rows]
    )
    edges = cast(list[BaseGeometry], invalid.tolist())
    return [
        Problem("G4", f"Row {label} has edges that do not match.", edge)
        for (label, _), edge in zip(rows, edges, strict=True)
        if not edge.is_empty
    ]


def check_inside_area(polygons: gpd.GeoSeries, area: BaseGeometry) -> list[Problem]:
    """Check that no polygon extends outside the area (G5).

    Together with `check_no_gaps`, this means the outlines are the same.

    Parameters
    ----------
    polygons
        The polygons to check.
    area
        The area the polygons must stay inside.

    Returns
    -------
    list[Problem]
        One problem with the parts outside the area, or an empty list.
    """
    outside = polygons.union_all().difference(area)
    if outside.is_empty:
        return []
    return [Problem("G5", "Polygons extend outside the area.", outside)]


def check_min_area(polygons: gpd.GeoSeries, min_area: float) -> list[Problem]:
    """Check that no polygon is smaller than a minimum area (G6).

    Parameters
    ----------
    polygons
        The polygons to check.
    min_area
        The smallest allowed area, in map units squared.

    Returns
    -------
    list[Problem]
        One problem for each polygon that is too small.
    """
    return [
        Problem("G6", f"Row {label} is smaller than {min_area}.", geometry)
        for label, geometry in _to_rows(polygons)
        if geometry is not None and geometry.area < min_area
    ]


def check_all(
    polygons: gpd.GeoSeries, area: BaseGeometry, min_area: float
) -> list[Problem]:
    """Run all checks in this module.

    The other checks need valid polygons, so they run only if G7 passes.

    Parameters
    ----------
    polygons
        The polygons to check.
    area
        The area the polygons must cover exactly.
    min_area
        The smallest allowed area, in map units squared.

    Returns
    -------
    list[Problem]
        All problems found. Empty if every check passes.
    """
    problems = check_valid_polygons(polygons)
    if problems:
        return problems
    return [
        *check_no_gaps(polygons, area),
        *check_no_overlaps(polygons),
        *check_shared_edges(polygons),
        *check_inside_area(polygons, area),
        *check_min_area(polygons, min_area),
    ]
