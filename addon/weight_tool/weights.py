"""BMesh vertex-group weight access used by the UI and operators."""

from dataclasses import dataclass

import bmesh
from mathutils.kdtree import KDTree


WEIGHT_EPSILON = 1.0e-8


@dataclass(frozen=True)
class GroupSummary:
    index: int
    name: str
    average: float
    member_count: int


def edit_mesh_state(context, create_deform_layer=False):
    obj = context.active_object
    if obj is None or obj.type != "MESH" or obj.mode != "EDIT":
        raise ValueError("An active mesh object in Edit Mode is required.")
    if tuple(context.tool_settings.mesh_select_mode) != (True, False, False):
        raise ValueError("Switch to Vertex Select mode first.")

    bm = bmesh.from_edit_mesh(obj.data)
    selected = tuple(
        vertex for vertex in bm.verts if vertex.select and not vertex.hide
    )
    if not selected:
        raise ValueError("Select at least one visible vertex.")
    deform_layer = bm.verts.layers.deform.active
    if deform_layer is None and create_deform_layer:
        deform_layer = bm.verts.layers.deform.verify()
    return obj, bm, selected, deform_layer


def group_summaries(context):
    obj, _bm, selected, deform_layer = edit_mesh_state(context)
    if deform_layer is None:
        return len(selected), ()
    totals = {}
    members = {}
    groups = {group.index: group for group in obj.vertex_groups}

    for vertex in selected:
        for group_index, weight in vertex[deform_layer].items():
            if group_index not in groups or weight <= WEIGHT_EPSILON:
                continue
            totals[group_index] = totals.get(group_index, 0.0) + weight
            members[group_index] = members.get(group_index, 0) + 1

    count = len(selected)
    summaries = tuple(
        GroupSummary(
            index=group_index,
            name=groups[group_index].name,
            average=totals[group_index] / count,
            member_count=members[group_index],
        )
        for group_index in sorted(
            totals,
            key=lambda index: groups[index].name.casefold(),
        )
    )
    return count, summaries


def set_selected_weight(context, group_index, weight):
    obj, bm, selected, deform_layer = edit_mesh_state(
        context,
        create_deform_layer=True,
    )
    group = next(
        (group for group in obj.vertex_groups if group.index == group_index),
        None,
    )
    if group is None:
        raise ValueError("The specified vertex group no longer exists.")

    for vertex in selected:
        deform = vertex[deform_layer]
        if weight <= WEIGHT_EPSILON:
            if group_index in deform:
                del deform[group_index]
        else:
            deform[group_index] = weight
    bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
    return len(selected), group.name


def blend_selected_weights(context, group_a_name, group_b_name, mode):
    obj, bm, selected, deform_layer = edit_mesh_state(
        context,
        create_deform_layer=True,
    )
    group_a = obj.vertex_groups.get(group_a_name)
    group_b = obj.vertex_groups.get(group_b_name)
    if group_a is None:
        raise ValueError(f'Vertex group A "{group_a_name}" does not exist.')
    if group_b is None:
        raise ValueError(f'Vertex group B "{group_b_name}" does not exist.')
    if group_a.index == group_b.index:
        raise ValueError("Vertex groups A and B must be different.")

    operations = {
        "REPLACE": lambda _a, b: b,
        "ADD": lambda a, b: a + b,
        "SUBTRACT": lambda a, b: a - b,
        "MULTIPLY": lambda a, b: a * b,
        "MAXIMUM": max,
        "MINIMUM": min,
        "AVERAGE": lambda a, b: (a + b) * 0.5,
    }
    operation = operations.get(mode)
    if operation is None:
        raise ValueError(f'Unknown blend mode "{mode}".')

    results = []
    for vertex in selected:
        deform = vertex[deform_layer]
        weight_a = deform.get(group_a.index, 0.0)
        weight_b = deform.get(group_b.index, 0.0)
        result = max(0.0, min(1.0, operation(weight_a, weight_b)))
        results.append((vertex, result))

    for vertex, result in results:
        deform = vertex[deform_layer]
        if result <= WEIGHT_EPSILON:
            if group_a.index in deform:
                del deform[group_a.index]
        else:
            deform[group_a.index] = result
    bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
    return len(selected), group_a.name, group_b.name


