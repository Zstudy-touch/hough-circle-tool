"""启动入口。

用法：
    python run.py                     # 空白启动，界面里再导入图片
    python run.py examples/coins.jpg  # 直接打开指定图片
"""

import sys
from pathlib import Path

# 源码放在 src/ 下，直接运行时把 src 加进搜索路径，省去打包安装
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from hough_tool.gui import main  # noqa: E402  (必须在 sys.path 调整之后导入)

if __name__ == "__main__":
    raise SystemExit(main())
