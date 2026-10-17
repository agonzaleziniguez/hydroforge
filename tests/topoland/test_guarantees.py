import geopandas as gpd
from shapely import box

from hydroforge.topoland.guarantees import check_known_classes, check_landcover

AREA = box(0, 0, 2, 1)


def make_landcover(*classes: str) -> gpd.GeoDataFrame:
    geometries = [box(i, 0, i + 1, 1) for i in range(len(classes))]
    return gpd.GeoDataFrame({"class": list(classes)}, geometry=geometries)


def test_known_classes() -> None:
    assert check_known_classes(make_landcover("roads", "unclassified"), ["roads"]) == []

    problems = check_known_classes(make_landcover("roads", "lakes"), ["roads"])
    assert [problem.message for problem in problems] == ["Unknown class 'lakes'."]


def test_landcover_runs_all_checks() -> None:
    good = make_landcover("roads", "grass")
    assert check_landcover(good, AREA, ["roads", "grass"], min_area=0.5) == []

    problems = check_landcover(
        make_landcover("roads", "lakes"), AREA, ["roads"], min_area=2
    )
    assert [problem.guarantee for problem in problems] == ["G6", "G6", "G8"]
