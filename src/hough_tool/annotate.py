"""把检测结果画到图上并导出。

界面预览和命令行导出共用这一份绘制逻辑，保证"预览看到什么、导出就是什么"。
"""

from __future__ import annotations

import cv2
import numpy as np

from .detector import Circle

# 绿色在硬币、盘子的暖色背景上对比度足够，也不需要额外配色
CIRCLE_COLOR = (0, 255, 0)
CENTER_COLOR = (0, 0, 255)


def _label_origin(circle: Circle, width: int, height: int) -> tuple[int, int]:
    """挑选半径文字的画点，避免被图片边缘裁掉。

    优先放在圆上方，其次圆下方；两者都超出画布时（大圆贴近上下边），
    退到圆心下方一点，宁可压在图案上也不让数字缺一半。
    """
    text_h = 22  # 0.6 字号的实际文字高度，留一点余量
    x = min(max(circle.x - 30, 4), max(width - 64, 4))
    above = circle.y - circle.r - 8
    below = circle.y + circle.r + 22
    if above >= text_h:
        return x, above
    if below <= height - 6:
        return x, below
    return x, min(circle.y + 34, height - 8)


def annotate(
    image: np.ndarray,
    circles: list[Circle],
    color: tuple[int, int, int] = CIRCLE_COLOR,
    thickness: int = 3,
) -> np.ndarray:
    """返回画好圆的结果副本，不修改传入的原图。"""
    canvas = image.copy()
    height, width = canvas.shape[:2]
    for circle in circles:
        cv2.circle(canvas, (circle.x, circle.y), circle.r, color, thickness)
        # 画一个十字标记圆心，方便核对圆心是否落在目标中心
        cv2.drawMarker(
            canvas,
            (circle.x, circle.y),
            CENTER_COLOR,
            markerType=cv2.MARKER_CROSS,
            markerSize=18,
            thickness=2,
        )
        # 半径标注用拉丁字符，避免 OpenCV 默认字体不支持中文
        cv2.putText(
            canvas,
            f"r={circle.r}",
            _label_origin(circle, width, height),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
            cv2.LINE_AA,
        )
    return canvas


def save(image: np.ndarray, path: str) -> None:
    """写文件并检查返回值，避免路径写错时静默失败。"""
    if not cv2.imwrite(path, image):
        raise OSError(f"保存图片失败：{path}")
