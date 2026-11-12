"""Blender integration tests for Weight Tool."""

import importlib
import math
import pathlib
import sys

import bmesh
import bpy


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "addon"))
addon = importlib.import_module("weight_tool")
weights = importlib.import_module("weight_tool.weights")


def reset_scene():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def test_simplified_chinese_translation():
    preferences = bpy.context.preferences.view
    original_language = preferences.language
    original_translate = preferences.use_translate_interface
    try:
        preferences.language = "zh_HANS"
        preferences.use_translate_interface = True
        assert bpy.app.translations.pgettext_iface("Weight Tool") == "权重工具"
        assert (
            bpy.app.translations.pgettext_iface("Smooth Selected Vertex Weights")
            == "平滑所选顶点权重"
        )
    finally:
        preferences.language = original_language
        preferences.use_translate_interface = original_translate


def create_weighted_mesh():
    mesh = bpy.data.meshes.new("WeightsTest")
    mesh.from_pydata(
        [(0, 0, 0), (1, 0, 0), (0, 1, 0)],
        [],
        [(0, 1, 2)],
    )
    obj = bpy.data.objects.new("WeightsTest", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    first = obj.vertex_groups.new(name="First")
    first.add([0], 0.2, "REPLACE")
    first.add([1], 0.6, "REPLACE")
    second = obj.vertex_groups.new(name="Second")
    second.add([2], 0.9, "REPLACE")

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.context.tool_settings.mesh_select_mode = (True, False, False)
    bm = bmesh.from_edit_mesh(mesh)
    for vertex in bm.verts:
        vertex.select_set(True)
    bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
    return obj, first.index, second.index


def selected_weights(obj, group_index):
    bm = bmesh.from_edit_mesh(obj.data)
    layer = bm.verts.layers.deform.active
    return [
        vertex[layer].get(group_index, 0.0)
        for vertex in bm.verts
        if vertex.select
    ]


def all_weights(obj, group_index):
    bm = bmesh.from_edit_mesh(obj.data)
    layer = bm.verts.layers.deform.active
    return [vertex[layer].get(group_index, 0.0) for vertex in bm.verts]


def assert_weights(actual, expected):
    assert len(actual) == len(expected)
    assert all(
        math.isclose(value, wanted, abs_tol=1.0e-6)
        for value, wanted in zip(actual, expected)
    ), (actual, expected)


def assign_edit_weights(obj, group_index, values):
    bm = bmesh.from_edit_mesh(obj.data)
    layer = bm.verts.layers.deform.verify()
    for vertex, value in zip(bm.verts, values):
        deform = vertex[layer]
        if value == 0.0:
            if group_index in deform:
                del deform[group_index]
        else:
            deform[group_index] = value
    bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)


def test_union_and_zero_inclusive_average(obj):
    count, summaries = weights.group_summaries(bpy.context)
    by_name = {summary.name: summary for summary in summaries}
    assert count == 3
    assert set(by_name) == {"First", "Second"}
    assert by_name["First"].member_count == 2
    assert math.isclose(by_name["First"].average, 0.8 / 3.0, abs_tol=1.0e-6)
    assert by_name["Second"].member_count == 1
    assert math.isclose(by_name["Second"].average, 0.3, abs_tol=1.0e-6)


def test_overwrite_adds_missing_members(obj, group_index):
    result = bpy.ops.weight_tool.set_selected_group_weight(
        "EXEC_DEFAULT",
        group_index=group_index,
        weight=0.45,
    )
    assert result == {"FINISHED"}, result
    assert all(
        math.isclose(weight, 0.45, abs_tol=1.0e-6)
        for weight in selected_weights(obj, group_index)
    )


def test_remove_keeps_group(obj, group_index):
    group_name = next(
        group.name for group in obj.vertex_groups if group.index == group_index
    )
    result = bpy.ops.weight_tool.remove_selected_from_group(
        "EXEC_DEFAULT",
        group_index=group_index,
    )
    assert result == {"FINISHED"}, result
    assert obj.vertex_groups.get(group_name) is not None
    assert selected_weights(obj, group_index) == [0.0, 0.0, 0.0]


def test_create_new_group(obj):
    result = bpy.ops.weight_tool.add_selected_to_new_group(
        "EXEC_DEFAULT",
        group_name="Fresh",
        weight=0.7,
    )
    assert result == {"FINISHED"}, result
    group = obj.vertex_groups.get("Fresh")
    assert group is not None
    assert all(
        math.isclose(weight, 0.7, abs_tol=1.0e-6)
        for weight in selected_weights(obj, group.index)
    )


