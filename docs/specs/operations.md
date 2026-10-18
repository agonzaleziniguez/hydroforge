# Geometry operations

**Status:** Draft.

This document defines the geometry operations that HydroForge workflows are built from. Each operation says what it does and what it promises. It names the method only where the promises depend on it, for example buffers. It does not name library calls or code.

Workflows, for example [Topoland](topoland.md), decide which operations to use, in which order, and with which settings. Their guarantees are defined in their own documents.

## 1. Words

| Word      | Meaning                                                                   |
| --------- | ------------------------------------------------------------------------- |
| Map units | The units of the coordinate reference system (CRS), usually metres.       |
| Coverage  | Polygons that do not overlap and share exact edges with their neighbours. |
| Outline   | The outer boundary of a set of polygons, for example of a coverage.       |
| Reference | Geometry that an operation fits other geometry to. It never moves.        |
| Class     | A value that groups polygons, for example a landcover type.               |

All distances are in map units, and all areas in square map units.

## 2. Rules for all operations

1. **One job.** Each operation does one thing.
1. **Valid output.** The output is valid. Operations that may create lines or points keep only the polygons.
1. **Empty is allowed.** An operation can return an empty result, for example when every polygon is too small. This is not an error.
1. **Only given distances.** An operation moves geometry only by the distances given as its arguments. There are no hidden tolerances.
1. **Repeatable.** The same input always gives the same output.
1. **Tested.** Each operation has its own tests with small data files that contain the problem it solves.

## 3. Operations

### Repair

Makes every geometry valid.

- Crossing edges and self-touching rings are split into valid polygons.
- Lines and points left by the repair are removed, for example the line left by a spike.
- Area that was inside a valid polygon stays inside.

### Remove duplicate points

Removes vertices that repeat the previous vertex. The shape does not change.

### Fill holes

Removes the inner rings of polygons. The outer ring does not change.

### Close gaps

Closes gaps and notches narrower than a width. It buffers the polygons out by half the width, then in by the same distance (also called closing).

- Polygons closer than the width are joined.
- Buffers use square corners, so straight corners stay straight and no rounded corners are added.
- Edges that are not near a gap do not move.
- Argument: width.

### Remove thin parts

Removes parts narrower than a width, such as tails, strips and narrow necks. It buffers the polygons in by half the width, then out by the same distance (also called opening).

- Buffers use square corners, so straight corners stay straight and no rounded corners are added.
- Parts that are wider than the width do not move.
- Argument: width.

### Snap

Moves the edges of polygons onto the edges of a reference, where they are closer than a distance.

- Each vertex closer than the distance moves to the closest point of the reference edges. This can be a reference vertex or the middle of an edge.
- Vertices are added where a reference vertex lies near an edge, so both edges match along their whole common length.
- No point moves more than the distance.
- Argument: distance.

The reference can be other polygons or an outline. Snapping polygons to themselves is not defined yet.

### Cut

Removes from polygons the area covered by a reference.

### Add shared vertices

Adds to each polygon the vertices of its neighbours that lie on its edges, so that neighbours have the same vertices along their common edges. No vertex moves.

This is needed after snap and cut: the snapped polygons get new vertices that the reference does not have yet.

### Simplify

Removes vertices from the edges of a coverage, so that no edge moves more than a tolerance.

- Each edge between two polygons is simplified once, so both neighbours stay matched.
- Points where three or more polygons meet do not move.
- The outline can be kept fixed, or simplified with the other edges.
- The result is still a coverage. Each polygon keeps its class.
- Argument: tolerance.

### Remove extra vertices

Removes vertices that lie on a straight line between their two neighbours.

- Vertices where three or more polygons meet, or where an edge meets the outline, are kept.
- No vertex moves.

### Dissolve

Joins touching polygons of the same class into one geometry. Edges inside it are removed. Use remove extra vertices afterwards to remove the vertices left where the old edges ended.

### Merge small polygons

Joins each polygon smaller than an area to the neighbour with the longest shared edge.

- The neighbour keeps its class.
- A small polygon with no neighbour is removed.
- Argument: area.

### Fill gaps

Fills the parts of an extent that no polygon covers with new polygons of a given class.

## 4. Not used

### Segmentize

Segmentize (also called densify) adds vertices along edges at a fixed interval. It is sometimes used before snapping, so that there are more vertices to snap to. HydroForge does not use it, because:

- It adds many vertices that simplify must remove later.
- Snapping to the added vertices moves true corners, by up to about half the interval.
- It is not needed: snap moves vertices onto the middle of reference edges and adds vertices where needed.
