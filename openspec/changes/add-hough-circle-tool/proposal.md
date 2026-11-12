# Proposal

## Why

组里需要反复处理不同光照、不同半径的实拍图，仅靠背参数表很难调出可用的阈值组合；直接用一段 OpenCV 脚本又只能"改一次、跑一次、看图"，调整成本高。把"改参数—看效果—导出结果"放进一个窗口，可以显著缩短调参时间，并把确认过的参数固化成可复现的预设。

## What Changes

- 新增 tkinter 桌面界面：导入图片、六个参数滑块、实时预览、导出标注图，并内置两套参数预设。
- 新增无界面命令行通道，复用同一套检测与绘制逻辑，便于批量出图和自动比对。
- 检测参数收敛为可序列化的 `CircleParams`，界面、命令行与测试共用同一份默认值。
- 验收覆盖两张实拍图：`coins.jpg` 标出两个硬币外缘，`cookie-plate.jpg` 标出一个盘沿。

## Capabilities

### New Capabilities
- `hough-circle-tool`: 霍夫圆检测工具对外的完整行为——图片导入、参数调节、标注预览与导出、命令行批处理通道，以及两张样例图的验收口径。

### Modified Capabilities

（无，新仓库无既有能力）

## Impact

- 代码：新仓库，包含 `src/hough_tool/`（检测、绘制、界面、命令行）、`tests/`、`examples/`、`docs/results/`。
- 依赖：`opencv-python`、`numpy`、`Pillow`；`tkinter` 随官方 Python 提供，无需额外安装。
- 运行环境：Windows / macOS / Linux 桌面，Python 3.10 及以上；命令行通道可在无显示环境使用。
- 无既有调用方，不涉及兼容性迁移。
