"""Weight editing operators."""

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    StringProperty,
)

from .translations import iface_, iface_format
from .weights import (
    blend_selected_weights,
    create_group_and_assign,
    mirror_selected_weights,
    normalize_selected_weights,
    set_selected_weight,
    smooth_selected_weights,
)
from .weights import group_summaries


BLEND_MODE_ITEMS = (
    ("REPLACE", "Replace", "Copy the source weight to the output"),
    ("ADD", "Add", "Add the two weights"),
    ("SUBTRACT", "Subtract", "Subtract in the selected direction"),
    ("MULTIPLY", "Multiply", "Multiply the two weights"),
    ("MAXIMUM", "Maximum", "Use the larger weight"),
    ("MINIMUM", "Minimum", "Use the smaller weight"),
    ("AVERAGE", "Average", "Use the arithmetic mean"),
)


class _SelectedWeightOperator:
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH" or obj.mode != "EDIT":
            cls.poll_message_set("An active mesh in Edit Mode is required")
            return False
        if tuple(context.tool_settings.mesh_select_mode) != (True, False, False):
            cls.poll_message_set("Vertex Select mode is required")
            return False
        return True


class WEIGHTTOOL_PG_mirror_group_item(bpy.types.PropertyGroup):
    name: StringProperty()
    selected: BoolProperty(name="Use", default=False)


class WEIGHTTOOL_UL_mirror_group_selection(bpy.types.UIList):
    def draw_item(
        self,
        _context,
        layout,
        _data,
        item,
        _icon,
        _active_data,
        _active_propname,
        _index,
    ):
        row = layout.row(align=True)
        row.prop(item, "selected", text="")
        row.label(text=item.name, icon="GROUP_VERTEX")

    def filter_items(self, _context, data, propname):
        items = getattr(data, propname)
        if not self.filter_name:
            return [], []
        flags = bpy.types.UI_UL_list.filter_items_by_name(
            self.filter_name,
            self.bitflag_filter_item,
            items,
            "name",
            reverse=self.use_filter_invert,
        )
        return flags, []


class WEIGHTTOOL_OT_set_selected_group_weight(
    _SelectedWeightOperator,
    bpy.types.Operator,
):
    bl_idname = "weight_tool.set_selected_group_weight"
    bl_label = "Overwrite Selected Vertex Weights"
    bl_description = "Set this group to one weight on every selected vertex"
    bl_options = {"REGISTER", "UNDO"}

    group_index: IntProperty(options={"HIDDEN"})
    group_name: StringProperty(options={"HIDDEN"})
    weight: FloatProperty(
        name="Weight",
        description="New weight for every selected vertex; zero removes membership",
        min=0.0,
        max=1.0,
        precision=4,
        default=1.0,
    )

    def invoke(self, context, _event):
        group = next(
            (
                group
                for group in context.active_object.vertex_groups
                if group.index == self.group_index
            ),
            None,
        )
        if group is None:
            self.report({"ERROR"}, iface_("The specified vertex group no longer exists."))
            return {"CANCELLED"}
        self.group_name = group.name
        return context.window_manager.invoke_props_dialog(self, width=320)

    def draw(self, _context):
        self.layout.label(text=self.group_name, icon="GROUP_VERTEX")
        self.layout.prop(self, "weight")

    def execute(self, context):
        try:
            count, name = set_selected_weight(
                context,
                self.group_index,
                self.weight,
            )
        except (RuntimeError, ValueError) as error:
            self.report({"ERROR"}, iface_(str(error)))
            return {"CANCELLED"}
        self.report(
            {"INFO"},
            iface_format(
                'Set {count} vertices in "{name}" to {weight:.4f}.',
                count=count,
                name=name,
                weight=self.weight,
            ),
        )
        return {"FINISHED"}