def create_mirror_mesh():
    mesh = bpy.data.meshes.new("MirrorTest")
    mesh.from_pydata(
        [
            (-1, 0, 0),
            (1, 0, 0),
            (-2, 1, 0),
            (2, 1, 0),
            (0, 2, 0),
            (-3, 2, 0),
            (3, 2, 0),
        ],
        [],
        [(0, 1, 3, 2), (2, 3, 4)],
    )
    obj = bpy.data.objects.new("MirrorTest", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    group = obj.vertex_groups.new(name="Mirror")
    group.add([0, 1, 2, 3, 4, 5, 6], 0.0, "REPLACE")
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.context.tool_settings.mesh_select_mode = (True, False, False)
    bm = bmesh.from_edit_mesh(mesh)
    for vertex in bm.verts:
        vertex.select_set(vertex.index != 6)
    bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
    return obj, group.index


def test_mirror_modes_and_directions(obj, group_index):
    group = next(group for group in obj.vertex_groups if group.index == group_index)
    source = [0.2, 0.8, 0.4, 0.6, 0.9, 0.3, 0.7]
    assign_edit_weights(obj, group_index, source)

    result = weights.mirror_selected_weights(
        bpy.context,
        (group.name,),
        "REPLACE",
        "LEFT_TO_RIGHT",
        1.0e-5,
    )
    assert result == (2, 2), result
    assert_weights(
        all_weights(obj, group_index),
        [0.2, 0.2, 0.4, 0.4, 0.9, 0.3, 0.7],
    )

    assign_edit_weights(obj, group_index, source)
    result = weights.mirror_selected_weights(
        bpy.context,
        (group.name,),
        "REPLACE",
        "RIGHT_TO_LEFT",
        1.0e-5,
    )
    assert result == (2, 2), result
    assert_weights(
        all_weights(obj, group_index),
        [0.8, 0.8, 0.6, 0.6, 0.9, 0.3, 0.7],
    )

    assign_edit_weights(obj, group_index, source)
    result = weights.mirror_selected_weights(
        bpy.context,
        (group.name,),
        "SUBTRACT",
        "LEFT_TO_RIGHT",
        1.0e-5,
    )
    assert result == (2, 2), result
    assert_weights(
        all_weights(obj, group_index),
        [0.2, 0.0, 0.4, 0.0, 0.9, 0.3, 0.7],
    )

    assign_edit_weights(obj, group_index, source)
    result = weights.mirror_selected_weights(
        bpy.context,
        (group.name,),
        "SUBTRACT",
        "RIGHT_TO_LEFT",
        1.0e-5,
    )
    assert result == (2, 2), result
    assert_weights(
        all_weights(obj, group_index),
        [0.6, 0.8, 0.2, 0.6, 0.9, 0.3, 0.7],
    )

    symmetric_expected = {
        "ADD": [1.0, 1.0, 1.0, 1.0],
        "MULTIPLY": [0.16, 0.16, 0.24, 0.24],
        "MAXIMUM": [0.8, 0.8, 0.6, 0.6],
        "MINIMUM": [0.2, 0.2, 0.4, 0.4],
        "AVERAGE": [0.5, 0.5, 0.5, 0.5],
    }
    for mode, paired_weights in symmetric_expected.items():
        assign_edit_weights(obj, group_index, source)
        result = weights.mirror_selected_weights(
            bpy.context,
            (group.name,),
            mode,
            "LEFT_TO_RIGHT",
            1.0e-5,
        )
        assert result == (2, 2), (mode, result)
        assert_weights(
            all_weights(obj, group_index),
            [*paired_weights, 0.9, 0.3, 0.7],
        )


def test_multi_group_mirror_rules(obj, shared_group_index):
    bpy.ops.object.mode_set(mode="OBJECT")
    left_group = obj.vertex_groups.new(name="Arm.L")
    right_group = obj.vertex_groups.new(name="Arm.R")
    unrelated = obj.vertex_groups.new(name="Unrelated")
    bpy.ops.object.mode_set(mode="EDIT")

    assign_edit_weights(obj, shared_group_index, [0.2, 0.8, 0, 0, 0, 0, 0])
    assign_edit_weights(obj, left_group.index, [0.3, 0, 0, 0, 0, 0, 0])
    assign_edit_weights(obj, right_group.index, [0, 0.7, 0, 0, 0, 0, 0])
    assign_edit_weights(obj, unrelated.index, [0.4, 0, 0, 0, 0, 0, 0])

    pair_count, channel_count = weights.mirror_selected_weights(
        bpy.context,
        ("Mirror", "Arm.L", "Arm.R", "Unrelated"),
        "REPLACE",
        "LEFT_TO_RIGHT",
        1.0e-5,
    )
    assert (pair_count, channel_count) == (1, 2)
    assert_weights(
        all_weights(obj, shared_group_index),
        [0.2, 0.2, 0, 0, 0, 0, 0],
    )
    assert_weights(
        all_weights(obj, right_group.index),
        [0, 0.3, 0, 0, 0, 0, 0],
    )
    assert_weights(
        all_weights(obj, unrelated.index),
        [0.4, 0, 0, 0, 0, 0, 0],
    )


def create_smooth_mesh():
    mesh = bpy.data.meshes.new("SmoothTest")
    mesh.from_pydata(
        [(0, 0, 0), (1, 0, 0), (3, 0, 0), (4, 0, 0)],
        [(0, 1), (1, 2), (2, 3)],
        [],
    )
    obj = bpy.data.objects.new("SmoothTest", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    group = obj.vertex_groups.new(name="Smooth")
    group.add([0, 3], 1.0, "REPLACE")
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.context.tool_settings.mesh_select_mode = (True, False, False)
    bm = bmesh.from_edit_mesh(mesh)
    for vertex in bm.verts:
        vertex.select_set(vertex.index in {1, 2})
    bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
    return obj, group.index


def test_smoothing_neighbor_scope_and_iterations(obj, group_index):
    group = next(group for group in obj.vertex_groups if group.index == group_index)

    result = bpy.ops.weight_tool.smooth_selected_group_weights(
        "EXEC_DEFAULT",
        group_name=group.name,
        factor=0.5,
        iterations=1,
        include_unselected_neighbors=True,
    )
    assert result == {"FINISHED"}, result
    assert_weights(all_weights(obj, group_index), [1.0, 0.25, 0.25, 1.0])

    assign_edit_weights(obj, group_index, [1.0, 0.0, 0.0, 1.0])
    result = bpy.ops.weight_tool.smooth_selected_group_weights(
        "EXEC_DEFAULT",
        group_name=group.name,
        factor=1.0,
        iterations=1,
        include_unselected_neighbors=True,
    )
    assert result == {"FINISHED"}, result
    assert_weights(all_weights(obj, group_index), [1.0, 0.5, 0.5, 1.0])

    assign_edit_weights(obj, group_index, [1.0, 0.0, 0.0, 1.0])
    result = bpy.ops.weight_tool.smooth_selected_group_weights(
        "EXEC_DEFAULT",
        group_name=group.name,
        factor=1.0,
        iterations=1,
        include_unselected_neighbors=True,
        use_inverse_distance=True,
    )
    assert result == {"FINISHED"}, result
    assert_weights(
        all_weights(obj, group_index),
        [1.0, 2.0 / 3.0, 2.0 / 3.0, 1.0],
    )

    assign_edit_weights(obj, group_index, [1.0, 0.0, 0.0, 1.0])
    result = bpy.ops.weight_tool.smooth_selected_group_weights(
        "EXEC_DEFAULT",
        group_name=group.name,
        factor=1.0,
        iterations=1,
        include_unselected_neighbors=False,
    )
    assert result == {"FINISHED"}, result
    assert_weights(all_weights(obj, group_index), [1.0, 0.0, 0.0, 1.0])

    assign_edit_weights(obj, group_index, [1.0, 0.0, 0.0, 1.0])
    result = bpy.ops.weight_tool.smooth_selected_group_weights(
        "EXEC_DEFAULT",
        group_name=group.name,
        factor=1.0,
        iterations=2,
        include_unselected_neighbors=True,
    )
    assert result == {"FINISHED"}, result
    assert_weights(all_weights(obj, group_index), [1.0, 0.75, 0.75, 1.0])


def create_normalize_mesh():
    mesh = bpy.data.meshes.new("NormalizeTest")
    mesh.from_pydata([(index, 0, 0) for index in range(5)], [], [])
    obj = bpy.data.objects.new("NormalizeTest", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    first = obj.vertex_groups.new(name="NormalizeA")
    second = obj.vertex_groups.new(name="NormalizeB")
    first.add([0], 0.2, "REPLACE")
    second.add([0], 0.3, "REPLACE")
    first.add([1], 0.25, "REPLACE")
    first.add([4], 0.2, "REPLACE")
    second.add([4], 0.3, "REPLACE")

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.context.tool_settings.mesh_select_mode = (True, False, False)
    bm = bmesh.from_edit_mesh(mesh)
    bm.verts.ensure_lookup_table()
    layer = bm.verts.layers.deform.verify()
    bm.verts[3][layer][first.index] = 0.0
    for vertex in bm.verts:
        vertex.select_set(vertex.index < 4)
    bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
    return obj, first.index, second.index


def test_normalize_and_skip_counts(obj, first_index, second_index):
    counts = weights.normalize_selected_weights(bpy.context)
    assert counts == (4, 2, 2), counts
    assert_weights(
        all_weights(obj, first_index),
        [0.4, 1.0, 0.0, 0.0, 0.2],
    )
    assert_weights(
        all_weights(obj, second_index),
        [0.6, 0.0, 0.0, 0.0, 0.3],
    )
    result = bpy.ops.weight_tool.normalize_selected_vertex_weights("EXEC_DEFAULT")
    assert result == {"FINISHED"}, result


def test_all_blend_modes(obj, group_a_index, group_b_index):
    group_a = next(
        group for group in obj.vertex_groups if group.index == group_a_index
    )
    group_b = next(
        group for group in obj.vertex_groups if group.index == group_b_index
    )
    source_a = [0.2, 0.8, 0.0]
    source_b = [0.5, 0.4, 1.0]
    expected_by_mode = {
        "REPLACE": [0.5, 0.4, 1.0],
        "ADD": [0.7, 1.0, 1.0],
        "SUBTRACT": [0.0, 0.4, 0.0],
        "MULTIPLY": [0.1, 0.32, 0.0],
        "MAXIMUM": [0.5, 0.8, 1.0],
        "MINIMUM": [0.2, 0.4, 0.0],
        "AVERAGE": [0.35, 0.6, 0.5],
    }

    for mode, expected in expected_by_mode.items():
        assign_edit_weights(obj, group_a_index, source_a)
        assign_edit_weights(obj, group_b_index, source_b)
        result = bpy.ops.weight_tool.blend_selected_group_weights(
            "EXEC_DEFAULT",
            group_a=group_a.name,
            group_b=group_b.name,
            mode=mode,
        )
        assert result == {"FINISHED"}, (mode, result)
        actual = selected_weights(obj, group_a_index)
        assert all(
            math.isclose(value, wanted, abs_tol=1.0e-6)
            for value, wanted in zip(actual, expected)
        ), (mode, actual, expected)
        unchanged_b = selected_weights(obj, group_b_index)
        assert all(
            math.isclose(value, wanted, abs_tol=1.0e-6)
            for value, wanted in zip(unchanged_b, source_b)
        ), (mode, unchanged_b, source_b)


def main():
    addon.register()
    try:
        test_simplified_chinese_translation()
        reset_scene()
        obj, first_index, second_index = create_weighted_mesh()
        test_union_and_zero_inclusive_average(obj)
        test_overwrite_adds_missing_members(obj, first_index)
        test_remove_keeps_group(obj, second_index)
        test_all_blend_modes(obj, first_index, second_index)
        test_create_new_group(obj)
        reset_scene()
        mirror_obj, mirror_group_index = create_mirror_mesh()
        test_mirror_modes_and_directions(mirror_obj, mirror_group_index)
        test_multi_group_mirror_rules(mirror_obj, mirror_group_index)
        reset_scene()
        smooth_obj, smooth_group_index = create_smooth_mesh()
        test_smoothing_neighbor_scope_and_iterations(
            smooth_obj,
            smooth_group_index,
        )
        reset_scene()
        normalize_obj, normalize_first, normalize_second = create_normalize_mesh()
        test_normalize_and_skip_counts(
            normalize_obj,
            normalize_first,
            normalize_second,
        )
    finally:
        reset_scene()
        addon.unregister()
    print("All Weight Tool integration tests passed")


if __name__ == "__main__":
    main()
