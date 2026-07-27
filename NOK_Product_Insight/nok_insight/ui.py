from __future__ import annotations

import math
import queue
import shutil
import sys
import tempfile
import threading
import time
import tkinter as tk
import uuid
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import pandas as pd

from .config import AnalysisConfig
from .exporter import export_analysis
from .loader import load_excel
from .metrics import AnalysisResult, METRIC_DEFINITIONS, analyze


PALETTE = {
    "ink": "#14283D",
    "ink_soft": "#274057",
    "paper": "#F4F7F5",
    "surface": "#FFFFFF",
    "line": "#D8E0E5",
    "muted": "#657482",
    "teal": "#0F766E",
    "teal_light": "#DDF3EF",
    "amber": "#D97706",
    "amber_light": "#FEF1D6",
    "red": "#C94C4C",
    "red_light": "#FBE3E3",
    "blue": "#3E7199",
    "blue_light": "#E3EEF5",
}

FONT_BODY = ("Microsoft YaHei UI", 10)
FONT_SMALL = ("Microsoft YaHei UI", 9)
FONT_TITLE = ("Microsoft YaHei UI", 20, "bold")
FONT_SECTION = ("Microsoft YaHei UI", 13, "bold")
FONT_NUMBER = ("Bahnschrift SemiBold", 21)


def _format_number(value: object, decimals: int = 0) -> str:
    if value is None or pd.isna(value):
        return "—"
    number = float(value)
    return f"{number:,.{decimals}f}"


def _format_percent(value: object) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):+.1%}"


PERCENT_METRICS = {"销售贡献率", "近3个月增长率", "断货率", "销售占比", "库存占比"}
ONE_DECIMAL_METRICS = {
    "月均销售金额(万元)",
    "月均销量",
    "近3个月均量",
    "前3个月均量",
    "需求波动系数",
    "可用量可销月数",
    "合计可销月数",
    "目标可销月数",
    "库存覆盖缺口",
    "销售库存错配指数",
    "客户复购频次",
    "采购覆盖月数",
    "参考售价",
}
INTEGER_METRICS = {
    "总销售数量",
    "总在库数量",
    "总可用量",
    "合计未完成",
    "理论补货量",
    "最低补货量",
    "建议采购量",
    "超储数量",
    "缺口参考销售额",
    "超储参考销售额",
    "购买客户数",
    "购买次数",
    "断货次数",
    "当月采购数量",
    "经营优先分",
}


def _format_metric(column: str, value: object) -> str:
    if value is None or pd.isna(value):
        return "—"
    if column in PERCENT_METRICS:
        return _format_percent(value)
    if column in ONE_DECIMAL_METRICS:
        return _format_number(value, 1)
    if column in INTEGER_METRICS:
        return _format_number(value, 0)
    return str(value)


class KpiCard(tk.Frame):
    def __init__(self, master, title: str, accent: str, **kwargs):
        super().__init__(
            master,
            bg=PALETTE["surface"],
            highlightthickness=1,
            highlightbackground=PALETTE["line"],
            padx=16,
            pady=12,
            **kwargs,
        )
        self.accent = tk.Frame(self, bg=accent, width=5)
        self.accent.pack(side="left", fill="y", padx=(0, 12))
        body = tk.Frame(self, bg=PALETTE["surface"])
        body.pack(side="left", fill="both", expand=True)
        self.title_label = tk.Label(
            body, text=title, bg=PALETTE["surface"], fg=PALETTE["muted"], font=FONT_SMALL
        )
        self.title_label.pack(anchor="w")
        self.value_label = tk.Label(
            body, text="—", bg=PALETTE["surface"], fg=PALETTE["ink"], font=FONT_NUMBER
        )
        self.value_label.pack(anchor="w", pady=(2, 0))
        self.note_label = tk.Label(
            body, text="", bg=PALETTE["surface"], fg=PALETTE["muted"], font=("Microsoft YaHei UI", 8)
        )
        self.note_label.pack(anchor="w")

    def set(self, value: str, note: str = "") -> None:
        self.value_label.configure(text=value)
        self.note_label.configure(text=note)


class BarChart(tk.Canvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, bg=PALETTE["surface"], highlightthickness=0, **kwargs)
        self.items: list[tuple[str, float]] = []
        self.bind("<Configure>", lambda _event: self.redraw())

    def set_data(self, items: list[tuple[str, float]]) -> None:
        self.items = items
        self.redraw()

    def redraw(self) -> None:
        self.delete("all")
        width = max(self.winfo_width(), 480)
        height = max(self.winfo_height(), 260)
        if not self.items:
            self.create_text(
                width / 2,
                height / 2,
                text="导入 Excel 后显示销售贡献排名",
                fill=PALETTE["muted"],
                font=FONT_BODY,
            )
            return
        left, right, top, bottom = 125, 30, 20, 20
        chart_width = max(100, width - left - right)
        row_height = (height - top - bottom) / len(self.items)
        maximum = max(value for _, value in self.items) or 1
        for index, (label, value) in enumerate(self.items):
            y = top + index * row_height
            bar_height = max(8, row_height * 0.54)
            bar_width = chart_width * value / maximum
            self.create_text(
                left - 10,
                y + bar_height / 2,
                text=label[:16],
                anchor="e",
                fill=PALETTE["ink_soft"],
                font=FONT_SMALL,
            )
            self.create_rectangle(
                left,
                y,
                left + chart_width,
                y + bar_height,
                fill=PALETTE["paper"],
                outline="",
            )
            self.create_rectangle(
                left,
                y,
                left + max(bar_width, 2),
                y + bar_height,
                fill=PALETTE["teal"] if index < 3 else PALETTE["blue"],
                outline="",
            )
            self.create_text(
                min(left + bar_width + 8, width - right),
                y + bar_height / 2,
                text=f"{value:,.1f}",
                anchor="w" if left + bar_width + 45 < width else "e",
                fill=PALETTE["ink"],
                font=("Bahnschrift", 9, "bold"),
            )


class DonutChart(tk.Canvas):
    COLORS = [
        PALETTE["teal"],
        PALETTE["amber"],
        PALETTE["red"],
        PALETTE["blue"],
        PALETTE["ink_soft"],
        "#8C6BB1",
        "#6F8A63",
    ]

    def __init__(self, master, **kwargs):
        super().__init__(master, bg=PALETTE["surface"], highlightthickness=0, **kwargs)
        self.items: list[tuple[str, int]] = []
        self.bind("<Configure>", lambda _event: self.redraw())

    def set_data(self, items: list[tuple[str, int]]) -> None:
        self.items = items
        self.redraw()

    def redraw(self) -> None:
        self.delete("all")
        width = max(self.winfo_width(), 360)
        height = max(self.winfo_height(), 260)
        total = sum(value for _, value in self.items)
        if total <= 0:
            self.create_text(
                width / 2,
                height / 2,
                text="导入 Excel 后显示产品分层",
                fill=PALETTE["muted"],
                font=FONT_BODY,
            )
            return
        size = min(height - 48, width * 0.46)
        x0, y0 = 24, (height - size) / 2
        start = 90
        for index, (_, value) in enumerate(self.items):
            extent = -360 * value / total
            self.create_arc(
                x0,
                y0,
                x0 + size,
                y0 + size,
                start=start,
                extent=extent,
                fill=self.COLORS[index % len(self.COLORS)],
                outline=PALETTE["surface"],
                width=2,
            )
            start += extent
        inset = size * 0.29
        self.create_oval(
            x0 + inset,
            y0 + inset,
            x0 + size - inset,
            y0 + size - inset,
            fill=PALETTE["surface"],
            outline="",
        )
        self.create_text(
            x0 + size / 2,
            y0 + size / 2 - 8,
            text=str(total),
            fill=PALETTE["ink"],
            font=("Bahnschrift SemiBold", 22),
        )
        self.create_text(
            x0 + size / 2,
            y0 + size / 2 + 14,
            text="产品",
            fill=PALETTE["muted"],
            font=FONT_SMALL,
        )
        legend_x = x0 + size + 28
        for index, (label, value) in enumerate(self.items):
            y = 34 + index * 27
            color = self.COLORS[index % len(self.COLORS)]
            self.create_rectangle(legend_x, y, legend_x + 10, y + 10, fill=color, outline="")
            self.create_text(
                legend_x + 18,
                y + 5,
                text=f"{label}  {value}",
                anchor="w",
                fill=PALETTE["ink_soft"],
                font=FONT_SMALL,
            )