class WEIGHTTOOL_OT_remove_selected_from_group(
    _SelectedWeightOperator,
    bpy.types.Operator,
):
    bl_idname = "weight_tool.remove_selected_from_group"
    bl_label = "Remove Selected Vertices from Group"
    bl_description = "Remove every selected vertex from this vertex group"
    bl_options = {"REGISTER", "UNDO"}

    group_index: IntProperty(options={"HIDDEN"})

    def execute(self, context):
        try:
            count, name = set_selected_weight(context, self.group_index, 0.0)
        except (RuntimeError, ValueError) as error:
            self.report({"ERROR"}, iface_(str(error)))
            return {"CANCELLED"}
        self.report(
            {"INFO"},
            iface_format(
                'Removed {count} selected vertices from "{name}".',
                count=count,
                name=name,
            ),
        )
        return {"FINISHED"}


class WEIGHTTOOL_OT_add_selected_to_new_group(
    _SelectedWeightOperator,
    bpy.types.Operator,
):
    bl_idname = "weight_tool.add_selected_to_new_group"
    bl_label = "Add Selected to New Vertex Group"
    bl_description = "Create a new vertex group and assign all selected vertices"
    bl_options = {"REGISTER", "UNDO"}

    group_name: StringProperty(
        name="Group Name",
        description="Name of the new vertex group",
        default="Group",
    )
    weight: FloatProperty(
        name="Weight",
        description="Weight assigned to every selected vertex",
        min=0.0001,
        max=1.0,
        precision=4,
        default=1.0,
    )

    def invoke(self, context, _event):
        base_name = "Group"
        name = base_name
        suffix = 1
        while context.active_object.vertex_groups.get(name) is not None:
            name = f"{base_name}.{suffix:03d}"
            suffix += 1
        self.group_name = name
        return context.window_manager.invoke_props_dialog(self, width=360)

    def execute(self, context):
        try:
            count, name = create_group_and_assign(
                context,
                self.group_name,
                self.weight,
            )
        except (RuntimeError, ValueError) as error:
            self.report({"ERROR"}, iface_(str(error)))
            return {"CANCELLED"}
        self.report(
            {"INFO"},
            iface_format(
                'Added {count} selected vertices to new group "{name}" at {weight:.4f}.',
                count=count,
                name=name,
                weight=self.weight,
            ),
        )
        return {"FINISHED"}


class WEIGHTTOOL_OT_blend_selected_group_weights(
    _SelectedWeightOperator,
    bpy.types.Operator,
):
    bl_idname = "weight_tool.blend_selected_group_weights"
    bl_label = "Blend Selected Vertex Weights"
    bl_description = (
        "Blend group A with group B per selected vertex and write the result to A"
    )
    bl_options = {"REGISTER", "UNDO"}

    group_a: StringProperty(name="Group A")
    group_b: StringProperty(name="Group B")
    mode: EnumProperty(
        name="Blend Mode",
        items=BLEND_MODE_ITEMS,
        default="REPLACE",
    )

    def invoke(self, context, _event):
        groups = list(context.active_object.vertex_groups)
        if len(groups) < 2:
            self.report({"ERROR"}, iface_("At least two vertex groups are required."))
            return {"CANCELLED"}

        active_index = context.active_object.vertex_groups.active_index
        active = next(
            (group for group in groups if group.index == active_index),
            groups[0],
        )
        if context.active_object.vertex_groups.get(self.group_a) is None:
            self.group_a = active.name
        if (
            context.active_object.vertex_groups.get(self.group_b) is None
            or self.group_b == self.group_a
        ):
            self.group_b = next(
                group.name for group in groups if group.name != self.group_a
            )
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.prop_search(
            self,
            "group_a",
            context.active_object,
            "vertex_groups",
            text="Group A (Output)",
        )
        layout.prop_search(
            self,
            "group_b",
            context.active_object,
            "vertex_groups",
            text="Group B",
        )
        layout.prop(self, "mode")
        layout.label(text="Result is clamped to 0-1 and written to Group A")

    def execute(self, context):
        try:
            count, group_a, group_b = blend_selected_weights(
                context,
                self.group_a,
                self.group_b,
                self.mode,
            )
        except (RuntimeError, ValueError) as error:
            self.report({"ERROR"}, iface_(str(error)))
            return {"CANCELLED"}
        mode_label = self.mode.replace("_", " ").title()
        self.report(
            {"INFO"},
            iface_format(
                'Blended "{group_a}" with "{group_b}" using {mode} on {count} vertices.',
                group_a=group_a,
                group_b=group_b,
                mode=iface_(mode_label),
                count=count,
            ),
        )
        return {"FINISHED"}


