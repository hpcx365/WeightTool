"""English and Simplified Chinese translations for Weight Tool."""

import bpy


ZH_HANS = {
    "Weight Tool": "权重工具",
    "Use": "使用",
    "Set": "设置",
    "Weight": "权重",
    "Group Name": "顶点组名称",
    "Vertex Group": "顶点组",
    "Group A": "顶点组 A",
    "Group B": "顶点组 B",
    "Group A (Output)": "顶点组 A（输出）",
    "Blend Mode": "混合模式",
    "Direction": "方向",
    "Mirror Tolerance": "镜像容差",
    "Smooth Factor": "平滑度",
    "Iterations": "迭代次数",
    "Include Unselected Neighbors": "包含未选中的邻居",
    "Inverse Distance Weighting": "按距离倒数加权",
    "Replace": "替换",
    "Add": "相加",
    "Subtract": "相减",
    "Multiply": "相乘",
    "Maximum": "最大值",
    "Minimum": "最小值",
    "Average": "平均值",
    "Left to Right": "从左到右",
    "Right to Left": "从右到左",
    "Overwrite Selected Vertex Weights": "覆写所选顶点权重",
    "Remove Selected Vertices from Group": "从顶点组移除所选顶点",
    "Add Selected to New Vertex Group": "将所选顶点加入新顶点组",
    "Blend Selected Vertex Weights": "混合所选顶点权重",
    "Mirror Selected Vertex Weights": "镜像所选顶点权重",
    "Smooth Selected Vertex Weights": "平滑所选顶点权重",
    "Normalize Selected Vertex Weights": "归一化所选顶点权重",
    "Vertex Select mode is required": "需要使用顶点选择模式",
    "An active mesh in Edit Mode is required": "需要一个处于编辑模式的活动网格",
    "No non-zero group weights": "没有非零顶点组权重",
    "{count} selected vertex": "已选择 {count} 个顶点",
    "{count} selected vertices": "已选择 {count} 个顶点",
    "Result is clamped to 0-1 and written to Group A": "结果会限制在 0 到 1，并写入顶点组 A",
    "Set this group to one weight on every selected vertex": "将所有所选顶点在此组中的权重设为同一数值",
    "New weight for every selected vertex; zero removes membership": "所有所选顶点的新权重；设为零会移除组成员关系",
    "Remove every selected vertex from this vertex group": "从此顶点组移除所有所选顶点",
    "Create a new vertex group and assign all selected vertices": "新建顶点组并分配所有所选顶点",
    "Name of the new vertex group": "新顶点组的名称",
    "Weight assigned to every selected vertex": "分配给每个所选顶点的权重",
    "Blend group A with group B per selected vertex and write the result to A": "逐顶点混合 A 与 B，并将结果写入 A",
    "Blend weights between selected vertex pairs mirrored across local X=0": "在局部 X=0 平面两侧的所选镜像顶点对之间混合权重",
    "Maximum local-space distance from an exact X-axis mirror": "相对于精确 X 轴镜像的最大局部空间距离",
    "Laplacian-smooth one vertex group over the selected mesh vertices": "对所选网格顶点的一个顶点组进行拉普拉斯平滑",
    "Blend amount from the current weight to neighbor average": "当前权重向邻居平均值混合的程度",
    "Number of synchronous Laplacian smoothing passes": "同步拉普拉斯平滑的迭代次数",
    "Allow adjacent unselected vertices to contribute without changing them": "允许相邻未选中顶点参与计算，但不修改它们",
    "Weight each neighbor's contribution by the inverse local edge length": "按局部边长的倒数分配每个邻居的贡献",
    "Scale each selected vertex's group weights so their sum equals one": "缩放每个所选顶点的组权重，使其总和等于一",
    "At least one vertex group is required.": "至少需要一个顶点组。",
    "At least two vertex groups are required.": "至少需要两个顶点组。",
    "The specified vertex group no longer exists.": "指定的顶点组已不存在。",
    "Select at least one visible vertex.": "请至少选择一个可见顶点。",
    "Switch to Vertex Select mode first.": "请先切换到顶点选择模式。",
    "Select at least one vertex group to mirror.": "请至少选择一个要镜像的顶点组。",
    "Mirror tolerance must be greater than zero.": "镜像容差必须大于零。",
    "Smooth factor must be between zero and one.": "平滑度必须在零到一之间。",
    "Iterations must be at least one.": "迭代次数必须至少为一。",
    "Enter a vertex-group name.": "请输入顶点组名称。",
    "The weight for a new group must be greater than zero.": "新顶点组的权重必须大于零。",
    "Set {count} vertices in \"{name}\" to {weight:.4f}.": "已将“{name}”中的 {count} 个顶点设为 {weight:.4f}。",
    "Removed {count} selected vertices from \"{name}\".": "已从“{name}”移除 {count} 个所选顶点。",
    "Added {count} selected vertices to new group \"{name}\" at {weight:.4f}.": "已将 {count} 个所选顶点以权重 {weight:.4f} 加入新组“{name}”。",
    "Blended \"{group_a}\" with \"{group_b}\" using {mode} on {count} vertices.": "已使用{mode}在 {count} 个顶点上混合“{group_a}”与“{group_b}”。",
    "Mirrored {channels} weight channels across {pairs} vertex pairs using {mode}.": "已使用{mode}在 {pairs} 对顶点间镜像 {channels} 个权重通道。",
    "Smoothed \"{name}\" on {updated}/{selected} selected vertices.": "已平滑“{name}”，修改了 {updated}/{selected} 个所选顶点。",
    "Normalized {normalized}/{selected} selected vertices; skipped {skipped} with no non-zero group weights.": "已归一化 {normalized}/{selected} 个所选顶点；跳过 {skipped} 个无非零组权重的顶点。",
    "Normalized all {count} selected vertices.": "已归一化全部 {count} 个所选顶点。",
}


def _catalog(entries):
    contexts = ("*", "Operator")
    return {
        (context, source): translated
        for source, translated in entries.items()
        for context in contexts
    }


TRANSLATIONS = {
    "en_US": _catalog({source: source for source in ZH_HANS}),
    "zh_HANS": _catalog(ZH_HANS),
}


def iface_(message):
    return bpy.app.translations.pgettext_iface(message)


def iface_format(message, **values):
    return iface_(message).format(**values)
