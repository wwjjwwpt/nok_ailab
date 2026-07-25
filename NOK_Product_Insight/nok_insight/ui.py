from __future__ import annotations

import math
import threading
import tkinter as tk
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
    COLUMNS = [
        ("品号", 90),
        ("品名", 110),
        ("产品分层", 120),
        ("经营优先分", 90),
        ("月均销售金额(万元)", 125),
        ("月均销量", 95),
        ("近3个月增长率", 105),
        ("需求波动系数", 95),
        ("合计可销月数", 100),
        ("目标可销月数", 95),
        ("建议采购量", 100),
        ("超储参考销售额", 120),
        ("建议动作", 320),
    ]

    def __init__(self, master, on_select):
        super().__init__(master, bg=PALETTE["paper"])
        self.result: AnalysisResult | None = None
        self.filtered = pd.DataFrame()
        self.on_select = on_select
        filters = tk.Frame(self, bg=PALETTE["paper"])
        filters.pack(fill="x", padx=22, pady=(18, 10))
        tk.Label(filters, text="搜索", bg=PALETTE["paper"], fg=PALETTE["muted"], font=FONT_SMALL).pack(side="left")
        self.search_var = tk.StringVar()
        search = ttk.Entry(filters, textvariable=self.search_var, width=28)
        search.pack(side="left", padx=(8, 18))
        search.bind("<KeyRelease>", lambda _event: self.apply_filter())
        tk.Label(filters, text="产品分层", bg=PALETTE["paper"], fg=PALETTE["muted"], font=FONT_SMALL).pack(side="left")
        self.category_var = tk.StringVar(value="全部")
        self.category = ttk.Combobox(filters, textvariable=self.category_var, state="readonly", width=18)
        self.category["values"] = ("全部",)
        self.category.pack(side="left", padx=(8, 18))
        self.category.bind("<<ComboboxSelected>>", lambda _event: self.apply_filter())
        self.count_label = tk.Label(filters, text="0 个产品", bg=PALETTE["paper"], fg=PALETTE["muted"], font=FONT_SMALL)
        self.count_label.pack(side="right")

        container = tk.Frame(
            self,
            bg=PALETTE["surface"],
            highlightbackground=PALETTE["line"],
            highlightthickness=1,
        )
        container.pack(fill="both", expand=True, padx=22, pady=(0, 20))
        columns = [name for name, _ in self.COLUMNS]
        self.tree = ttk.Treeview(container, columns=columns, show="headings", selectmode="browse")
        for name, width in self.COLUMNS:
            self.tree.heading(name, text=name, command=lambda key=name: self.sort_by(key))
            self.tree.column(name, width=width, minwidth=65, stretch=name == "建议动作")
        y_scroll = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self._selected)
        self.tree.tag_configure("risk", background=PALETTE["red_light"])
        self.tree.tag_configure("opportunity", background=PALETTE["amber_light"])
        self.tree.tag_configure("healthy", background=PALETTE["teal_light"])
        self.sort_reverse: dict[str, bool] = {}

    def update_result(self, result: AnalysisResult) -> None:
        self.result = result
        categories = ["全部"] + sorted(result.products["产品分层"].dropna().astype(str).unique().tolist())
        self.category["values"] = categories
        self.category_var.set("全部")
        self.search_var.set("")
        self.apply_filter()

    def apply_filter(self) -> None:
        if self.result is None:
            return
        frame = self.result.products.copy()
        category = self.category_var.get()
        if category and category != "全部":
            frame = frame[frame["产品分层"] == category]
        query = self.search_var.get().strip().lower()
        if query:
            searchable = frame["品号"].astype(str) + " " + frame["品名"].astype(str)
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
        for index, row in self.filtered.iterrows():
            values = []
            for column, _ in self.COLUMNS:
                value = row.get(column)
                if column == "近3个月增长率":
                    values.append(_format_percent(value))
                elif column in ("月均销售金额(万元)", "月均销量", "需求波动系数", "合计可销月数", "目标可销月数"):
                    values.append(_format_number(value, 1))
                elif column in ("建议采购量", "超储参考销售额", "经营优先分"):
                    values.append(_format_number(value, 0))
                else:
                    values.append("" if pd.isna(value) else str(value))
            category = row["产品分层"]
            tag = "risk" if category in ("衰退观察品", "数据不足") else "opportunity" if category in ("高库存促销品", "补货关注品") else "healthy"
            self.tree.insert("", "end", iid=str(index), values=values, tags=(tag,))
        self.count_label.configure(text=f"{len(self.filtered)} 个产品")

    def _selected(self, _event=None) -> None:
        selection = self.tree.selection()
        if not selection or self.filtered.empty:
            return
        index = int(selection[0])
        if index not in self.filtered.index:
            return
        self.on_select(self.filtered.loc[index])


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
        self._configure_style()
        self._build_header()
        self._build_tabs()
        self._build_status()

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
        return tk.Button(
            master,
            text=text,
            command=command,
            bg=PALETTE["teal"] if primary else PALETTE["surface"],
            fg="#FFFFFF" if primary else PALETTE["ink"],
            activebackground=PALETTE["ink_soft"] if primary else PALETTE["paper"],
            activeforeground="#FFFFFF" if primary else PALETTE["ink"],
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
        self.products = ProductTab(self.notebook, self._product_selected)
        self.alerts = AlertsTab(self.notebook)
        self.definitions = DefinitionsTab(self.notebook)
        self.notebook.add(self.dashboard, text="总览")
        self.notebook.add(self.products, text="产品清单")
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

        def worker() -> None:
            try:
                loaded = load_excel(path)
                result = analyze(loaded, config)
                self.after(0, lambda: self._analysis_complete(result))
            except Exception as exc:  # UI boundary: show actionable error to the user.
                self.after(0, lambda: self._analysis_failed(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _analysis_complete(self, result: AnalysisResult) -> None:
        self.result = result
        self.dashboard.update_result(result)
        self.products.update_result(result)
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
            f"{error}\n\n请确认文件未加密，并且包含品号/品名及销售数量字段。",
        )

    def _product_selected(self, row: pd.Series) -> None:
        label = f"{row['品号']} · {row['品名']}｜{row['产品分层']}"
        self.dashboard.gauge.set_value(label, row["合计可销月数"], row["目标可销月数"])

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