class CoverageGauge(tk.Canvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, bg=PALETTE["surface"], highlightthickness=0, **kwargs)
        self.current: float | None = None
        self.target: float | None = None
        self.label = ""
        self.bind("<Configure>", lambda _event: self.redraw())

    def set_value(self, label: str, current: float | None, target: float | None) -> None:
        self.label = label
        self.current = current
        self.target = target
        self.redraw()

    def redraw(self) -> None:
        self.delete("all")
        width = max(self.winfo_width(), 400)
        height = max(self.winfo_height(), 105)
        if self.current is None or self.target is None or pd.isna(self.current) or pd.isna(self.target):
            self.create_text(
                18, height / 2, text="选择产品后显示库存水位", anchor="w", fill=PALETTE["muted"], font=FONT_BODY
            )
            return
        target = max(float(self.target), 0.1)
        current = max(float(self.current), 0)
        maximum = max(target * 2.2, current * 1.1, 1)
        left, right, y = 20, 24, 54
        track_width = width - left - right
        self.create_text(left, 18, text=self.label, anchor="w", fill=PALETTE["ink"], font=FONT_SECTION)
        self.create_rectangle(left, y, left + track_width, y + 16, fill=PALETTE["paper"], outline="")
        target_x = left + track_width * target / maximum
        current_x = left + track_width * min(current, maximum) / maximum
        fill = PALETTE["red"] if current < target else PALETTE["amber"] if current > target * 2 else PALETTE["teal"]
        self.create_rectangle(left, y, current_x, y + 16, fill=fill, outline="")
        self.create_line(target_x, y - 8, target_x, y + 24, fill=PALETTE["ink"], width=2)
        self.create_text(
            target_x,
            y + 34,
            text=f"目标 {target:.1f}月",
            fill=PALETTE["muted"],
            font=("Microsoft YaHei UI", 8),
        )
        self.create_text(
            min(current_x, width - right),
            y - 12,
            text=f"当前 {current:.1f}月",
            fill=fill,
            font=("Bahnschrift", 10, "bold"),
        )


class DashboardTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=PALETTE["paper"])
        self.cards: dict[str, KpiCard] = {}
        cards_frame = tk.Frame(self, bg=PALETTE["paper"])
        cards_frame.pack(fill="x", padx=22, pady=(20, 12))
        card_specs = [
            ("产品数", PALETTE["blue"]),
            ("月均销售额", PALETTE["teal"]),
            ("目标以下", PALETTE["amber"]),
            ("高库存", PALETTE["red"]),
            ("历史断货", PALETTE["ink_soft"]),
        ]
        for column, (title, color) in enumerate(card_specs):
            cards_frame.grid_columnconfigure(column, weight=1, uniform="card")
            card = KpiCard(cards_frame, title, color)
            card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 5, 0 if column == 4 else 5))
            self.cards[title] = card

        charts = tk.Frame(self, bg=PALETTE["paper"])
        charts.pack(fill="both", expand=True, padx=22, pady=8)
        charts.grid_columnconfigure(0, weight=3)
        charts.grid_columnconfigure(1, weight=2)
        charts.grid_rowconfigure(0, weight=1)
        sales_panel = self._panel(charts, "销售贡献前10", "单位：表内月均销售金额（万元）")
        sales_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        self.bar_chart = BarChart(sales_panel, height=320)
        self.bar_chart.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        category_panel = self._panel(charts, "产品经营分层", "按库存水位、趋势与销售贡献自动判断")
        category_panel.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        self.donut_chart = DonutChart(category_panel, height=320)
        self.donut_chart.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        gauge_panel = self._panel(self, "库存水位轨", "点击产品清单中的任意产品，查看当前覆盖月数与目标差距")
        gauge_panel.pack(fill="x", padx=22, pady=(4, 20))
        self.gauge = CoverageGauge(gauge_panel, height=108)
        self.gauge.pack(fill="x", padx=12, pady=(0, 10))

    def _panel(self, master, title: str, subtitle: str) -> tk.Frame:
        panel = tk.Frame(
            master,
            bg=PALETTE["surface"],
            highlightbackground=PALETTE["line"],
            highlightthickness=1,
        )
        heading = tk.Frame(panel, bg=PALETTE["surface"])
        heading.pack(fill="x", padx=16, pady=(14, 8))
        tk.Label(heading, text=title, bg=PALETTE["surface"], fg=PALETTE["ink"], font=FONT_SECTION).pack(anchor="w")
        tk.Label(heading, text=subtitle, bg=PALETTE["surface"], fg=PALETTE["muted"], font=FONT_SMALL).pack(anchor="w")
        return panel

    def update_result(self, result: AnalysisResult) -> None:
        summary = result.summary
        self.cards["产品数"].set(str(summary["产品数"]), "已成功解析")
        self.cards["月均销售额"].set(
            _format_number(summary["月均销售金额合计(万元)"], 1),
            "万元｜按原表口径",
        )
        self.cards["目标以下"].set(str(summary["目标以下产品数"]), "需要核对补货")
        self.cards["高库存"].set(str(summary["高库存产品数"]), "超过目标水位2倍")
        self.cards["历史断货"].set(str(summary["历史断货产品数"]), "统计期内发生过断货")

        top = result.products.nlargest(10, "月均销售金额(万元)")
        self.bar_chart.set_data(
            [
                (f"{row['品号']} {row['品名']}".strip(), float(row["月均销售金额(万元)"]))
                for _, row in top.iterrows()
            ]
        )
        counts = result.products["产品分层"].value_counts()
        self.donut_chart.set_data([(str(label), int(value)) for label, value in counts.items()])