class WEIGHTTOOL_OT_mirror_selected_group_weights(
    _SelectedWeightOperator,
    bpy.types.Operator,
):
    bl_idname = "weight_tool.mirror_selected_group_weights"
    bl_label = "Mirror Selected Vertex Weights"
    bl_description = (
        "Blend weights between selected vertex pairs mirrored across local X=0"
    )
    bl_options = {"REGISTER", "UNDO"}

    groups: CollectionProperty(type=WEIGHTTOOL_PG_mirror_group_item)
    active_group_index: IntProperty(default=0)
    mode: EnumProperty(
        name="Blend Mode",
        items=BLEND_MODE_ITEMS,
        default="REPLACE",
    )
    direction: EnumProperty(
        name="Direction",
        items=(
            (
                "LEFT_TO_RIGHT",
                "Left to Right",
                "Copy left to right, or write left minus right to the right",
            ),
            (
                "RIGHT_TO_LEFT",
                "Right to Left",
                "Copy right to left, or write right minus left to the left",
            ),
        ),
        default="LEFT_TO_RIGHT",
    )
    tolerance: FloatProperty(
        name="Mirror Tolerance",
        description="Maximum local-space distance from an exact X-axis mirror",
        min=0.0000001,
        soft_max=0.01,
        precision=6,
        default=0.0001,
        subtype="DISTANCE",
    )

    def invoke(self, context, _event):
        object_groups = list(context.active_object.vertex_groups)
        if not object_groups:
            self.report({"ERROR"}, iface_("At least one vertex group is required."))
            return {"CANCELLED"}

        try:
            _count, summaries = group_summaries(context)
            default_indices = {summary.index for summary in summaries}
        except (RuntimeError, ValueError):
            default_indices = set()
        self.groups.clear()
        for group in object_groups:
            item = self.groups.add()
            item.name = group.name
            item.selected = group.index in default_indices
        return context.window_manager.invoke_props_dialog(self, width=420)

    def draw(self, context):
        layout = self.layout
        layout.template_list(
            "WEIGHTTOOL_UL_mirror_group_selection",
            "mirror_groups",
            self,
            "groups",
            self,
            "active_group_index",
            rows=8,
            maxrows=8,
        )
        layout.prop(self, "mode")
        if self.mode in {"REPLACE", "SUBTRACT"}:
            layout.prop(self, "direction", expand=True)
        layout.prop(self, "tolerance")

    def execute(self, context):
        try:
            group_names = tuple(
                item.name for item in self.groups if item.selected
            )
            pair_count, channel_count = mirror_selected_weights(
                context,
                group_names,
                self.mode,
                self.direction,
                self.tolerance,
            )
        except (RuntimeError, ValueError) as error:
            self.report({"ERROR"}, iface_(str(error)))
            return {"CANCELLED"}
        mode_label = self.mode.replace("_", " ").title()
        self.report(
            {"INFO"},
            iface_format(
                "Mirrored {channels} weight channels across {pairs} vertex pairs using {mode}.",
                channels=channel_count,
                pairs=pair_count,
                mode=iface_(mode_label),
            ),
        )
        return {"FINISHED"}