def _selected_mirror_pairs(selected, tolerance):
    left = [vertex for vertex in selected if vertex.co.x < -tolerance]
    right = [vertex for vertex in selected if vertex.co.x > tolerance]
    if not left or not right:
        return ()

    left_tree = KDTree(len(left))
    for index, vertex in enumerate(left):
        left_tree.insert(vertex.co, index)
    left_tree.balance()

    right_tree = KDTree(len(right))
    for index, vertex in enumerate(right):
        right_tree.insert(vertex.co, index)
    right_tree.balance()

    def candidates(tree, vertices, vertex):
        mirrored = vertex.co.copy()
        mirrored.x = -mirrored.x
        return tuple(
            vertices[index]
            for _coordinate, index, _distance in tree.find_range(
                mirrored,
                tolerance,
            )
        )

    right_by_left = {
        vertex: candidates(right_tree, right, vertex)
        for vertex in left
    }
    left_by_right = {
        vertex: candidates(left_tree, left, vertex)
        for vertex in right
    }
    return tuple(
        (left_vertex, matches[0])
        for left_vertex, matches in right_by_left.items()
        if len(matches) == 1
        and len(left_by_right[matches[0]]) == 1
        and left_by_right[matches[0]][0] is left_vertex
    )


def mirror_selected_weights(context, group_names, mode, direction, tolerance):
    obj, bm, selected, deform_layer = edit_mesh_state(
        context,
        create_deform_layer=True,
    )
    selected_groups = {}
    for group_name in group_names:
        group = obj.vertex_groups.get(group_name)
        if group is None:
            raise ValueError(f'Vertex group "{group_name}" does not exist.')
        selected_groups[group.name] = group
    if not selected_groups:
        raise ValueError("Select at least one vertex group to mirror.")
    if tolerance <= 0.0:
        raise ValueError("Mirror tolerance must be greater than zero.")

    pairs = _selected_mirror_pairs(selected, tolerance)
    if not pairs:
        raise ValueError(
            "No uniquely mirrored vertex pairs were found within the selection."
        )

    symmetric_operations = {
        "ADD": lambda left, right: left + right,
        "MULTIPLY": lambda left, right: left * right,
        "MAXIMUM": max,
        "MINIMUM": min,
        "AVERAGE": lambda left, right: (left + right) * 0.5,
    }
    if mode not in {"REPLACE", "SUBTRACT", *symmetric_operations}:
        raise ValueError(f'Unknown mirror blend mode "{mode}".')
    if direction not in {"LEFT_TO_RIGHT", "RIGHT_TO_LEFT"}:
        raise ValueError(f'Unknown mirror direction "{direction}".')

    paired_channels = []
    paired_group_names = set()
    for name, left_group in selected_groups.items():
        if not name.endswith(".L"):
            continue
        right_name = f"{name[:-2]}.R"
        right_group = selected_groups.get(right_name)
        if right_group is None:
            continue
        paired_channels.append((left_group, right_group))
        paired_group_names.update((name, right_name))

    results = {}
    eligible_pair_count = 0
    channel_count = 0
    for left_vertex, right_vertex in pairs:
        channels = []
        left_deform = left_vertex[deform_layer]
        right_deform = right_vertex[deform_layer]

        for name, group in selected_groups.items():
            if name in paired_group_names:
                continue
            if (
                left_deform.get(group.index, 0.0) > WEIGHT_EPSILON
                and right_deform.get(group.index, 0.0) > WEIGHT_EPSILON
            ):
                channels.append((group, group))

        for left_group, right_group in paired_channels:
            if (
                left_deform.get(left_group.index, 0.0) > WEIGHT_EPSILON
                and right_deform.get(right_group.index, 0.0) > WEIGHT_EPSILON
            ):
                channels.append((left_group, right_group))

        if channels:
            eligible_pair_count += 1
        channel_count += len(channels)
        for left_group, right_group in channels:
            left_weight = left_deform.get(left_group.index, 0.0)
            right_weight = right_deform.get(right_group.index, 0.0)
            if mode == "REPLACE":
                if direction == "LEFT_TO_RIGHT":
                    results[(right_vertex, right_group.index)] = left_weight
                else:
                    results[(left_vertex, left_group.index)] = right_weight
            elif mode == "SUBTRACT":
                if direction == "LEFT_TO_RIGHT":
                    results[(right_vertex, right_group.index)] = (
                        left_weight - right_weight
                    )
                else:
                    results[(left_vertex, left_group.index)] = (
                        right_weight - left_weight
                    )
            else:
                result = symmetric_operations[mode](left_weight, right_weight)
                results[(left_vertex, left_group.index)] = result
                results[(right_vertex, right_group.index)] = result

    if not results:
        raise ValueError(
            "No selected mirror pair shares a selected group or matching .L/.R groups."
        )

    for (vertex, group_index), result in results.items():
        result = max(0.0, min(1.0, result))
        deform = vertex[deform_layer]
        if result <= WEIGHT_EPSILON:
            if group_index in deform:
                del deform[group_index]
        else:
            deform[group_index] = result
    bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
    return eligible_pair_count, channel_count