class ProductTab(tk.Frame):
    VIEW_COLUMNS = {
        "经营核心": [
            "品号", "品名", "产品分层", "经营优先分", "ABC分类", "月均销售金额(万元)",
            "销售贡献率", "近3个月增长率", "合计可销月数", "目标可销月数",
            "建议采购量", "建议动作",
        ],
        "销售趋势": [
            "品号", "品名", "类型", "规格", "总销售数量", "月均销量", "近3个月均量",
            "前3个月均量", "近3个月增长率", "需求波动系数", "月均销售金额(万元)",
            "销售贡献率", "ABC分类", "购买客户数", "客户复购频次",
        ],
        "库存采购": [
            "品号", "品名", "总在库数量", "总可用量", "合计未完成", "可用量可销月数",
            "合计可销月数", "目标可销月数", "库存覆盖缺口", "销售库存错配指数",
            "理论补货量", "最低补货量", "建议采购量", "当月采购数量", "采购覆盖月数",
            "缺口参考销售额", "超储参考销售额",
        ],
        "客户风险": [
            "品号", "品名", "产品分层", "经营优先分", "购买客户数", "购买次数",
            "客户复购频次", "断货次数", "断货率", "近3个月增长率",
            "可用量可销月数", "库存覆盖缺口", "建议动作",
        ],
    }
    VIEW_COLUMNS["全部指标"] = list(
        dict.fromkeys(column for columns in VIEW_COLUMNS.values() for column in columns)
    )
    WIDTHS = {
        "品号": 95, "品名": 130, "类型": 90, "规格": 110, "产品分层": 118,
        "建议动作": 350, "月均销售金额(万元)": 135, "近3个月增长率": 110,
        "销售库存错配指数": 125, "缺口参考销售额": 120, "超储参考销售额": 120,
    }

    def __init__(self, master, on_select, on_open=None):
        super().__init__(master, bg=PALETTE["paper"])
        self.result: AnalysisResult | None = None
        self.filtered = pd.DataFrame()
        self.on_select = on_select
        self.on_open = on_open
        self.sort_reverse: dict[str, bool] = {}

        title_row = tk.Frame(self, bg=PALETTE["paper"])
        title_row.pack(fill="x", padx=22, pady=(16, 4))
        tk.Label(
            title_row, text="产品全景清单", bg=PALETTE["paper"], fg=PALETTE["ink"],
            font=FONT_SECTION,
        ).pack(side="left")
        tk.Label(
            title_row, text="双击任一行进入产品详情", bg=PALETTE["paper"],
            fg=PALETTE["teal"], font=FONT_SMALL,
        ).pack(side="left", padx=12)
        self.count_label = tk.Label(
            title_row, text="0 个产品", bg=PALETTE["paper"],
            fg=PALETTE["muted"], font=FONT_SMALL,
        )
        self.count_label.pack(side="right")

        filters = tk.Frame(self, bg=PALETTE["paper"])
        filters.pack(fill="x", padx=22, pady=(4, 10))
        tk.Label(filters, text="搜索", bg=PALETTE["paper"], fg=PALETTE["muted"], font=FONT_SMALL).pack(side="left")
        self.search_var = tk.StringVar()
        search = ttk.Entry(filters, textvariable=self.search_var, width=24)
        search.pack(side="left", padx=(7, 15))
        search.bind("<KeyRelease>", lambda _event: self.apply_filter())

        tk.Label(filters, text="产品分层", bg=PALETTE["paper"], fg=PALETTE["muted"], font=FONT_SMALL).pack(side="left")
        self.category_var = tk.StringVar(value="全部")
        self.category = ttk.Combobox(filters, textvariable=self.category_var, state="readonly", width=15)
        self.category["values"] = ("全部",)
        self.category.pack(side="left", padx=(7, 15))
        self.category.bind("<<ComboboxSelected>>", lambda _event: self.apply_filter())

        tk.Label(filters, text="指标视图", bg=PALETTE["paper"], fg=PALETTE["muted"], font=FONT_SMALL).pack(side="left")
        self.view_var = tk.StringVar(value="经营核心")
        self.view = ttk.Combobox(
            filters, textvariable=self.view_var, state="readonly", width=12,
            values=tuple(self.VIEW_COLUMNS),
        )
        self.view.pack(side="left", padx=(7, 15))
        self.view.bind("<<ComboboxSelected>>", lambda _event: self._change_view())

        self.high_priority_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            filters, text="只看高优先级（≥70）", variable=self.high_priority_var,
            command=self.apply_filter, bg=PALETTE["paper"], fg=PALETTE["ink_soft"],
            activebackground=PALETTE["paper"], selectcolor=PALETTE["surface"], font=FONT_SMALL,
        ).pack(side="left")

        container = tk.Frame(
            self, bg=PALETTE["surface"], highlightbackground=PALETTE["line"],
            highlightthickness=1,
        )
        container.pack(fill="both", expand=True, padx=22, pady=(0, 20))
        self.tree = ttk.Treeview(container, show="headings", selectmode="browse")
        y_scroll = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self._selected)
        self.tree.bind("<Double-1>", self._open_selected)
        self.tree.tag_configure("risk", background=PALETTE["red_light"])
        self.tree.tag_configure("opportunity", background=PALETTE["amber_light"])
        self.tree.tag_configure("healthy", background=PALETTE["teal_light"])
        self._configure_columns()

    def _configure_columns(self) -> None:
        columns = self.VIEW_COLUMNS[self.view_var.get()]
        self.tree.configure(columns=columns)
        for name in columns:
            width = self.WIDTHS.get(name, 100)
            self.tree.heading(name, text=name, command=lambda key=name: self.sort_by(key))
            self.tree.column(name, width=width, minwidth=70, stretch=name == "建议动作")

    def _change_view(self) -> None:
        self._configure_columns()
        self._render()

    def update_result(self, result: AnalysisResult) -> None:
        self.result = result
        categories = ["全部"] + sorted(result.products["产品分层"].dropna().astype(str).unique().tolist())
        self.category["values"] = categories
        self.category_var.set("全部")
        self.search_var.set("")
        self.high_priority_var.set(False)
        self.apply_filter()

    def apply_filter(self) -> None:
        if self.result is None:
            return
        frame = self.result.products.copy()
        category = self.category_var.get()
        if category and category != "全部":
            frame = frame[frame["产品分层"] == category]
        if self.high_priority_var.get():
            frame = frame[frame["经营优先分"] >= 70]
        query = self.search_var.get().strip().lower()
        if query:
            searchable = (
                frame["品号"].astype(str) + " " + frame["品名"].astype(str)
                + " " + frame["类型"].astype(str) + " " + frame["规格"].astype(str)
            )
            frame = frame[searchable.str.lower().str.contains(query, regex=False)]
        self.filtered = frame
        self._render()

    def sort_by(self, column: str) -> None:
        if self.filtered.empty:
            return
        reverse = not self.sort_reverse.get(column, False)
        self.sort_reverse[column] = reverse
        self.filtered = self.filtered.sort_values(column, ascending=not reverse, na_position="last")
        self._render()

    def _render(self) -> None:
        self.tree.delete(*self.tree.get_children())
        columns = self.VIEW_COLUMNS[self.view_var.get()]
        for index, row in self.filtered.iterrows():
            values = [_format_metric(column, row.get(column)) for column in columns]
            category = row["产品分层"]
            tag = (
                "risk" if category in ("衰退观察品", "数据不足")
                else "opportunity" if category in ("高库存促销品", "补货关注品")
                else "healthy"
            )
            self.tree.insert("", "end", iid=str(index), values=values, tags=(tag,))
        self.count_label.configure(text=f"{len(self.filtered)} 个产品")

    def _current_row(self) -> pd.Series | None:
        selection = self.tree.selection()
        if not selection or self.filtered.empty:
            return None
        index = int(selection[0])
        if index not in self.filtered.index:
            return None
        return self.filtered.loc[index]

    def _selected(self, _event=None) -> None:
        row = self._current_row()
        if row is not None:
            self.on_select(row)

    def _open_selected(self, _event=None) -> None:
        row = self._current_row()
        if row is not None and self.on_open:
            self.on_open(row)


