# Topoland specification

**Status:** Draft.

This document sets the direction for Topoland: its purpose, principles, guarantees and scope. It does not describe the implementation. Parameter names and default values are decided during implementation and added here later.

Topoland is built from the geometry operations defined in [operations.md](operations.md). That document also defines general geometry words, such as coverage and map units.

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

| Word         | Meaning                                                                                                                                                                                       |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Study area   | The outer extent of the area to model, given as polygons.                                                                                                                                     |
| Layer        | One input layer of polygons for one class, for example `buildings`.                                                                                                                           |
| Class        | The landcover type of a polygon. It is the name of the layer it comes from.                                                                                                                   |
| Priority     | The order of the layers. Where layers overlap, the earlier layer wins.                                                                                                                        |
| Unclassified | The class of areas in the study area that no layer covers.                                                                                                                                    |
| Thin part    | A polygon, a part of a polygon or a gap that is narrower than the minimum width. Includes slivers (thin polygons or gaps where the edges of two layers almost match), tails and narrow necks. |

## 4. Inputs

| Input      | Description                                                                            |
| ---------- | -------------------------------------------------------------------------------------- |
| Study area | Polygons. Together they form the outer extent of the study area.                       |
| Layers     | An ordered list of `(class name, polygons)`. The first layer has the highest priority. |
| Settings   | See [section 8](#8-settings).                                                          |

Topoland cleans the study area once, at the start: it [repairs](operations.md#repair) it, [dissolves](operations.md#dissolve) its polygons into one, [fills its holes](operations.md#fill-holes) and [simplifies](operations.md#simplify) its outline. After that, the study area does not move. The layers are fitted to it.

Holes in the study area are not part of the extent. They are filled. If an area inside the study area needs its own class, for example a lake, it must be given as a layer. Otherwise it becomes `unclassified`.

Users can give the inputs in two ways:

- **As files.** HydroForge reads them, for example layers from a GeoPackage.
- **As data in memory,** for example GeoDataFrames. This is useful when Topoland is one step in a larger Python workflow.

The processing works the same way for both. Reading files is a separate step from processing.

## 5. Outputs

| Output     | Description                                                                                     |
| ---------- | ----------------------------------------------------------------------------------------------- |
| Study area | The cleaned outer extent. It has no holes. Its outline is exactly the outline of the landcover. |
| Landcover  | One row per polygon, with one column, `class`.                                                  |

Both outputs use the CRS of the inputs.

Users can get the outputs as data in memory, or HydroForge writes them to files, for example a GeoPackage.

## 6. Guarantees

These rules are always true for the output. Each rule has its own tests.

Rules are grouped in categories, and each category has its own hundred:

- `x00` names the category. It is never a rule.
- A new rule takes the next free number in its category. A new category takes the next free hundred.
- An ID is never reused or renumbered. A removed rule keeps its number and is marked as removed.

The input errors in [section 7](#7-input-validation) follow the same system.

**G100 Topology**

| ID   | Rule                                                                                                                                          |
| ---- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| G101 | **No gaps.** The landcover covers the whole study area. There are no gaps.                                                                    |
| G102 | **No overlaps.** No two landcover polygons overlap.                                                                                           |
| G103 | **Shared edges.** Neighbouring polygons have the same vertices along their common edge.                                                       |
| G104 | **Same outline.** The outline of the landcover is exactly the outline of the cleaned study area. The study area does not move after cleaning. |
| G105 | **Valid geometry.** Every row is one valid, non-empty polygon. There are no multipolygons, lines or points.                                   |

**G200 Classes**

| ID   | Rule                                                                                 |
| ---- | ------------------------------------------------------------------------------------ |
| G201 | **Priority.** Where layers overlap, the polygon gets the class of the earlier layer. |
| G202 | **Known classes.** Every `class` value is a layer name or `unclassified`.            |

**G300 Cleaning**

| ID   | Rule                                                                                                                                                                                                                                                                                                                                           |
| ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| G301 | **Snapping.** Where an edge of a layer is closer than the snap distance to an edge of a higher layer, or to the study area outline, it is moved onto that edge. Vertices are added where needed, so both edges match along their whole common length. A layer only moves towards higher layers and the study area, never towards lower layers. |
| G302 | **No thin parts or slivers.** No polygon, or part of a polygon, is narrower than the minimum width. Inside a layer, gaps and notches narrower than the minimum width are closed.                                                                                                                                                               |
| G303 | **No small polygons.** No polygon is smaller than the minimum area set by the user. A small polygon joins the neighbour with the longest shared edge.                                                                                                                                                                                          |
| G304 | **No extra vertices.** No vertex lies on a straight line between its two neighbours, unless three or more polygons meet there, or a polygon edge meets the outline there. Edges are simplified as far as the simplify tolerance allows.                                                                                                        |
| G305 | **Small changes only.** A point only changes class, compared with the input layers by priority, if it is close to an input edge: within the largest distance setting. Small polygons (G303) and thin parts (G302) are the only exceptions.                                                                                                     |

**G400 Behaviour**

| ID   | Rule                                                                      |
| ---- | ------------------------------------------------------------------------- |
| G401 | **Repeatable.** The same inputs and settings always give the same output. |

## 7. Input validation

Input is invalid, and Topoland stops with a clear message, if:

**E100 Inputs**

| ID   | Case                                                        |
| ---- | ----------------------------------------------------------- |
| E101 | There are no layers.                                        |
| E102 | The study area is empty.                                    |
| E103 | An input contains lines or points.                          |
| E104 | A class name is empty, is used twice, or is `unclassified`. |

**E200 Coordinate reference system**

| ID   | Case                                                              |
| ---- | ----------------------------------------------------------------- |
| E201 | An input has no CRS, or a geographic CRS (for example EPSG:4326). |
| E202 | The inputs do not all have the same CRS.                          |

**E300 Settings**

| ID   | Case                                       |
| ---- | ------------------------------------------ |
| E301 | A setting has a value that is not allowed. |

Invalid polygons are not an error. Topoland repairs them.

## 8. Settings

The user must be able to control how Topoland cleans the data. At least:

| Setting            | Meaning                                                    | Operation                                                                                    | Rules |
| ------------------ | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ----- |
| Snap distance      | How far snapping may move a vertex.                        | [Snap](operations.md#snap)                                                                   | G301  |
| Minimum width      | Thin parts narrower than this are removed.                 | [Close gaps](operations.md#close-gaps), [Remove thin parts](operations.md#remove-thin-parts) | G302  |
| Simplify tolerance | How far simplifying may move an edge.                      | [Simplify](operations.md#simplify)                                                           | G304  |
| Minimum area       | The smallest area of an output polygon.                    | [Merge small polygons](operations.md#merge-small-polygons)                                   | G303  |
| Fill holes         | Fill the holes in the polygons of a layer. Off by default. | [Fill holes](operations.md#fill-holes)                                                       |       |

The user should be able to use different settings for different layers.

Names, units, default values and any other settings are decided during implementation. They are added to this section when they are stable.

## 9. Out of scope

Topoland does not:

- Reproject data.
- Work with raster data.
- Keep the attributes of the input layers.
- Write files in the format of a specific model.
- Split large polygons into parts with a maximum number of vertices.

## 10. Open questions

1. Are the snap distance and the minimum width one setting or two? The snap distance is usually larger than the minimum width.
1. Which settings can differ per layer? The study area needs its own simplify tolerance.
1. How do we test G301 and G304 on any output, not only on prepared cases?
