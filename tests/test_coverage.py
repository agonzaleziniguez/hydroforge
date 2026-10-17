from typing import cast

import geopandas as gpd
from shapely import MultiPolygon, Polygon, box
from shapely.geometry.base import BaseGeometry

from hydroforge.coverage import (
    Problem,
    check_all,
    check_inside_area,
    check_min_area,
    check_no_gaps,
    check_no_overlaps,
    check_shared_edges,
    check_valid_polygons,
)

AREA = box(0, 0, 2, 1)
LEFT = box(0, 0, 1, 1)
RIGHT = box(1, 0, 2, 1)


def make_series(*geometries: BaseGeometry | None) -> gpd.GeoSeries:
    # The geopandas stubs reject None, but GeoSeries accepts it.
    return gpd.GeoSeries(cast(list[BaseGeometry], list(geometries)))


def list_guarantees(problems: list[Problem]) -> list[str]:
    return [problem.guarantee for problem in problems]


def test_valid_coverage_has_no_problems() -> None:
    assert check_all(make_series(LEFT, RIGHT), AREA, min_area=0.5) == []


def test_valid_polygons() -> None:
    bowtie = Polygon([(0, 0), (1, 1), (1, 0), (0, 1)])
    multi = MultiPolygon([LEFT, box(3, 0, 4, 1)])
    problems = check_valid_polygons(make_series(LEFT, None, Polygon(), bowtie, multi))
    assert [problem.message for problem in problems] == [
        "Row 1 is empty.",
        "Row 2 is empty.",
        "Row 3 is invalid.",
        "Row 4 is a MultiPolygon.",
    ]


def test_no_gaps() -> None:
    problems = check_no_gaps(make_series(LEFT), AREA)
    assert list_guarantees(problems) == ["G1"]
    assert problems[0].geometry is not None
    assert problems[0].geometry.equals(RIGHT)


def test_no_overlaps() -> None:
    assert check_no_overlaps(make_series(LEFT, RIGHT)) == []

    problems = check_no_overlaps(make_series(LEFT, box(0.5, 0, 2, 1)))
    assert list_guarantees(problems) == ["G2"]
    assert problems[0].geometry is not None
    assert problems[0].geometry.equals(box(0.5, 0, 1, 1))


def test_no_overlaps_finds_polygon_inside_another() -> None:
    problems = check_no_overlaps(make_series(AREA, box(0.2, 0.2, 0.8, 0.8)))
    assert list_guarantees(problems) == ["G2"]


def test_shared_edges() -> None:
    assert check_shared_edges(make_series(LEFT, RIGHT)) == []

    # RIGHT with an extra vertex at (1, 0.5) that LEFT does not have.
    right = Polygon([(1, 0), (2, 0), (2, 1), (1, 1), (1, 0.5)])
    assert list_guarantees(check_shared_edges(make_series(LEFT, right))) == ["G4", "G4"]


def test_inside_area() -> None:
    assert check_inside_area(make_series(LEFT, RIGHT), AREA) == []

    problems = check_inside_area(make_series(LEFT, box(1, 0, 3, 1)), AREA)
    assert list_guarantees(problems) == ["G5"]
    assert problems[0].geometry is not None
    assert problems[0].geometry.equals(box(2, 0, 3, 1))


def test_min_area() -> None:
    small = box(1, 0, 1.1, 1)
    problems = check_min_area(make_series(LEFT, small), min_area=0.5)
    assert list_guarantees(problems) == ["G6"]
    assert problems[0].geometry == small


def test_check_all_stops_after_invalid_polygons() -> None:
    assert list_guarantees(check_all(make_series(LEFT, None), AREA, min_area=0.5)) == [
        "G7"
    ]
