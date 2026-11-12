# 项目约定

这是一个 Python + OpenCV 的霍夫圆检测小工具，界面基于 tkinter，源码在 `src/hough_tool/`。

## 运行与验证

- 启动界面：`python run.py`（可选参数是要打开的图片路径）
- 无界面检测：`PYTHONPATH=src python -m hough_tool.cli --image <图片> [--out <标注图>]`
- 测试：`python -m unittest discover -s tests -v`；改动检测逻辑后必须全部通过

## 约定

- 参数默认值只在 `detector.CircleParams` 定义一次，界面、命令行和测试都从这里取，不要各写一套。
- 界面只负责收集参数与展示；检测留在 `detector.py`，绘制留在 `annotate.py`，保证预览与导出结果一致。
- 两张验收样例图的参数同时存在于 README「验收参数与结果」、`gui.PRESETS` 和 `tests/test_detector.py`，改动时必须三处同步。
- 提交前确认 `openspec/changes/add-hough-circle-tool/tasks.md` 的勾选状态与实际进度一致。