def smooth_selected_weights(
    context,
    group_name,
    factor,
    iterations,
    include_unselected_neighbors,
    use_inverse_distance,
):
    obj, bm, selected, deform_layer = edit_mesh_state(
        context,
        create_deform_layer=True,
    )
    group = obj.vertex_groups.get(group_name)
    if group is None:
        raise ValueError(f'Vertex group "{group_name}" does not exist.')
    if not 0.0 <= factor <= 1.0:
        raise ValueError("Smooth factor must be between zero and one.")
    if iterations < 1:
        raise ValueError("Iterations must be at least one.")

    selected_set = set(selected)
    current = {
        vertex: vertex[deform_layer].get(group.index, 0.0)
        for vertex in bm.verts
    }
    updated_count = 0
    for _iteration in range(iterations):
        next_values = {}
        for vertex in selected:
            neighbors = tuple(
                (edge.other_vert(vertex), edge.calc_length())
                for edge in vertex.link_edges
                if (
                    include_unselected_neighbors
                    or edge.other_vert(vertex) in selected_set
                )
            )
            if not neighbors:
                next_values[vertex] = current[vertex]
                continue
            if use_inverse_distance:
                coincident = tuple(
                    neighbor
                    for neighbor, distance in neighbors
                    if distance <= WEIGHT_EPSILON
                )
                if coincident:
                    neighbor_average = sum(
                        current[neighbor] for neighbor in coincident
                    ) / len(coincident)
                else:
                    weighted_sum = sum(
                        current[neighbor] / distance
                        for neighbor, distance in neighbors
                    )
                    total_weight = sum(
                        1.0 / distance for _neighbor, distance in neighbors
                    )
                    neighbor_average = weighted_sum / total_weight
            else:
                neighbor_average = sum(
                    current[neighbor] for neighbor, _distance in neighbors
                ) / len(neighbors)
            next_values[vertex] = (
                current[vertex] * (1.0 - factor)
                + neighbor_average * factor
            )
        current.update(next_values)

    for vertex in selected:
        result = max(0.0, min(1.0, current[vertex]))
        deform = vertex[deform_layer]
        old_weight = deform.get(group.index, 0.0)
        if abs(result - old_weight) > WEIGHT_EPSILON:
            updated_count += 1
        if result <= WEIGHT_EPSILON:
            if group.index in deform:
                del deform[group.index]
        else:
            deform[group.index] = result
    bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
    return len(selected), updated_count, group.name


def normalize_selected_weights(context):
    obj, bm, selected, deform_layer = edit_mesh_state(
        context,
        create_deform_layer=True,
    )
    valid_indices = {group.index for group in obj.vertex_groups}
    normalized_count = 0
    skipped_count = 0

    for vertex in selected:
        deform = vertex[deform_layer]
        weighted_groups = tuple(
            (group_index, weight)
            for group_index, weight in deform.items()
            if group_index in valid_indices and weight > WEIGHT_EPSILON
        )
        total = sum(weight for _group_index, weight in weighted_groups)
        if not weighted_groups or total <= WEIGHT_EPSILON:
            skipped_count += 1
            continue
        inverse_total = 1.0 / total
        for group_index, weight in weighted_groups:
            deform[group_index] = weight * inverse_total
        normalized_count += 1

    bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
    return len(selected), normalized_count, skipped_count


def create_group_and_assign(context, name, weight):
    obj, bm, selected, deform_layer = edit_mesh_state(
        context,
        create_deform_layer=True,
    )
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Enter a vertex-group name.")
    if obj.vertex_groups.get(clean_name) is not None:
        raise ValueError(f'Vertex group "{clean_name}" already exists.')
    if weight <= WEIGHT_EPSILON:
        raise ValueError("The weight for a new group must be greater than zero.")

    group = obj.vertex_groups.new(name=clean_name)
    try:
        for vertex in selected:
            vertex[deform_layer][group.index] = weight
        bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)
    except Exception:
        obj.vertex_groups.remove(group)
        raise
    return len(selected), group.name