class TrendChart(tk.Canvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, bg=PALETTE["surface"], highlightthickness=0, **kwargs)
        self.labels: list[str] = []
        self.values: list[float] = []
        self.bind("<Configure>", lambda _event: self.redraw())

    def set_data(self, labels: list[str], values: list[float]) -> None:
        self.labels = labels
        self.values = values
        self.redraw()

    def redraw(self) -> None:
        self.delete("all")
        measured_width = self.winfo_width()
        measured_height = self.winfo_height()
        width = measured_width if measured_width > 100 else 600
        height = measured_height if measured_height > 100 else 240
        if not self.values:
            self.create_text(
                width / 2, height / 2, text="原表未识别到月度销量序列",
                fill=PALETTE["muted"], font=FONT_BODY,
            )
            return
        left, right, top, bottom = 52, 24, 22, 42
        chart_w, chart_h = width - left - right, height - top - bottom
        maximum = max(max(self.values), 1)
        for step in range(5):
            y = top + chart_h * step / 4
            value = maximum * (4 - step) / 4
            self.create_line(left, y, width - right, y, fill=PALETTE["line"])
            self.create_text(
                left - 8, y, text=f"{value:,.0f}", anchor="e",
                fill=PALETTE["muted"], font=("Bahnschrift", 8),
            )
        if len(self.values) == 1:
            xs = [left + chart_w / 2]
        else:
            xs = [left + chart_w * i / (len(self.values) - 1) for i in range(len(self.values))]
        ys = [top + chart_h * (1 - value / maximum) for value in self.values]
        polygon = [left, top + chart_h]
        for x, y in zip(xs, ys, strict=False):
            polygon.extend([x, y])
        polygon.extend([xs[-1], top + chart_h])
        self.create_polygon(*polygon, fill=PALETTE["blue_light"], outline="")
        if len(xs) > 1:
            points = [coordinate for pair in zip(xs, ys, strict=False) for coordinate in pair]
            self.create_line(*points, fill=PALETTE["teal"], width=3, smooth=True)
        for index, (x, y) in enumerate(zip(xs, ys, strict=False)):
            self.create_oval(x - 4, y - 4, x + 4, y + 4, fill=PALETTE["surface"], outline=PALETTE["teal"], width=2)
            if index == len(xs) - 1:
                self.create_text(
                    x - 4, y - 12, text=f"{self.values[index]:,.0f}",
                    anchor="e", fill=PALETTE["teal"], font=("Bahnschrift", 9, "bold"),
                )
        label_step = max(1, math.ceil(len(self.labels) / 8))
        for index, label in enumerate(self.labels):
            if index % label_step == 0 or index == len(self.labels) - 1:
                self.create_text(
                    xs[index], height - 20, text=label[2:] if len(label) >= 7 else label,
                    fill=PALETTE["muted"], font=("Bahnschrift", 8),
                )


class MetricTile(tk.Frame):
    def __init__(self, master, title: str):
        super().__init__(
            master, bg=PALETTE["surface"], highlightbackground=PALETTE["line"],
            highlightthickness=1, padx=12, pady=10,
        )
        tk.Label(
            self, text=title, bg=PALETTE["surface"], fg=PALETTE["muted"],
            font=("Microsoft YaHei UI", 8),
        ).pack(anchor="w")
        self.value_label = tk.Label(
            self, text="—", bg=PALETTE["surface"], fg=PALETTE["ink"],
            font=("Bahnschrift SemiBold", 16),
        )
        self.value_label.pack(anchor="w", pady=(2, 2))
        self.note_label = tk.Label(
            self, text="", bg=PALETTE["surface"], fg=PALETTE["muted"],
            font=("Microsoft YaHei UI", 8), justify="left", anchor="w",
        )
        self.note_label.pack(fill="x", anchor="w")

    def set(self, value: str, note: str = "", tone: str = "ink") -> None:
        self.value_label.configure(text=value, fg=PALETTE.get(tone, PALETTE["ink"]))
        self.note_label.configure(text=note)


