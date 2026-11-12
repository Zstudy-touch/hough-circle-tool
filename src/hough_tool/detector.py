"""霍夫圆检测核心：把 OpenCV 的 `HoughCircles` 包装成可保存、可复现的参数对象。

界面、命令行和测试都只依赖这里的参数结构，避免三处各写一套默认值。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import cv2
import numpy as np


@dataclass
class CircleParams:
    """一次检测所用的全部参数，字段含义与 `cv2.HoughCircles` 对齐。"""

    dp: float = 1.2            # 累加器分辨率相对原图的比例，1.0~2.0
    min_dist: int = 200        # 两个圆心之间的最小距离，防止同一个圆被重复检出
    param1: int = 120          # Canny 边缘检测的高阈值（低阈值取它的一半）
    param2: int = 40           # 圆心累加器阈值，越大越严格、检出的圆越少
    min_radius: int = 0        # 最小半径，0 表示不限制
    max_radius: int = 0        # 最大半径，0 表示不限制
    blur_ksize: int = 9        # 预处理高斯核，必须是正奇数
    blur_sigma: float = 2.0    # 高斯核标准差

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Circle:
    """检出的一个圆，单位都是像素。"""

    x: int
    y: int
    r: int

    def as_dict(self) -> dict:
        return {"x": self.x, "y": self.y, "r": self.r}


def to_gray(image: np.ndarray) -> np.ndarray:
    """统一转成单通道灰度图；传进来的已经是灰度图时原样返回。"""
    if image.ndim == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def preprocess(image: np.ndarray, params: CircleParams) -> np.ndarray:
    """灰度化 + 高斯模糊。

    模糊是必要的：实拍图的纹理和噪点会在 Canny 阶段产生大量短边缘，
    不先平滑会在累加器里形成假圆。
    """
    gray = to_gray(image)
    k = params.blur_ksize
    if k >= 3:  # 核太小时 OpenCV 会退化成不平滑，这里显式挡掉非法值
        k = k if k % 2 == 1 else k + 1
        gray = cv2.GaussianBlur(gray, (k, k), params.blur_sigma)
    return gray


def detect_circles(image: np.ndarray, params: CircleParams) -> list[Circle]:
    """在图像上检测圆，返回按 x 坐标排序的结果，便于结果稳定比较。"""
    gray = preprocess(image, params)
    found = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=params.dp,
        minDist=params.min_dist,
        param1=params.param1,
        param2=params.param2,
        minRadius=params.min_radius,
        maxRadius=params.max_radius,
    )
    if found is None:
        return []
    # HoughCircles 返回 float32，四舍五入成整数像素后更易读、也便于写入日志
    circles = [Circle(int(round(x)), int(round(y)), int(round(r))) for x, y, r in found[0]]
    return sorted(circles, key=lambda c: (c.x, c.y))


def load_image(path: str) -> np.ndarray:
    """读图并检查是否成功；cv2.imread 读失败只会返回 None，不会抛异常。"""
    image = cv2.imread(path)
    if image is None:
        raise FileNotFoundError(f"无法读取图片：{path}")
    return image
