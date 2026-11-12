# Spec Delta

## Purpose

为霍夫圆检测提供一个可直接调参的桌面工具：导入实拍图后调整 HoughCircles 参数，实时看到检出的圆，并把标注结果导出为图片；同一套参数也能在命令行原样复现。

## ADDED Requirements

### Requirement: 导入图片并自动检测

工具 SHALL 支持导入 `jpg`、`jpeg`、`png`、`bmp` 图片，导入成功后 MUST 立即用当前参数执行一次检测并显示结果。

#### Scenario: 导入样例图

- **WHEN** 用户在界面选择 `examples/coins.jpg`
- **THEN** 画布显示该图的标注预览，状态栏给出检出数量与各圆半径

#### Scenario: 图片无法读取

- **WHEN** 启动时传入的图片路径不存在或不是有效图片
- **THEN** 界面给出错误提示并保持可操作，不崩溃退出

### Requirement: 参数调节即时生效

界面 SHALL 提供 `dp`、`minDist`、`param1`、`param2`、最小半径、最大半径六个可调参数；参数变化后 MUST 自动重新检测并刷新预览，无需再点任何按钮。

#### Scenario: 拖动阈值滑块

- **WHEN** 用户拖动 `param2` 滑块后停下
- **THEN** 预览与状态栏自动更新为按新 `param2` 得到的检出结果，滑块数值本身保持为整数

#### Scenario: 套用参数预设

- **WHEN** 用户点击「硬币（coins.jpg）」或「盘子（cookie-plate.jpg）」预设
- **THEN** 六个滑块被设置为该预设值，并立即按新参数重新检测

### Requirement: 标注预览与导出保持一致

预览与导出 MUST 使用同一套绘制逻辑：绿色圆环标出圆周、红色十字标出圆心、圆环外侧标注半径数值；导出结果 MUST 为原图分辨率。

#### Scenario: 导出当前结果

- **WHEN** 用户在已有检出结果时点击「导出标注图」并确认保存路径
- **THEN** 该路径生成与预览一致的标注图片，尺寸与原图相同

#### Scenario: 绘制不修改原图

- **WHEN** 对同一张图连续执行多次检测与绘制
- **THEN** 内存中的原图数据保持不变，导出结果不出现叠加痕迹

### Requirement: 无界面命令行通道

工具 SHALL 提供命令行入口，接受与界面相同的检测参数，支持把标注图写到指定路径；输出 MUST 支持 `--json` 形式，未检出任何圆时退出码 MUST 为 1。

#### Scenario: 输出 JSON

- **WHEN** 运行 `python -m hough_tool.cli --image examples/coins.jpg --json`
- **THEN** 标准输出为包含 `count`、`circles`、`params` 的 JSON，`count` 与当前参数下的圆数量一致

#### Scenario: 未检出圆

- **WHEN** 用收窄到极端的半径范围检测样例图，结果为空
- **THEN** 程序打印 0 个圆并以退出码 1 结束

### Requirement: 两张样例图的验收结果

工具 MUST 能按文档记录的参数在两张样例图上得到指定结果：`coins.jpg` 检出 2 个圆且半径落在 140–175 像素；`cookie-plate.jpg` 检出 1 个圆且半径落在 200–280 像素。

#### Scenario: 硬币图标出两个外缘

- **WHEN** 以 `dp=1.2`、`minDist=200`、`param1=120`、`param2=40`、半径 140–175 检测 `examples/coins.jpg`
- **THEN** 恰好检出 2 个圆，左右分布且分别贴合两枚硬币外缘

#### Scenario: 盘子图标出一个盘沿

- **WHEN** 以 `dp=1.2`、`minDist=200`、`param1=120`、`param2=40`、半径 200–280 检测 `examples/cookie-plate.jpg`
- **THEN** 恰好检出 1 个圆，圆心接近图片中心并贴合盘沿

### Requirement: README 记录启动方式与验收参数

仓库 README MUST 写明依赖安装、启动命令、两张样例图各自的验收参数，并嵌入两张标注结果图。

#### Scenario: 照文档复现验收

- **WHEN** 新用户按 README 安装依赖并执行启动命令
- **THEN** 能打开界面，并按 README 的参数在两张样例图上复现记录的检出数量与半径
