"""命令行入口：不打开界面也能跑一次检测，用于批量出图和自动化验收。

用法示例：
    python -m hough_tool.cli --image examples/coins.jpg --out out/coins.png \
        --min-dist 200 --param2 40 --min-radius 120 --max-radius 200
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import annotate as annotate_mod
from .detector import CircleParams, detect_circles, load_image


def build_parser() -> argparse.ArgumentParser:
    defaults = CircleParams()
    parser = argparse.ArgumentParser(
        prog="hough_tool.cli",
        description="对一张图片执行霍夫圆检测，并可选地导出一张标注图。",
    )
    parser.add_argument("--image", required=True, help="输入图片路径")
    parser.add_argument("--out", help="标注图输出路径；省略时只打印检测结果")
    parser.add_argument("--dp", type=float, default=defaults.dp, help="累加器分辨率比例，默认 1.2")
    parser.add_argument("--min-dist", type=int, default=defaults.min_dist, help="圆心最小间距，默认 200")
    parser.add_argument("--param1", type=int, default=defaults.param1, help="Canny 高阈值，默认 120")
    parser.add_argument("--param2", type=int, default=defaults.param2, help="圆心累加器阈值，默认 40")
    parser.add_argument("--min-radius", type=int, default=defaults.min_radius, help="最小半径，0 表示不限")
    parser.add_argument("--max-radius", type=int, default=defaults.max_radius, help="最大半径，0 表示不限")
    parser.add_argument("--blur-ksize", type=int, default=defaults.blur_ksize, help="高斯核大小，默认 9")
    parser.add_argument("--blur-sigma", type=float, default=defaults.blur_sigma, help="高斯标准差，默认 2.0")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果，便于脚本比对")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    params = CircleParams(
        dp=args.dp,
        min_dist=args.min_dist,
        param1=args.param1,
        param2=args.param2,
        min_radius=args.min_radius,
        max_radius=args.max_radius,
        blur_ksize=args.blur_ksize,
        blur_sigma=args.blur_sigma,
    )

    image = load_image(args.image)
    circles = detect_circles(image, params)

    if args.json:
        print(json.dumps(
            {
                "image": str(args.image),
                "count": len(circles),
                "circles": [c.as_dict() for c in circles],
                "params": params.as_dict(),
            },
            ensure_ascii=False,
        ))
    else:
        print(f"{args.image}: 检出 {len(circles)} 个圆")
        for index, circle in enumerate(circles, start=1):
            print(f"  #{index} x={circle.x} y={circle.y} r={circle.r}")

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        annotate_mod.save(annotate_mod.annotate(image, circles), str(out_path))
        if not args.json:
            print(f"标注图已写出：{out_path}")

    return 0 if circles else 1


if __name__ == "__main__":
    sys.exit(main())