class ProductDetailTab(tk.Frame):
    GROUPS = [
        (
            "销售表现",
            "销售贡献、增长与需求稳定性",
            ["月均销售金额(万元)", "销售贡献率", "ABC分类", "总销售数量", "月均销量",
             "近3个月均量", "近3个月增长率", "需求波动系数"],
        ),
        (
            "库存健康",
            "现货、在途、目标水位和资金风险",
            ["总在库数量", "总可用量", "合计未完成", "可用量可销月数", "合计可销月数",
             "目标可销月数", "库存覆盖缺口", "销售库存错配指数",
             "缺口参考销售额", "超储参考销售额"],
        ),
        (
            "采购执行",
            "从理论缺口到可执行采购量",
            ["理论补货量", "最低补货量", "建议采购量", "当月采购数量", "采购覆盖月数"],
        ),
        (
            "客户与风险",
            "客户覆盖、复购深度、断货和经营优先级",
            ["购买客户数", "购买次数", "客户复购频次", "断货次数", "断货率", "经营优先分"],
        ),
    ]

    def __init__(self, master):
        super().__init__(master, bg=PALETTE["paper"])
        self.result: AnalysisResult | None = None
        self.visible_products = pd.DataFrame()
        self.current_row: pd.Series | None = None
        self.tiles: dict[str, MetricTile] = {}

        navigation = tk.Frame(
            self, bg=PALETTE["ink"], width=235,
            highlightbackground=PALETTE["ink_soft"], highlightthickness=1,
        )
        navigation.pack(side="left", fill="y")
        navigation.pack_propagate(False)
        tk.Label(
            navigation, text="产品导航", bg=PALETTE["ink"], fg="#FFFFFF",
            font=FONT_SECTION,
        ).pack(anchor="w", padx=16, pady=(18, 3))
        tk.Label(
            navigation, text="搜索品号、品名或规格", bg=PALETTE["ink"], fg="#AEBECB",
            font=("Microsoft YaHei UI", 8),
        ).pack(anchor="w", padx=16)
        self.search_var = tk.StringVar()
        search = ttk.Entry(navigation, textvariable=self.search_var)
        search.pack(fill="x", padx=14, pady=(10, 10))
        search.bind("<KeyRelease>", lambda _event: self._filter_products())
        list_frame = tk.Frame(navigation, bg=PALETTE["ink"])
        list_frame.pack(fill="both", expand=True, padx=(8, 3), pady=(0, 10))
        self.product_list = tk.Listbox(
            list_frame, bg=PALETTE["ink"], fg="#D8E4EC", selectbackground=PALETTE["teal"],
            selectforeground="#FFFFFF", borderwidth=0, highlightthickness=0,
            activestyle="none", font=FONT_SMALL, exportselection=False,
        )
        list_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.product_list.yview)
        self.product_list.configure(yscrollcommand=list_scroll.set)
        self.product_list.pack(side="left", fill="both", expand=True)
        list_scroll.pack(side="right", fill="y")
        self.product_list.bind("<<ListboxSelect>>", self._list_selected)

        content_frame = tk.Frame(self, bg=PALETTE["paper"])
        content_frame.pack(side="left", fill="both", expand=True)
        self.canvas = tk.Canvas(content_frame, bg=PALETTE["paper"], highlightthickness=0)
        scroll = ttk.Scrollbar(content_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.body = tk.Frame(self.canvas, bg=PALETTE["paper"])
        self.body_window = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.body.bind("<Configure>", self._update_scrollregion)
        self.canvas.bind("<Configure>", self._resize_body)
        self.canvas.bind_all("<MouseWheel>", self._mousewheel)

        self._build_detail()

    def _update_scrollregion(self, _event=None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_body(self, event) -> None:
        self.canvas.itemconfigure(self.body_window, width=event.width)

    def _mousewheel(self, event) -> None:
        if self.winfo_ismapped():
            direction = -1 if event.delta > 0 else 1
            self.canvas.yview_scroll(direction, "units")

    def _build_detail(self) -> None:
        header = tk.Frame(self.body, bg=PALETTE["paper"])
        header.pack(fill="x", padx=22, pady=(18, 10))
        identity = tk.Frame(header, bg=PALETTE["paper"])
        identity.pack(side="left", fill="x", expand=True)
        self.product_title = tk.Label(
            identity, text="请选择产品", bg=PALETTE["paper"], fg=PALETTE["ink"],
            font=("Microsoft YaHei UI", 19, "bold"),
        )
        self.product_title.pack(anchor="w")
        self.product_meta = tk.Label(
            identity, text="导入 Excel 后可查看每个产品的完整经营画像",
            bg=PALETTE["paper"], fg=PALETTE["muted"], font=FONT_SMALL,
        )
        self.product_meta.pack(anchor="w", pady=(3, 0))
        badges = tk.Frame(header, bg=PALETTE["paper"])
        badges.pack(side="right")
        self.layer_badge = self._badge(badges, "产品分层", PALETTE["teal_light"], PALETTE["teal"])
        self.abc_badge = self._badge(badges, "ABC —", PALETTE["blue_light"], PALETTE["blue"])
        self.score_badge = self._badge(badges, "优先分 —", PALETTE["amber_light"], PALETTE["amber"])

        self.action_panel = tk.Frame(
            self.body, bg=PALETTE["teal_light"], highlightbackground="#B6DCD7",
            highlightthickness=1, padx=16, pady=12,
        )
        self.action_panel.pack(fill="x", padx=22, pady=(0, 12))
        self.action_heading = tk.Label(
            self.action_panel, text="建议动作", bg=PALETTE["teal_light"],
            fg=PALETTE["teal"], font=("Microsoft YaHei UI", 9, "bold"),
        )
        self.action_heading.pack(anchor="w")
        self.action_text = tk.Label(
            self.action_panel, text="选择一个产品后生成经营建议", bg=PALETTE["teal_light"],
            fg=PALETTE["ink"], font=FONT_BODY, justify="left", anchor="w", wraplength=850,
        )
        self.action_text.pack(fill="x", anchor="w", pady=(2, 0))

        visual_row = tk.Frame(self.body, bg=PALETTE["paper"])
        visual_row.pack(fill="x", padx=22, pady=(0, 12))
        visual_row.grid_columnconfigure(0, weight=3)
        visual_row.grid_columnconfigure(1, weight=2)
        trend_panel = self._panel(visual_row, "月度销量趋势", "识别季节性、增长拐点和异常波动")
        trend_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.trend_chart = TrendChart(trend_panel, height=250)
        self.trend_chart.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        gauge_panel = self._panel(visual_row, "库存水位轨", "当前覆盖月数与目标水位的距离")
        gauge_panel.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self.gauge = CoverageGauge(gauge_panel, height=145)
        self.gauge.pack(fill="x", padx=10, pady=(22, 8))
        self.cover_note = tk.Label(
            gauge_panel, text="—", bg=PALETTE["surface"], fg=PALETTE["muted"],
            font=FONT_SMALL, justify="left", wraplength=360,
        )
        self.cover_note.pack(fill="x", padx=18, pady=(0, 18))

        for title, subtitle, metrics in self.GROUPS:
            panel = self._panel(self.body, title, subtitle)
            panel.pack(fill="x", padx=22, pady=(0, 12))
            grid = tk.Frame(panel, bg=PALETTE["surface"])
            grid.pack(fill="x", padx=12, pady=(0, 14))
            for column in range(4):
                grid.grid_columnconfigure(column, weight=1, uniform=f"{title}_tile")
            for index, metric in enumerate(metrics):
                tile = MetricTile(grid, metric)
                tile.grid(
                    row=index // 4, column=index % 4, sticky="nsew",
                    padx=(0 if index % 4 == 0 else 4, 0 if index % 4 == 3 else 4),
                    pady=4,
                )
                self.tiles[metric] = tile

    def _badge(self, master, text: str, background: str, foreground: str) -> tk.Label:
        label = tk.Label(
            master, text=text, bg=background, fg=foreground,
            font=("Microsoft YaHei UI", 9, "bold"), padx=11, pady=6,
        )
        label.pack(side="left", padx=4)
        return label

    def _panel(self, master, title: str, subtitle: str) -> tk.Frame:
        panel = tk.Frame(
            master, bg=PALETTE["surface"], highlightbackground=PALETTE["line"],
            highlightthickness=1,
        )
        heading = tk.Frame(panel, bg=PALETTE["surface"])
        heading.pack(fill="x", padx=16, pady=(13, 8))
        tk.Label(
            heading, text=title, bg=PALETTE["surface"], fg=PALETTE["ink"], font=FONT_SECTION,
        ).pack(anchor="w")
        tk.Label(
            heading, text=subtitle, bg=PALETTE["surface"], fg=PALETTE["muted"], font=FONT_SMALL,
        ).pack(anchor="w")
        return panel

    def update_result(self, result: AnalysisResult) -> None:
        self.result = result
        self.search_var.set("")
        self._filter_products()
        if not result.products.empty:
            self.select_product(result.products.iloc[0])

    def _filter_products(self) -> None:
        if self.result is None:
            return
        products = self.result.products
        query = self.search_var.get().strip().lower()
        if query:
            searchable = (
                products["品号"].astype(str) + " " + products["品名"].astype(str)
                + " " + products["类型"].astype(str) + " " + products["规格"].astype(str)
            )
            products = products[searchable.str.lower().str.contains(query, regex=False)]
        self.visible_products = products
        self.product_list.delete(0, "end")
        for _, row in products.iterrows():
            self.product_list.insert("end", f"{row['品号']}  {row['品名']}".strip())

    def _list_selected(self, _event=None) -> None:
        selection = self.product_list.curselection()
        if not selection or self.visible_products.empty:
            return
        self.select_product(self.visible_products.iloc[selection[0]], sync_list=False)

    def select_product(self, row: pd.Series, sync_list: bool = True) -> None:
        self.current_row = row
        self.product_title.configure(text=f"{row['品号']}  {row['品名']}".strip())
        meta = " ｜ ".join(
            f"{label}：{row[field]}"
            for label, field in (("类型", "类型"), ("规格", "规格"), ("材料", "材料"))
            if str(row.get(field, "")).strip() and str(row.get(field, "")).lower() != "nan"
        )
        self.product_meta.configure(text=meta or "原表未提供类型、规格或材料")
        self.layer_badge.configure(text=str(row["产品分层"]))
        self.abc_badge.configure(text=f"ABC {row['ABC分类']}")
        self.score_badge.configure(text=f"优先分 {_format_number(row['经营优先分'], 0)}")

        tone, background, border = self._action_tone(str(row["产品分层"]))
        self.action_panel.configure(bg=background, highlightbackground=border)
        self.action_heading.configure(bg=background, fg=PALETTE[tone])
        self.action_text.configure(bg=background, text=str(row["建议动作"]))

        label = f"{row['品号']} · {row['品名']}"
        self.gauge.set_value(label, row["合计可销月数"], row["目标可销月数"])
        self.cover_note.configure(text=self._coverage_note(row), fg=PALETTE[tone])
        self._set_monthly_series(row)
        for metric, tile in self.tiles.items():
            tile.set(
                _format_metric(metric, row.get(metric)),
                self._metric_note(metric, row.get(metric), row),
                self._metric_tone(metric, row.get(metric), row),
            )
        if sync_list and not self.visible_products.empty:
            source_row = int(row["_源数据行"])
            matches = [
                index for index, value in enumerate(self.visible_products["_源数据行"].tolist())
                if int(value) == source_row
            ]
            if matches:
                position = matches[0]
                self.product_list.selection_clear(0, "end")
                self.product_list.selection_set(position)
                self.product_list.see(position)
        self.canvas.yview_moveto(0)

    def _set_monthly_series(self, row: pd.Series) -> None:
        if self.result is None or self.result.monthly_sales.empty:
            self.trend_chart.set_data([], [])
            return
        match = self.result.monthly_sales[
            self.result.monthly_sales["_源数据行"] == int(row["_源数据行"])
        ]
        if match.empty:
            self.trend_chart.set_data([], [])
            return
        labels = [column for column in match.columns if column != "_源数据行"]
        values = pd.to_numeric(match.iloc[0][labels], errors="coerce").fillna(0).astype(float).tolist()
        self.trend_chart.set_data(labels[-24:], values[-24:])

    def _action_tone(self, category: str) -> tuple[str, str, str]:
        if category in ("衰退观察品", "数据不足"):
            return "red", PALETTE["red_light"], "#E9B9B9"
        if category in ("高库存促销品", "补货关注品"):
            return "amber", PALETTE["amber_light"], "#EBD19A"
        return "teal", PALETTE["teal_light"], "#B6DCD7"

    def _coverage_note(self, row: pd.Series) -> str:
        gap = row.get("库存覆盖缺口")
        if pd.isna(gap):
            return "缺少有效销量或库存数据，暂时无法判断库存健康度。"
        if gap < 0:
            return f"比目标少 {abs(float(gap)):.1f} 个月，建议核对在途订单并确认补货。"
        if gap > float(row["目标可销月数"]):
            return f"比目标多 {float(gap):.1f} 个月，存在明显积压与资金占用风险。"
        return f"比目标多 {float(gap):.1f} 个月，库存处于可控范围。"

    def _metric_tone(self, metric: str, value: object, row: pd.Series) -> str:
        if value is None or pd.isna(value):
            return "muted"
        number = float(value) if pd.api.types.is_number(value) else None
        if metric in ("近3个月增长率", "库存覆盖缺口") and number is not None:
            return "teal" if number >= 0 else "red"
        if metric == "断货率" and number is not None:
            return "red" if number > 0 else "teal"
        if metric == "合计可销月数" and number is not None:
            target = float(row["目标可销月数"])
            return "red" if number < target else "amber" if number > target * 2 else "teal"
        if metric in ("建议采购量", "缺口参考销售额", "超储参考销售额") and number:
            return "amber"
        if metric == "经营优先分" and number is not None:
            return "red" if number >= 70 else "amber" if number >= 50 else "teal"
        return "ink"

    def _metric_note(self, metric: str, value: object, row: pd.Series) -> str:
        if value is None or pd.isna(value):
            return "数据不足"
        number = float(value) if pd.api.types.is_number(value) else None
        if metric == "销售贡献率":
            return "全部产品营业额中的份额"
        if metric == "ABC分类":
            return {"A": "核心经营产品", "B": "重点维护产品", "C": "长尾产品"}.get(str(value), "")
        if metric == "近3个月增长率" and number is not None:
            return "近期增长" if number > 0.05 else "近期下滑" if number < -0.05 else "基本平稳"
        if metric == "需求波动系数" and number is not None:
            return "需求稳定" if number < 0.5 else "波动中等" if number < 1 else "波动较大"
        if metric in ("可用量可销月数", "合计可销月数"):
            return f"目标 {_format_number(row['目标可销月数'], 1)} 个月"
        if metric == "库存覆盖缺口" and number is not None:
            return "低于目标水位" if number < 0 else "高于目标水位"
        if metric == "销售库存错配指数" and number is not None:
            return "销售份额高于库存份额" if number > 1.15 else "库存份额偏高" if number < 0.85 else "销售与库存较匹配"
        if metric == "建议采购量":
            return "已按最低补货量取整"
        if metric == "采购覆盖月数" and number is not None:
            return "本月采购可覆盖的销售月份"
        if metric == "客户复购频次" and number is not None:
            return "复购较深" if number >= 2 else "复购空间较大"
        if metric == "断货率" and number is not None:
            return "存在断货历史" if number > 0 else "统计期未记录断货"
        if metric == "经营优先分" and number is not None:
            return "管理层优先处理" if number >= 70 else "持续关注" if number >= 50 else "例行复盘"
        if metric in ("缺口参考销售额", "超储参考销售额"):
            return "按参考售价估算"
        return ""


class AlertsTab(tk.Frame):
    COLUMNS = [
        ("级别", 60),
        ("类型", 100),
        ("产品", 150),
        ("说明", 310),
        ("建议", 420),
        ("经营优先分", 90),
    ]

    def __init__(self, master):
        super().__init__(master, bg=PALETTE["paper"])
        heading = tk.Frame(self, bg=PALETTE["paper"])
        heading.pack(fill="x", padx=22, pady=(18, 10))
        tk.Label(heading, text="风险与机会预警", bg=PALETTE["paper"], fg=PALETTE["ink"], font=FONT_SECTION).pack(side="left")
        self.count_label = tk.Label(heading, text="尚未分析", bg=PALETTE["paper"], fg=PALETTE["muted"], font=FONT_SMALL)
        self.count_label.pack(side="right")
        container = tk.Frame(self, bg=PALETTE["surface"], highlightbackground=PALETTE["line"], highlightthickness=1)
        container.pack(fill="both", expand=True, padx=22, pady=(0, 20))
        columns = [name for name, _ in self.COLUMNS]
        self.tree = ttk.Treeview(container, columns=columns, show="headings")
        for name, width in self.COLUMNS:
            self.tree.heading(name, text=name)
            self.tree.column(name, width=width, minwidth=60, stretch=name in ("说明", "建议"))
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.tag_configure("高", background=PALETTE["red_light"])
        self.tree.tag_configure("中", background=PALETTE["amber_light"])
        self.tree.tag_configure("低", background=PALETTE["teal_light"])

    def update_result(self, result: AnalysisResult) -> None:
        self.tree.delete(*self.tree.get_children())
        for _, row in result.alerts.iterrows():
            values = [row.get(column, "") for column, _ in self.COLUMNS]
            self.tree.insert("", "end", values=values, tags=(str(row["级别"]),))
        high = int((result.alerts["级别"] == "高").sum()) if not result.alerts.empty else 0
        self.count_label.configure(text=f"{len(result.alerts)} 条预警｜{high} 条高优先级")


class DefinitionsTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=PALETTE["paper"])
        pane = tk.Frame(self, bg=PALETTE["surface"], highlightbackground=PALETTE["line"], highlightthickness=1)
        pane.pack(fill="both", expand=True, padx=22, pady=20)
        text = tk.Text(
            pane,
            bg=PALETTE["surface"],
            fg=PALETTE["ink_soft"],
            font=FONT_BODY,
            relief="flat",
            padx=24,
            pady=20,
            wrap="word",
        )
        scroll = ttk.Scrollbar(pane, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        text.tag_configure("title", font=("Microsoft YaHei UI", 18, "bold"), foreground=PALETTE["ink"], spacing3=14)
        text.tag_configure("metric", font=("Microsoft YaHei UI", 11, "bold"), foreground=PALETTE["teal"], spacing1=12)
        text.tag_configure("body", font=FONT_BODY, foreground=PALETTE["ink_soft"], lmargin1=8, lmargin2=8, spacing3=5)
        text.insert("end", "指标口径与使用方法\n", "title")
        text.insert(
            "end",
            "程序优先使用原始Excel中的现成字段；缺失时再按下列公式推导。所有金额指标均为参考销售价值，不等于毛利或现金占用。\n\n",
            "body",
        )
        for name, formula, purpose in METRIC_DEFINITIONS:
            text.insert("end", f"{name}\n", "metric")
            text.insert("end", f"计算：{formula}\n用途：{purpose}\n", "body")
        text.configure(state="disabled")


class QualityPanel(tk.Toplevel):
    def __init__(self, master, result: AnalysisResult):
        super().__init__(master)
        self.title("数据质量检查")
        self.geometry("720x440")
        self.configure(bg=PALETTE["paper"])
        self.transient(master)
        tk.Label(self, text="数据质量检查", bg=PALETTE["paper"], fg=PALETTE["ink"], font=FONT_TITLE).pack(
            anchor="w", padx=24, pady=(22, 4)
        )
        tk.Label(
            self,
            text=f"{result.source.path.name}｜{result.source.sheet_name}｜表头第 {result.source.header_row} 行",
            bg=PALETTE["paper"],
            fg=PALETTE["muted"],
            font=FONT_SMALL,
        ).pack(anchor="w", padx=24)
        tk.Label(
            self,
            text=(
                f"已识别 {len(result.source.columns.fields)} 个业务字段、"
                f"{len(result.source.columns.monthly_sales)} 个月度销量字段；"
                f"{len(result.source.columns.unmatched_columns)} 个字段保留在原始数据中"
            ),
            bg=PALETTE["paper"],
            fg=PALETTE["teal"],
            font=("Microsoft YaHei UI", 9, "bold"),
        ).pack(anchor="w", padx=24, pady=(4, 0))
        body = tk.Frame(self, bg=PALETTE["surface"], highlightbackground=PALETTE["line"], highlightthickness=1)
        body.pack(fill="both", expand=True, padx=24, pady=18)
        messages = result.quality_messages or ["未发现明显的数据质量问题。"]
        for index, message in enumerate(messages, start=1):
            row = tk.Frame(body, bg=PALETTE["surface"])
            row.pack(fill="x", padx=18, pady=(14 if index == 1 else 5, 5))
            tk.Label(
                row,
                text=str(index),
                width=3,
                bg=PALETTE["amber_light"],
                fg=PALETTE["amber"],
                font=("Bahnschrift", 10, "bold"),
            ).pack(side="left", anchor="n")
            tk.Label(
                row,
                text=message,
                bg=PALETTE["surface"],
                fg=PALETTE["ink_soft"],
                font=FONT_BODY,
                justify="left",
                wraplength=590,
            ).pack(side="left", padx=12, anchor="w")


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NOK 产品经营分析")
        self.geometry("1420x880")
        self.minsize(1120, 700)
        self.configure(bg=PALETTE["paper"])
        self.result: AnalysisResult | None = None
        self._analysis_queue: queue.Queue[tuple[str, int, object]] = queue.Queue()
        self._analysis_token = 0
        self._analysis_active = False
        self._analysis_started_at = 0.0
        self._analysis_path = ""
        self._configure_style()
        self._build_header()
        self._build_tabs()
        self._build_status()
        self._bind_shortcuts()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TNotebook", background=PALETTE["paper"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=PALETTE["paper"],
            foreground=PALETTE["muted"],
            padding=(20, 11),
            font=FONT_BODY,
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", PALETTE["surface"])],
            foreground=[("selected", PALETTE["teal"])],
        )
        style.configure(
            "Treeview",
            background=PALETTE["surface"],
            fieldbackground=PALETTE["surface"],
            foreground=PALETTE["ink_soft"],
            rowheight=30,
            font=FONT_SMALL,
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background=PALETTE["ink"],
            foreground="#FFFFFF",
            font=("Microsoft YaHei UI", 9, "bold"),
            relief="flat",
            padding=(7, 8),
        )
        style.map("Treeview.Heading", background=[("active", PALETTE["ink_soft"])])
        style.configure("TEntry", padding=7)
        style.configure("TCombobox", padding=6)

    def _button(self, master, text: str, command, primary: bool = False) -> tk.Button:
        macos_native_button = sys.platform == "darwin"
        primary_background = PALETTE["surface"] if macos_native_button else PALETTE["teal"]
        primary_foreground = PALETTE["teal"] if macos_native_button else "#FFFFFF"
        return tk.Button(
            master,
            text=text,
            command=command,
            bg=primary_background if primary else PALETTE["surface"],
            fg=primary_foreground if primary else PALETTE["ink"],
            activebackground=PALETTE["ink_soft"] if primary else PALETTE["paper"],
            activeforeground=primary_foreground if primary else PALETTE["ink"],
            font=("Microsoft YaHei UI", 9, "bold"),
            relief="flat",
            bd=0,
            padx=16,
            pady=9,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=PALETTE["teal"] if primary else PALETTE["line"],
        )

    def _build_header(self) -> None:
        header = tk.Frame(self, bg=PALETTE["ink"], height=92)
        header.pack(fill="x")
        header.pack_propagate(False)
        brand = tk.Frame(header, bg=PALETTE["ink"])
        brand.pack(side="left", padx=26, pady=18)
        tk.Label(
            brand,
            text="NOK / PRODUCT SIGNAL",
            bg=PALETTE["ink"],
            fg="#8FC9C3",
            font=("Bahnschrift SemiCondensed", 9, "bold"),
        ).pack(anchor="w")
        tk.Label(
            brand,
            text="产品经营分析",
            bg=PALETTE["ink"],
            fg="#FFFFFF",
            font=FONT_TITLE,
        ).pack(anchor="w")

        actions = tk.Frame(header, bg=PALETTE["ink"])
        actions.pack(side="right", padx=24)
        self.quality_button = self._button(actions, "数据质量", self.show_quality)
        self.quality_button.pack(side="left", padx=5)
        self.export_button = self._button(actions, "导出分析", self.export_result)
        self.export_button.pack(side="left", padx=5)
        self.import_button = self._button(actions, "导入 Excel", self.choose_file, primary=True)
        self.import_button.pack(side="left", padx=5)

        settings = tk.Frame(header, bg=PALETTE["ink"])
        settings.pack(side="right", padx=14)
        tk.Label(settings, text="默认目标月数", bg=PALETTE["ink"], fg="#B9C8D4", font=FONT_SMALL).grid(row=0, column=0, sticky="w")
        self.target_var = tk.StringVar(value="7.7")
        ttk.Entry(settings, textvariable=self.target_var, width=6).grid(row=1, column=0, padx=(0, 12))
        tk.Label(settings, text="高库存倍数", bg=PALETTE["ink"], fg="#B9C8D4", font=FONT_SMALL).grid(row=0, column=1, sticky="w")
        self.multiple_var = tk.StringVar(value="2.0")
        ttk.Entry(settings, textvariable=self.multiple_var, width=6).grid(row=1, column=1)

    def _build_tabs(self) -> None:
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        self.dashboard = DashboardTab(self.notebook)
        self.products = ProductTab(
            self.notebook, self._product_selected, self._open_product_detail
        )
        self.product_detail = ProductDetailTab(self.notebook)
        self.alerts = AlertsTab(self.notebook)
        self.definitions = DefinitionsTab(self.notebook)
        self.notebook.add(self.dashboard, text="总览")
        self.notebook.add(self.products, text="产品清单")
        self.notebook.add(self.product_detail, text="产品详情")
        self.notebook.add(self.alerts, text="风险预警")
        self.notebook.add(self.definitions, text="指标说明")

    def _build_status(self) -> None:
        status = tk.Frame(self, bg=PALETTE["surface"], height=30, highlightbackground=PALETTE["line"], highlightthickness=1)
        status.pack(fill="x")
        self.status_dot = tk.Label(status, text="●", bg=PALETTE["surface"], fg=PALETTE["muted"], font=("Arial", 8))
        self.status_dot.pack(side="left", padx=(16, 7))
        self.status_label = tk.Label(
            status,
            text="等待导入 Excel",
            bg=PALETTE["surface"],
            fg=PALETTE["muted"],
            font=FONT_SMALL,
        )
        self.status_label.pack(side="left")

    def _bind_shortcuts(self) -> None:
        tabs = [
            self.dashboard,
            self.products,
            self.product_detail,
            self.alerts,
            self.definitions,
        ]
        for position, tab in enumerate(tabs, start=1):
            self.bind_all(
                f"<Command-Key-{position}>",
                lambda _event, target=tab: self.notebook.select(target),
            )
            self.bind_all(
                f"<Control-Key-{position}>",
                lambda _event, target=tab: self.notebook.select(target),
            )

    def choose_file(self) -> None:
        path = filedialog.askopenfilename(
            title="选择产品分析 Excel",
            filetypes=[
                ("Excel 文件", "*.xlsx *.xlsm *.xls"),
                ("CSV 文件", "*.csv"),
                ("所有文件", "*.*"),
            ],
        )
        if path:
            self.analyze_path(path)

    def _config(self) -> AnalysisConfig:
        try:
            target = float(self.target_var.get())
            multiple = float(self.multiple_var.get())
        except ValueError as exc:
            raise ValueError("目标月数和高库存倍数必须是数字。") from exc
        if target <= 0 or multiple <= 1:
            raise ValueError("目标月数必须大于0，高库存倍数必须大于1。")
        return AnalysisConfig(default_target_months=target, high_stock_multiple=multiple)

    def analyze_path(self, path: str) -> None:
        try:
            config = self._config()
        except ValueError as exc:
            messagebox.showerror("设置无效", str(exc))
            return
        self.import_button.configure(state="disabled", text="正在分析…")
        self.status_dot.configure(fg=PALETTE["amber"])
        self.status_label.configure(text=f"正在读取 {Path(path).name}")
        self._analysis_token += 1
        token = self._analysis_token
        self._analysis_active = True
        self._analysis_started_at = time.monotonic()
        self._analysis_path = path

        def worker() -> None:
            staged_path: Path | None = None
            try:
                source_path = Path(path).expanduser().resolve()
                analysis_path = source_path
                if "com.tencent.xinWeChat" in str(source_path):
                    self._analysis_queue.put(
                        ("progress", token, "正在从微信文件夹创建临时副本…")
                    )
                    staging_dir = Path(tempfile.gettempdir()) / "nok_product_insight_imports"
                    staging_dir.mkdir(parents=True, exist_ok=True)
                    staged_path = staging_dir / f"{uuid.uuid4().hex}{source_path.suffix.lower()}"
                    shutil.copyfile(source_path, staged_path)
                    analysis_path = staged_path

                loaded = load_excel(analysis_path)
                # Keep the user-visible source name even when a temporary copy was used.
                loaded.path = source_path
                self._analysis_queue.put(("progress", token, "字段识别完成，正在计算指标…"))
                result = analyze(loaded, config)
                self._analysis_queue.put(("success", token, result))
            except Exception as exc:  # UI boundary: show actionable error to the user.
                self._analysis_queue.put(("error", token, exc))
            finally:
                if staged_path is not None:
                    try:
                        staged_path.unlink(missing_ok=True)
                    except OSError:
                        pass

        threading.Thread(target=worker, daemon=True).start()
        # Only the main Tk thread reads worker messages and updates widgets.
        self.after(80, self._poll_analysis_queue)

    def _poll_analysis_queue(self) -> None:
        terminal_event = False
        while True:
            try:
                event, token, payload = self._analysis_queue.get_nowait()
            except queue.Empty:
                break
            if token != self._analysis_token:
                continue
            if event == "progress":
                self.status_label.configure(text=str(payload))
            elif event == "success":
                terminal_event = True
                self._analysis_active = False
                self._analysis_complete(payload)  # type: ignore[arg-type]
            elif event == "error":
                terminal_event = True
                self._analysis_active = False
                self._analysis_failed(payload)  # type: ignore[arg-type]

        if terminal_event or not self._analysis_active:
            return
        if time.monotonic() - self._analysis_started_at > 60:
            self._analysis_active = False
            self._analysis_token += 1
            self.import_button.configure(state="normal", text="导入 Excel")
            self.status_dot.configure(fg=PALETTE["red"])
            self.status_label.configure(text="读取超时，请将文件复制到桌面后重试")
            messagebox.showerror(
                "读取文件超时",
                "程序等待文件超过60秒。\n\n"
                "如果文件来自微信、网盘或邮件附件，请先把Excel复制到桌面或“下载”文件夹，"
                "确认能在Excel/WPS中正常打开后再导入。",
            )
            return
        self.after(80, self._poll_analysis_queue)

    def _analysis_complete(self, result: AnalysisResult) -> None:
        self.result = result
        self.dashboard.update_result(result)
        self.products.update_result(result)
        self.product_detail.update_result(result)
        self.alerts.update_result(result)
        self.import_button.configure(state="normal", text="导入 Excel")
        self.status_dot.configure(fg=PALETTE["teal"])
        self.status_label.configure(
            text=f"{result.source.path.name}｜{result.source.sheet_name}｜{len(result.products)} 个产品｜{len(result.quality_messages)} 条数据提示"
        )
        if not result.products.empty:
            self._product_selected(result.products.iloc[0])

    def _analysis_failed(self, error: Exception) -> None:
        self.import_button.configure(state="normal", text="导入 Excel")
        self.status_dot.configure(fg=PALETTE["red"])
        self.status_label.configure(text="分析失败，请检查文件结构")
        messagebox.showerror(
            "无法分析这个文件",
            f"{type(error).__name__}: {error}\n\n"
            "请确认文件未加密、未被其他程序锁定，并且包含品号/品名及销售数量字段。"
            "\n如果文件来自微信，请先复制到桌面后再试。",
        )

    def _product_selected(self, row: pd.Series) -> None:
        label = f"{row['品号']} · {row['品名']}｜{row['产品分层']}"
        self.dashboard.gauge.set_value(label, row["合计可销月数"], row["目标可销月数"])
        self.product_detail.select_product(row)

    def _open_product_detail(self, row: pd.Series) -> None:
        self.product_detail.select_product(row)
        self.notebook.select(self.product_detail)

    def export_result(self) -> None:
        if self.result is None:
            messagebox.showinfo("尚无分析结果", "请先导入一个 Excel 文件。")
            return
        default_name = f"{self.result.source.path.stem}_经营分析.xlsx"
        path = filedialog.asksaveasfilename(
            title="导出分析结果",
            defaultextension=".xlsx",
            initialfile=default_name,
            filetypes=[("Excel 文件", "*.xlsx")],
        )
        if not path:
            return
        try:
            output = export_analysis(self.result, path)
            messagebox.showinfo("导出完成", f"分析结果已保存到：\n{output}")
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))

    def show_quality(self) -> None:
        if self.result is None:
            messagebox.showinfo("尚无分析结果", "请先导入一个 Excel 文件。")
            return
        QualityPanel(self, self.result)


def run_app(initial_file: str | None = None) -> None:
    app = MainWindow()
    if initial_file:
        app.after(300, lambda: app.analyze_path(initial_file))
    app.mainloop()
