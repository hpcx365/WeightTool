"""3D View sidebar UI."""

import bpy

from .translations import iface_
from .weights import group_summaries


class WEIGHTTOOL_UL_selected_vertex_weights(bpy.types.UIList):
    """Scrollable list of groups used by at least one selected vertex."""

    def draw_item(
        self,
        context,
        layout,
        _data,
        item,
        _icon,
        _active_data,
        _active_propname,
        _index,
    ):
        if self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon="GROUP_VERTEX")
            return

        try:
            selected_count, summaries = group_summaries(context)
            summary = next(
                (summary for summary in summaries if summary.index == item.index),
                None,
            )
        except (RuntimeError, ValueError):
            summary = None
            selected_count = 0

        row = layout.row(align=True)
        row.label(text=item.name, icon="GROUP_VERTEX")
        if summary is None:
            row.label(text="-")
            return

        row.label(text=f"{summary.average:.4f}")
        if selected_count > 1:
            row.label(text=f"{summary.member_count}/{selected_count}")

        overwrite = row.operator(
            "weight_tool.set_selected_group_weight",
            text="Set",
        )
        overwrite.group_index = summary.index
        overwrite.weight = summary.average
        remove = row.operator(
            "weight_tool.remove_selected_from_group",
            text="",
            icon="X",
        )
        remove.group_index = summary.index

    def filter_items(self, context, data, propname):
        groups = getattr(data, propname)
        flags = [self.bitflag_filter_item] * len(groups)

        if self.filter_name:
            name_flags = bpy.types.UI_UL_list.filter_items_by_name(
                self.filter_name,
                self.bitflag_filter_item,
                groups,
                "name",
                reverse=self.use_filter_invert,
            )
            if name_flags:
                flags = name_flags

        try:
            _selected_count, summaries = group_summaries(context)
            included = {summary.index for summary in summaries}
        except (RuntimeError, ValueError):
            included = set()

        for position, group in enumerate(groups):
            if group.index not in included:
                flags[position] = 0
        return flags, []


class VIEW3D_PT_weight_tool(bpy.types.Panel):
    bl_label = "Weight Tool"
    bl_idname = "VIEW3D_PT_weight_tool"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Weight Tool"
    bl_context = "mesh_edit"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "MESH" and obj.mode == "EDIT"

    def draw(self, context):
        layout = self.layout
        if tuple(context.tool_settings.mesh_select_mode) != (True, False, False):
            layout.label(text=iface_("Vertex Select mode is required"), icon="ERROR")
            return

        try:
            selected_count, summaries = group_summaries(context)
        except (RuntimeError, ValueError) as error:
            layout.label(text=iface_(str(error)), icon="INFO")
            return

        header = layout.row()
        selection_label = (
            "{count} selected vertex"
            if selected_count == 1
            else "{count} selected vertices"
        )
        header.label(
            text=iface_(selection_label).format(count=selected_count),
            icon="VERTEXSEL",
        )

        if not summaries:
            box = layout.box()
            box.label(text="No non-zero group weights", icon="INFO")
        else:
            layout.template_list(
                "WEIGHTTOOL_UL_selected_vertex_weights",
                "selected_groups",
                context.active_object,
                "vertex_groups",
                context.active_object.vertex_groups,
                "active_index",
                rows=8,
                maxrows=8,
            )

        layout.separator()
        blend_row = layout.row()
        blend_row.enabled = len(context.active_object.vertex_groups) >= 2
        blend_row.operator(
            "weight_tool.blend_selected_group_weights",
            icon="GROUP_VERTEX",
        )
        mirror_row = layout.row()
        mirror_row.enabled = bool(context.active_object.vertex_groups)
        mirror_row.operator(
            "weight_tool.mirror_selected_group_weights",
            icon="MOD_MIRROR",
        )
        smooth_row = layout.row()
        smooth_row.enabled = bool(context.active_object.vertex_groups)
        smooth_row.operator(
            "weight_tool.smooth_selected_group_weights",
            icon="MOD_SMOOTH",
        )
        layout.operator(
            "weight_tool.normalize_selected_vertex_weights",
            icon="MOD_VERTEX_WEIGHT",
        )
        layout.operator(
            "weight_tool.add_selected_to_new_group",
            icon="ADD",
        )


UI_CLASSES = (
    WEIGHTTOOL_UL_selected_vertex_weights,
    VIEW3D_PT_weight_tool,
)
