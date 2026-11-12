# Weight Tool

A Blender 4.2+ extension for inspecting and editing the vertex-group weights of
selected vertices without leaving Edit Mode.

## Install

Install `weight_tool-2.1.0.zip` through **Edit > Preferences > Get
Extensions > Install from Disk**.

## Languages

The extension includes English (`en_US`) and Simplified Chinese (`zh_HANS`). It
follows Blender's language and interface-translation settings automatically.

## Use

Open a mesh in Edit Mode, enable Vertex Select, select one or more vertices, and
open **Weight Tool > Weight Tool** in the 3D View N sidebar.

The panel lists the union of all vertex groups with a non-zero weight on at least
one selected vertex. For multiple vertices, the average uses all selected
vertices as its denominator, so vertices absent from a group contribute zero.
The member count beside the average shows how many selected vertices currently
belong to that group. The group list uses a fixed eight-row viewport with a
scrollbar, so objects with many groups do not make the N sidebar excessively
tall. Blender's list filter can be used to search by group name.

- **Overwrite** assigns one entered weight to every selected vertex. Entering
  zero removes the selected vertices from the group.
- The **X** button removes all selected vertices from that row's group without
  deleting the group itself.
- **Add Selected to New Vertex Group** creates a uniquely named group and assigns
  the entered weight to every selected vertex.
- **Blend Selected Vertex Weights** combines group A and group B independently on
  every selected vertex, then writes the result to group A. Available modes are
  Replace (`A=B`), Add (`A+B`), Subtract (`A-B`), Multiply, Maximum, Minimum,
  and Average. Missing membership contributes zero, results are clamped to
  `0..1`, and a zero result removes that vertex from group A.
- **Mirror Selected Vertex Weights** supports selecting multiple groups from a
  scrollable checklist. Groups used by the selected vertices are checked by
  default. It finds unique mirrored pairs across the object's local `X=0` plane
  and processes only channels where both vertices share one selected group, or
  where the left vertex belongs to selected `XXX.L` and the right vertex belongs
  to selected `XXX.R`. Replace and Subtract use the chosen direction; the other
  modes write one shared result to both sides. Center-line, unpaired, ambiguous,
  hidden, and unselected vertices are unchanged. Mirror tolerance is measured in
  local object-space units.
- **Smooth Selected Vertex Weights** applies synchronous topology-based
  Laplacian smoothing to one group. Smooth factor and iteration count are
  adjustable. Unselected topological neighbors contribute by default but are
  never modified; disable the option to average selected neighbors only. Enable
  inverse-distance weighting to weight neighbor contributions by `1 / edge
  length` in object-local space instead of treating every neighbor equally.
- **Normalize Selected Vertex Weights** scales every selected vertex's non-zero
  weights across all valid groups so their sum is one. Vertices with no group
  membership or a zero weight sum are left unchanged and reported as skipped.