class WEIGHTTOOL_OT_smooth_selected_group_weights(
    _SelectedWeightOperator,
    bpy.types.Operator,
):
    bl_idname = "weight_tool.smooth_selected_group_weights"
    bl_label = "Smooth Selected Vertex Weights"
    bl_description = (
        "Laplacian-smooth one vertex group over the selected mesh vertices"
    )
    bl_options = {"REGISTER", "UNDO"}

    group_name: StringProperty(name="Vertex Group")
    factor: FloatProperty(
        name="Smooth Factor",
        description="Blend amount from the current weight to neighbor average",
        min=0.0,
        max=1.0,
        precision=3,
        default=0.5,
        subtype="FACTOR",
    )
    iterations: IntProperty(
        name="Iterations",
        description="Number of synchronous Laplacian smoothing passes",
        min=1,
        soft_max=100,
        default=1,
    )
    include_unselected_neighbors: BoolProperty(
        name="Include Unselected Neighbors",
        description=(
            "Allow adjacent unselected vertices to contribute without changing them"
        ),
        default=True,
    )
    use_inverse_distance: BoolProperty(
        name="Inverse Distance Weighting",
        description=(
            "Weight each neighbor's contribution by the inverse local edge length"
        ),
        default=False,
    )

    def invoke(self, context, _event):
        groups = list(context.active_object.vertex_groups)
        if not groups:
            self.report({"ERROR"}, iface_("At least one vertex group is required."))
            return {"CANCELLED"}
        active_index = context.active_object.vertex_groups.active_index
        active = next(
            (group for group in groups if group.index == active_index),
            groups[0],
        )
        if context.active_object.vertex_groups.get(self.group_name) is None:
            self.group_name = active.name
        return context.window_manager.invoke_props_dialog(self, width=420)

    def draw(self, context):
        layout = self.layout
        layout.prop_search(
            self,
            "group_name",
            context.active_object,
            "vertex_groups",
            text="Vertex Group",
        )
        layout.prop(self, "factor", slider=True)
        layout.prop(self, "iterations")
        layout.prop(self, "include_unselected_neighbors")
        layout.prop(self, "use_inverse_distance")

    def execute(self, context):
        try:
            selected_count, updated_count, group_name = smooth_selected_weights(
                context,
                self.group_name,
                self.factor,
                self.iterations,
                self.include_unselected_neighbors,
                self.use_inverse_distance,
            )
        except (RuntimeError, ValueError) as error:
            self.report({"ERROR"}, iface_(str(error)))
            return {"CANCELLED"}
        self.report(
            {"INFO"},
            iface_format(
                'Smoothed "{name}" on {updated}/{selected} selected vertices.',
                name=group_name,
                updated=updated_count,
                selected=selected_count,
            ),
        )
        return {"FINISHED"}


class WEIGHTTOOL_OT_normalize_selected_weights(
    _SelectedWeightOperator,
    bpy.types.Operator,
):
    bl_idname = "weight_tool.normalize_selected_vertex_weights"
    bl_label = "Normalize Selected Vertex Weights"
    bl_description = (
        "Scale each selected vertex's group weights so their sum equals one"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            selected_count, normalized_count, skipped_count = (
                normalize_selected_weights(context)
            )
        except (RuntimeError, ValueError) as error:
            self.report({"ERROR"}, iface_(str(error)))
            return {"CANCELLED"}

        if skipped_count:
            self.report(
                {"WARNING"},
                iface_format(
                    "Normalized {normalized}/{selected} selected vertices; skipped {skipped} with no non-zero group weights.",
                    normalized=normalized_count,
                    selected=selected_count,
                    skipped=skipped_count,
                ),
            )
        else:
            self.report(
                {"INFO"},
                iface_format(
                    "Normalized all {count} selected vertices.",
                    count=normalized_count,
                ),
            )
        return {"FINISHED"}


OPERATOR_CLASSES = (
    WEIGHTTOOL_PG_mirror_group_item,
    WEIGHTTOOL_UL_mirror_group_selection,
    WEIGHTTOOL_OT_set_selected_group_weight,
    WEIGHTTOOL_OT_remove_selected_from_group,
    WEIGHTTOOL_OT_add_selected_to_new_group,
    WEIGHTTOOL_OT_blend_selected_group_weights,
    WEIGHTTOOL_OT_mirror_selected_group_weights,
    WEIGHTTOOL_OT_smooth_selected_group_weights,
    WEIGHTTOOL_OT_normalize_selected_weights,
)
