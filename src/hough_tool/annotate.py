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


def annotate(
    image: np.ndarray,
    circles: list[Circle],
    color: tuple[int, int, int] = CIRCLE_COLOR,
    thickness: int = 3,
) -> np.ndarray:
    """返回画好圆的结果副本，不修改传入的原图。"""
    canvas = image.copy()
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
            (circle.x - 30, circle.y - circle.r - 8 if circle.y - circle.r - 8 > 12 else circle.y + circle.r + 20),
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
