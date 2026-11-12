"""验收测试：用 README 中记录的两组参数跑样例图，核对检出数量与半径。

不依赖 pytest，直接运行：
    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))  # 源码在 src/ 下，测试自己负责把它加进路径

import numpy as np  # noqa: E402

from hough_tool import annotate  # noqa: E402
from hough_tool.detector import CircleParams, detect_circles, load_image  # noqa: E402

COINS_IMAGE = ROOT / "examples" / "coins.jpg"
PLATE_IMAGE = ROOT / "examples" / "cookie-plate.jpg"

# 与 README「验收参数」一节保持一致；改这里就要同步改文档和预期结果
COINS_PARAMS = CircleParams(min_dist=200, param1=120, param2=40, min_radius=140, max_radius=175)
PLATE_PARAMS = CircleParams(min_dist=200, param1=120, param2=40, min_radius=200, max_radius=280)


class CoinsAcceptanceTest(unittest.TestCase):
    """coins.jpg：应标出两枚硬币的外缘。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.image = load_image(str(COINS_IMAGE))
        cls.circles = detect_circles(cls.image, COINS_PARAMS)

    def test_finds_exactly_two_circles(self) -> None:
        self.assertEqual(2, len(self.circles), f"实际检出：{self.circles}")

    def test_radius_matches_coin_size(self) -> None:
        for circle in self.circles:
            self.assertGreaterEqual(circle.r, 140)
            self.assertLessEqual(circle.r, 175)

    def test_two_circles_are_located_left_and_right(self) -> None:
        # 两枚硬币左右分布，圆心横向距离应明显大于半径，避免检出同一个圆两次
        left, right = self.circles
        self.assertGreater(right.x - left.x, 300)
        self.assertAlmostEqual(left.y, right.y, delta=40)


class PlateAcceptanceTest(unittest.TestCase):
    """cookie-plate.jpg：应标出一个盘沿。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.image = load_image(str(PLATE_IMAGE))
        cls.circles = detect_circles(cls.image, PLATE_PARAMS)

    def test_finds_exactly_one_circle(self) -> None:
        self.assertEqual(1, len(self.circles), f"实际检出：{self.circles}")

    def test_radius_covers_the_plate_rim(self) -> None:
        circle = self.circles[0]
        self.assertGreaterEqual(circle.r, 200)
        self.assertLessEqual(circle.r, 280)

    def test_center_is_near_image_center(self) -> None:
        height, width = self.image.shape[:2]
        circle = self.circles[0]
        self.assertLess(abs(circle.x - width // 2), 40)
        self.assertLess(abs(circle.y - height // 2), 40)


class RobustnessTest(unittest.TestCase):
    """边界情况：纯色图不应报错，绘制不应修改原图。"""

    def test_blank_image_returns_empty_list(self) -> None:
        blank = np.full((240, 320, 3), 255, dtype=np.uint8)
        self.assertEqual([], detect_circles(blank, CircleParams()))

    def test_annotate_keeps_source_image_untouched(self) -> None:
        image = load_image(str(COINS_IMAGE))
        before = image.copy()
        annotate.annotate(image, detect_circles(image, COINS_PARAMS))
        self.assertTrue(np.array_equal(before, image), "annotate 不应修改传入的原图")

    def test_annotate_draws_circles(self) -> None:
        image = np.full((200, 200, 3), 0, dtype=np.uint8)
        from hough_tool.detector import Circle

        result = annotate.annotate(image, [Circle(x=100, y=100, r=60)])
        # 绿色通道出现亮像素就说明圆确实画上去了
        self.assertGreater(int((result[:, :, 1] > 200).sum()), 100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
