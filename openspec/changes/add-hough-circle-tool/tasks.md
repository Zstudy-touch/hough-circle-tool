# Tasks

## 1. 规格确认与项目骨架

- [x] 1.1 用 `python -m hough_tool.cli` 在两张样例图上试跑，确认"coins 2 个圆、plate 1 个圆"的半径区间（140–175 / 200–280）并写入 spec 的可验收场景
- [x] 1.2 建立 `run.py`、`src/hough_tool/`、`tests/`、`examples/`、`docs/results/` 结构，运行 `python -c "import hough_tool"` 确认包可导入

## 2. 检测与绘制

- [x] 2.1 实现 `CircleParams`、`preprocess`、`detect_circles`，用 `python -m hough_tool.cli --image examples/coins.jpg` 验证能检出 2 个圆
- [x] 2.2 实现 `annotate` 与 `save`，用 `tests/test_detector.py` 的 `test_annotate_keeps_source_image_untouched`、`test_annotate_draws_circles` 验证不修改原图且确实画上圆环

## 3. 图形界面

- [x] 3.1 实现 tkinter 界面：导入图片、六个参数滑块、实时预览、导出标注图、两套预设；用脚本构造窗口并套用预设，确认硬币 2 个圆（r=179、180）、盘子 1 个圆（r=243）
- [x] 3.2 处理非法参数与坏图片路径：滑块初值取自 `CircleParams` 默认值，检测失败时状态栏提示而不是抛异常；重新构造窗口确认无 traceback

## 4. 命令行与文档

- [x] 4.1 实现 `cli.py`（`--json`、`--out`、全套参数），运行 `--json` 确认输出 `count=2` 并成功写出标注图
- [x] 4.2 编写 README：依赖安装、启动方式、参数说明表、两张图的验收参数与结果图；用 `docs/results/*.png` 的实际路径核对图片可显示

## 5. 验收

- [x] 5.1 运行 `python -m unittest discover -s tests -v`，9 条用例全部通过（含两张样例图的数量、半径、圆心位置断言）
- [x] 5.2 生成 `docs/results/coins-annotated.png` 与 `docs/results/cookie-plate-annotated.png`，逐张核对：硬币图两个圆贴合外缘（齿轮边），盘子图一个圆贴合盘沿；放大四角复核后修正了首版「硬币锁内圈、盘子圆心偏左上」的偏差
- [x] 5.3 运行 `openspec validate add-hough-circle-tool --strict`，确认变更记录合法

## Workflow follow-up

- 评审通过后归档该变更，把 `specs/hough-circle-tool/spec.md` 合入 `openspec/specs/`。
