# Topoland specification

**Status:** Draft.

This document sets the direction for Topoland: its purpose, principles, guarantees and scope. It does not describe the implementation. Parameter names and default values are decided during implementation and added here later.

## 1. Purpose

Topoland builds one landcover map for a study area from several landcover layers.

The map is ready for hydrological and hydraulic models:

- It covers the whole study area.
- Polygons do not overlap.
- Neighbouring polygons share exactly the same edges.

Input data is often not clean. Layers overlap, edges almost match, and geometries can be invalid. Topoland cleans and repairs the data and produces a topologically correct result.

## 2. Principles

1. **Correct topology first.** The guarantees in [section 6](#6-guarantees) are always met. If they cannot be met, Topoland stops with an error. It never returns a wrong result silently.
1. **Repair, do not reject.** Topoland repairs geometry problems in the input, such as invalid polygons or edges that almost match.
1. **Validate inputs.** Topoland validates the inputs. Invalid input stops the run early, with a clear message.
1. **Nothing hidden.** Every tolerance that changes the geometry can be seen and set by the user. There are no fixed, hidden values.
1. **Few, clear settings.** Each setting describes the result the user wants, for example a minimum polygon area. It does not describe an internal step.
1. **Repeatable.** The same inputs and settings always give the same output.
1. **Easy to install.** Every dependency installs as a Python package, for example from PyPI. Topoland does not need GIS software that users install separately.

## 3. Words

| Word         | Meaning                                                                     |
| ------------ | --------------------------------------------------------------------------- |
| Study area   | The outer extent of the area to model, given as polygons.                   |
| Layer        | One input layer of polygons for one class, for example `buildings`.         |
| Class        | The landcover type of a polygon. It is the name of the layer it comes from. |
| Priority     | The order of the layers. Where layers overlap, the earlier layer wins.      |
| Unclassified | The class of areas in the study area that no layer covers.                  |
| Map units    | The units of the coordinate reference system (CRS), usually metres.         |

## 4. Inputs

| Input      | Description                                                                            |
| ---------- | -------------------------------------------------------------------------------------- |
| Study area | Polygons. Together they form the outer extent of the study area.                       |
| Layers     | An ordered list of `(class name, polygons)`. The first layer has the highest priority. |
| Settings   | See [section 8](#8-settings).                                                          |

Holes in the study area are not part of the extent. They are filled. If an area inside the study area needs its own class, for example a lake, it must be given as a layer. Otherwise it becomes `unclassified`.

Users can give the inputs in two ways:

- **As files.** HydroForge reads them, for example layers from a GeoPackage.
- **As data in memory,** for example GeoDataFrames. This is useful when Topoland is one step in a larger Python workflow.

The processing works the same way for both. Reading files is a separate step from processing.

## 5. Outputs

| Output     | Description                                                                                         |
| ---------- | --------------------------------------------------------------------------------------------------- |
| Study area | The cleaned outer extent. It has no holes. Its outline is the same as the outline of the landcover. |
| Landcover  | One row per polygon, with one column, `class`.                                                      |

Both outputs use the CRS of the inputs.

Users can get the outputs as data in memory, or HydroForge writes them to files, for example a GeoPackage.

## 6. Guarantees

These rules are always true for the output. Each rule has its own tests.

| ID  | Rule                                                                                                                                                  |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| G1  | **Full coverage.** The landcover covers the whole study area. There are no gaps.                                                                      |
| G2  | **No overlaps.** No two landcover polygons overlap.                                                                                                   |
| G3  | **Priority.** Where layers overlap, the polygon gets the class of the earlier layer.                                                                  |
| G4  | **Shared edges.** Neighbouring polygons have the same vertices along their common edge.                                                               |
| G5  | **Same outline.** The outline of the landcover is the same as the outline of the output study area.                                                   |
| G6  | **No small polygons.** No polygon is smaller than the minimum area set by the user. A small polygon joins the neighbour with the longest shared edge. |
| G7  | **Valid geometry.** Every row is one valid, non-empty polygon. There are no multipolygons, lines or points.                                           |
| G8  | **Known classes.** Every `class` value is a layer name or `unclassified`.                                                                             |
| G9  | **Repeatable.** The same inputs and settings always give the same output.                                                                             |

## 7. Input validation

Input is invalid, and Topoland stops with a clear message, if:

| ID  | Case                                                              |
| --- | ----------------------------------------------------------------- |
| E1  | There are no layers.                                              |
| E2  | The study area is empty.                                          |
| E3  | An input has no CRS, or a geographic CRS (for example EPSG:4326). |
| E4  | The inputs do not all have the same CRS.                          |
| E5  | An input contains lines or points.                                |
| E6  | A class name is empty, is used twice, or is `unclassified`.       |
| E7  | A setting has a value that is not allowed.                        |

Invalid polygons are not an error. Topoland repairs them.

## 8. Settings

The user must be able to control how Topoland cleans the data. At least:

- The distance below which edges and vertices are treated as the same.
- The minimum area of an output polygon.

The user should be able to use different settings for different layers.

Names, units, default values and any other settings are decided during implementation. They are added to this section when they are stable.

## 9. Out of scope

Topoland does not:

- Reproject data.
- Work with raster data.
- Keep the attributes of the input layers.
- Write files in the format of a specific model.
