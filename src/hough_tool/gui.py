"""tkinter 图形界面：导入图片、调参、预览检测结果、导出标注图。

界面只做三件事——收集参数、调用 `detector`、把 `annotate` 的结果贴到画布上。
检测与绘制逻辑都不在这里复制一份，保证预览和导出结果一致。
"""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
from pathlib import Path

import cv2
from PIL import Image, ImageTk

from . import annotate as annotate_mod
from .detector import CircleParams, detect_circles, load_image

APP_TITLE = "霍夫圆检测工具"

# 两张验收样例图的参数：界面上一键套用，README 里也按这两个口径记录
PRESETS = {
    "硬币（coins.jpg）": dict(
        dp=1.2, min_dist=200, param1=120, param2=40, min_radius=140, max_radius=175
    ),
    "盘子（cookie-plate.jpg）": dict(
        dp=1.2, min_dist=200, param1=120, param2=40, min_radius=200, max_radius=280
    ),
}

SLIDER_SPECS = [
    # (字段名, 标签, 下限, 上限, 步长, 是否取整)
    ("dp", "dp 分辨率比例", 1.0, 3.0, 0.1, False),
    ("min_dist", "圆心最小间距", 10, 600, 5, True),
    ("param1", "param1 Canny 高阈值", 10, 300, 5, True),
    ("param2", "param2 累加器阈值", 5, 150, 1, True),
    ("min_radius", "最小半径", 0, 400, 5, True),
    ("max_radius", "最大半径（0=不限）", 0, 500, 5, True),
]

# 滑块初值取自数据类的默认值；如果直接给 0，OpenCV 会因为
# minDist/param1/param2 非正而抛 "arguments' values is out of range"
DEFAULTS = CircleParams()


