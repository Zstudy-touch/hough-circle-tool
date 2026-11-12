"""支持 `python -m hough_tool` 直接启动界面。"""

import sys

from .gui import main

if __name__ == "__main__":
    raise SystemExit(main())
