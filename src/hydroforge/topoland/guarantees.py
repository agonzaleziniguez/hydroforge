"""Checks for the Topoland guarantees in `docs/specs/topoland.md`.

G3 (priority) and G9 (repeatable) are checked in the tests, because they
need the inputs or a second run.
"""

from collections.abc import Iterable
from typing import cast

import geopandas as gpd
from shapely.geometry.base import BaseGeometry

from hydroforge import coverage
from hydroforge.coverage import Problem

UNCLASSIFIED = "unclassified"
CLASS_COLUMN = "class"


def check_known_classes(
    landcover: gpd.GeoDataFrame, class_names: Iterable[str]
) -> list[Problem]:
    """Check that every class is a layer name or ``unclassified`` (G8).

    Parameters
    ----------
    landcover
        The Topoland result, with a ``class`` column.
    class_names
        The names of the input layers.

    Returns
    -------
    list[Problem]
        One problem for each unknown class, sorted by name.
    """
    known = {*class_names, UNCLASSIFIED}
    classes = cast(list[str], landcover[CLASS_COLUMN].to_list())
    unknown = sorted(set(classes) - known)
    return [Problem("G8", f"Unknown class {name!r}.") for name in unknown]


def check_landcover(
    landcover: gpd.GeoDataFrame,
    study_area: BaseGeometry,
    class_names: Iterable[str],
    min_area: float,
) -> list[Problem]:
    """Run all checks on a Topoland result.

    Parameters
    ----------
    landcover
        The Topoland result, with a ``class`` column.
    study_area
        The area the result must cover exactly.
    class_names
        The names of the input layers.
    min_area
        The smallest allowed area, in map units squared.

    Returns
    -------
    list[Problem]
        All problems found. Empty if the result keeps every guarantee.
    """
    return [
        *coverage.check_all(landcover.geometry, study_area, min_area),
        *check_known_classes(landcover, class_names),
    ]