class HoughApp:
    def __init__(self, root: tk.Tk, initial_image: str | None = None) -> None:
        self.root = root
        self.image = None            # 原始 BGR 图，用于检测与导出
        self.circles = []            # 最近一次检测结果
        self.image_path: Path | None = None
        self.display_scale = 1.0     # 显示缩放比例，只影响预览
        self.preview_photo = None    # 必须持有引用，否则 Tk 会回收图像
        self._pending_detect = None  # 滑块防抖用的 after id

        self.root.title(APP_TITLE)
        self.root.geometry("1180x780")
        self.root.minsize(900, 600)

        self._build_layout()
        self._set_controls_enabled(False)
        if initial_image:
            self.open_image(initial_image)

    # ---------------- 界面搭建 ----------------
    def _build_layout(self) -> None:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")

        self.canvas = tk.Canvas(self.root, bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda _event: self.render())

        panel = ttk.Frame(self.root, padding=12)
        panel.pack(side=tk.RIGHT, fill=tk.Y)
        panel.pack_propagate(False)
        panel.configure(width=340)

        title_font = tkfont.Font(size=13, weight="bold")
        ttk.Label(panel, text=APP_TITLE, font=title_font).pack(anchor="w", pady=(0, 8))

        buttons = ttk.Frame(panel)
        buttons.pack(fill=tk.X, pady=(0, 10))
        self.btn_open = ttk.Button(buttons, text="导入图片", command=self.choose_image)
        self.btn_open.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        self.btn_export = ttk.Button(buttons, text="导出标注图", command=self.export_image)
        self.btn_export.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(4, 0))

        ttk.Label(panel, text="参数预设").pack(anchor="w")
        preset_row = ttk.Frame(panel)
        preset_row.pack(fill=tk.X, pady=(2, 10))
        for index, (name, values) in enumerate(PRESETS.items()):
            ttk.Button(
                preset_row,
                text=name,
                command=lambda v=values: self.apply_preset(v),
            ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4) if index == 0 else (4, 0))

        ttk.Separator(panel).pack(fill=tk.X, pady=8)

        self.scale_vars: dict[str, tk.Variable] = {}
        self.scale_widgets: dict[str, ttk.Scale] = {}
        for field, label, low, high, step, is_int in SLIDER_SPECS:
            ttk.Label(panel, text=label).pack(anchor="w", pady=(6, 0))
            initial = getattr(DEFAULTS, field)
            var: tk.Variable = tk.IntVar(value=int(initial)) if is_int else tk.DoubleVar(value=float(initial))
            widget = ttk.Scale(
                panel,
                from_=low,
                to=high,
                orient=tk.HORIZONTAL,
                variable=var,
            )
            widget.pack(fill=tk.X)
            # 滑块内部只有浮点值，这里按字段需要把显示和取值都收敛成整数
            widget.configure(command=lambda _value, f=field: self.on_slider(f))
            self.scale_vars[field] = var
            self.scale_widgets[field] = widget

        ttk.Separator(panel).pack(fill=tk.X, pady=10)

        self.status_var = tk.StringVar(value="尚未导入图片")
        ttk.Label(panel, textvariable=self.status_var, wraplength=310, justify="left").pack(anchor="w")

        self.detail_var = tk.StringVar(value="")
        ttk.Label(panel, textvariable=self.detail_var, wraplength=310, justify="left",
                  foreground="#555555").pack(anchor="w", pady=(6, 0))

    def _set_controls_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.btn_export.configure(state=state)
        for widget in self.scale_widgets.values():
            widget.configure(state=state)

    # ---------------- 参数读取 ----------------
    def current_params(self) -> CircleParams:
        values = {}
        for field, _label, low, _high, _step, is_int in SLIDER_SPECS:
            raw = self.scale_vars[field].get()
            value = int(round(float(raw))) if is_int else round(float(raw), 2)
            # OpenCV 要求 dp、minDist、param1、param2 必须是正数，这里兜底夹紧
            if field in ("min_dist", "param1", "param2"):
                value = max(1, value)
            values[field] = value
        return CircleParams(**values)

    def apply_preset(self, values: dict) -> None:
        for field, value in values.items():
            self.scale_vars[field].set(value)
        # 预设直接改的是变量，不会触发 Scale 的回调，手动安排一次检测
        self.schedule_detect(delay=0)

    def on_slider(self, field: str) -> None:
        """整数型滑块需要把值吸附到整数，否则 39.999 会显示成 39。"""
        var = self.scale_vars[field]
        var.set(int(round(float(var.get()))))
        self.schedule_detect()

    # ---------------- 检测与预览 ----------------
    def schedule_detect(self, delay: int = 150) -> None:
        """滑块拖动会连续触发，这里做防抖，停手后再算一次。"""
        if self.image is None:
            return
        if self._pending_detect is not None:
            self.root.after_cancel(self._pending_detect)
        self._pending_detect = self.root.after(delay, self.detect)

    def detect(self) -> None:
        self._pending_detect = None
        if self.image is None:
            return
        params = self.current_params()
        try:
            self.circles = detect_circles(self.image, params)
        except cv2.error as exc:
            # 极端参数组合会让 OpenCV 直接报错，界面上给提示而不是让窗口崩掉
            self.circles = []
            self.status_var.set("参数组合无效，请调整后重试")
            self.detail_var.set(str(exc).splitlines()[0][:200])
            self.render()
            return
        if self.circles:
            radii = "、".join(str(c.r) for c in self.circles)
            self.status_var.set(f"检出 {len(self.circles)} 个圆，半径：{radii}")
        else:
            self.status_var.set("未检出圆，试着降低 param2 或放宽半径范围")
        self.detail_var.set(
            f"dp={params.dp} minDist={params.min_dist} param1={params.param1} "
            f"param2={params.param2} 半径={params.min_radius}~{params.max_radius or '不限'}"
        )
        self.render()

    def render(self) -> None:
        if self.image is None:
            return
        canvas_w = max(self.canvas.winfo_width(), 1)
        canvas_h = max(self.canvas.winfo_height(), 1)
        height, width = self.image.shape[:2]
        # 等比缩放，保证整图可见且不拉伸
        self.display_scale = min(canvas_w / width, canvas_h / height, 1.0)
        annotated = annotate_mod.annotate(self.image, self.circles)
        rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb)
        if self.display_scale < 1.0:
            new_size = (max(int(width * self.display_scale), 1), max(int(height * self.display_scale), 1))
            pil_image = pil_image.resize(new_size, Image.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(pil_image)
        self.canvas.delete("all")
        self.canvas.create_image(canvas_w // 2, canvas_h // 2, image=self.preview_photo, anchor=tk.CENTER)

    # ---------------- 文件操作 ----------------
    def choose_image(self) -> None:
        path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片", "*.jpg *.jpeg *.png *.bmp"), ("全部文件", "*.*")],
        )
        if path:
            self.open_image(path)

    def open_image(self, path: str) -> None:
        try:
            image = load_image(path)
        except (FileNotFoundError, OSError) as exc:
            messagebox.showerror("无法打开图片", str(exc))
            return
        self.image = image
        self.image_path = Path(path)
        self._set_controls_enabled(True)
        # 换图后半径上限跟着图尺寸变化，避免沿用上一张图的量级
        max_side = max(image.shape[:2]) // 2
        for field in ("min_radius", "max_radius"):
            self.scale_widgets[field].configure(to=max(max_side, 50))
        self.root.title(f"{APP_TITLE} - {self.image_path.name}")
        self.schedule_detect(delay=0)

    def export_image(self) -> None:
        if self.image is None:
            return
        default_name = f"{self.image_path.stem if self.image_path else 'result'}-annotated.png"
        path = filedialog.asksaveasfilename(
            title="导出标注图",
            defaultextension=".png",
            initialfile=default_name,
            filetypes=[("PNG 图片", "*.png"), ("JPEG 图片", "*.jpg")],
        )
        if not path:
            return
        try:
            annotate_mod.save(annotate_mod.annotate(self.image, self.circles), path)
        except OSError as exc:
            messagebox.showerror("导出失败", str(exc))
            return
        messagebox.showinfo("导出成功", f"已保存到：\n{path}")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    initial = argv[0] if argv else None
    root = tk.Tk()
    HoughApp(root, initial_image=initial)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
