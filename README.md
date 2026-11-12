# Weight Tool

[简体中文](README.zh-CN.md)

Weight Tool is a Blender 4.2+ extension for viewing and editing vertex-group
weights in Mesh Edit Mode. Operations affect selected, visible vertices only.

## Features

Open the **Weight Tool** tab in the 3D View sidebar while using Vertex Select
mode.

- View every non-zero vertex group used by the selection.
- See the weight for one vertex or the average weight for multiple vertices.
- Set a weight on all selected vertices, remove them from a group, or add them to
  a new group.
- Blend two groups with Replace, Add, Subtract, Multiply, Maximum, Minimum, or
  Average modes.
- Mirror one or more groups between selected left/right vertex pairs. Matching
  `.L` and `.R` group names are supported.
- Smooth one group's weights over connected mesh vertices. Strength, iterations,
  unselected-neighbor contribution, and distance weighting are configurable.
- Normalize each selected vertex so its group weights add up to one. Vertices
  without usable weights are skipped and reported.

The group list is scrollable and searchable. All editing operations support
Blender Undo.

## Build

From the repository root, using Blender 4.2 or newer:

```powershell
blender --command extension build `
  --source-dir addon\weight_tool `
  --output-dir .

blender --command extension validate weight_tool-2.1.0.zip
```

Run the integration tests:

```powershell
blender --background --factory-startup --python tests\test_addon.py
```
