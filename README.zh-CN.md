# Weight Tool

[English](README.md)

Weight Tool 是一个适用于 Blender 4.2+ 的顶点组权重工具，可在网格编辑模式中查看和修改权重。所有操作只影响当前选中且未隐藏的顶点。

## 功能

在顶点选择模式下打开 3D 视图 N 侧栏中的 **Weight Tool** 标签。

- 查看当前选择涉及的所有非零顶点组。
- 单选时查看顶点权重，多选时查看平均权重。
- 为所有所选顶点设置权重、从组中移除，或加入新顶点组。
- 使用替换、相加、相减、相乘、最大值、最小值或平均值混合两个顶点组。
- 在所选的左右镜像顶点对之间镜像一个或多个顶点组，支持对应的 `.L` 和 `.R` 组名。
- 沿相连网格顶点平滑一个组的权重，可调整强度、迭代次数、未选中邻居是否参与以及是否按距离加权。
- 将每个所选顶点的组权重归一化；无法处理的顶点会被跳过并计数提示。

顶点组列表支持滚动和搜索，所有编辑操作均支持 Blender 撤销。

## 构建

在仓库根目录使用 Blender 4.2 或更高版本：

```powershell
blender --command extension build `
  --source-dir addon\weight_tool `
  --output-dir .

blender --command extension validate weight_tool-2.1.0.zip
```

运行集成测试：

```powershell
blender --background --factory-startup --python tests\test_addon.py
```
