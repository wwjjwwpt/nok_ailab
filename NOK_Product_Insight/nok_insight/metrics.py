from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .config import AnalysisConfig
from .loader import ExcelLoadResult


METRIC_DEFINITIONS = [
    ("销售贡献率", "产品月均销售金额 ÷ 全部产品月均销售金额", "识别营业额核心产品。"),
    ("ABC分类", "按销售贡献率从高到低累计；A≤70%，B≤90%，其余为C", "确定经营资源投入优先级。"),
    ("近3个月增长率", "最近3个月平均销量 ÷ 前3个月平均销量 - 1", "发现增长和快速衰退。"),
    ("需求波动系数", "12个月销量标准差 ÷ 月均销量", "区分稳定需求与偶发大单。"),
    ("合计可销月数", "(可用库存 + 未完成数量) ÷ 月均销量", "衡量现有供应可支撑的时间。"),
    ("库存覆盖缺口", "合计可销月数 - 目标可销月数", "负数代表低于目标，过高代表积压。"),
    ("销售库存错配指数", "销售占比 ÷ 库存占比", "大于1表示销售份额高于库存份额。"),
    ("缺口参考销售额", "MAX(目标月数-覆盖月数,0) × 月均销量 × 参考售价", "估算目标库存缺口对应的销售价值。"),
    ("超储参考销售额", "MAX(覆盖月数-目标月数,0) × 月均销量 × 参考售价", "估算超目标库存对应的销售价值。"),
    ("理论补货量", "MAX(目标月数-覆盖月数,0) × 月均销量", "补足目标库存所需的理论数量。"),
    ("建议采购量", "理论补货量按最低补货量向上取整", "形成可执行的采购建议。"),
    ("客户复购频次", "购买次数 ÷ 购买客户数", "判断客户黏性和复购深度。"),
    ("断货率", "统计期断货次数 ÷ 统计月数", "衡量缺货发生频率。"),
    ("采购覆盖月数", "当月采购数量 ÷ 月均销量", "检查当前采购规模是否合理。"),
    ("经营优先分", "销售贡献、增长变化、库存偏差、断货和客户覆盖的综合分", "决定管理层先处理哪些SKU。"),
]


@dataclass
class AnalysisResult:
    source: ExcelLoadResult
    products: pd.DataFrame
    monthly_sales: pd.DataFrame
    summary: dict[str, float | int | str]
    alerts: pd.DataFrame
    quality_messages: list[str] = field(default_factory=list)


def _numeric(frame: pd.DataFrame, column: str | None, default: float = np.nan) -> pd.Series:
    if column is None or column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype="float64")
    return pd.to_numeric(frame[column], errors="coerce")


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator.divide(denominator.where(denominator.abs() > 1e-12))


def _round_to_moq(quantity: pd.Series, minimum_order: pd.Series) -> pd.Series:
    values: list[float] = []
    for qty, moq in zip(quantity.fillna(0), minimum_order.fillna(0), strict=False):
        if qty <= 0:
            values.append(0.0)
        elif moq > 0:
            values.append(float(math.ceil(qty / moq) * moq))
        else:
            values.append(float(math.ceil(qty)))
    return pd.Series(values, index=quantity.index)


def _classify(row: pd.Series, config: AnalysisConfig) -> str:
    if row["月均销量"] <= 0 or pd.isna(row["合计可销月数"]):
        return "数据不足"
    if row["合计可销月数"] >= row["目标可销月数"] * config.high_stock_multiple:
        return "高库存促销品"
    if row["近3个月增长率"] <= config.decline_threshold and row["合计可销月数"] > row["目标可销月数"]:
        return "衰退观察品"
    if row["ABC分类"] == "A" and row["合计可销月数"] <= row["目标可销月数"] * 1.2:
        return "明星守供品"
    if row["近3个月增长率"] >= config.growth_threshold and row["合计可销月数"] <= row["目标可销月数"] * 1.5:
        return "增长培育品"
    if row["合计可销月数"] < row["目标可销月数"]:
        return "补货关注品"
    return "常规经营品"


def _action(row: pd.Series, config: AnalysisConfig) -> str:
    category = row["产品分层"]
    if category == "明星守供品":
        return "保障到货；每周跟踪可用库存和未完成订单"
    if category == "增长培育品":
        return "增加曝光和销售激励；按增长趋势滚动补货"
    if category == "高库存促销品":
        return "暂停常规补货；定向促销、组合销售并清理滞销规格"
    if category == "衰退观察品":
        return "检查流失客户、价格与替代品；确认原因前减少采购"
    if category == "补货关注品":
        return "结合最近3个月趋势和最低补货量确认采购"
    if category == "数据不足":
        return "补充销量或库存数据后再判断"
    if row["可用量可销月数"] < config.urgent_cover_months:
        return "可用库存偏低；确认在途订单能否按时到货"
    return "维持当前策略；按月复盘趋势与库存水位"


def _priority_score(products: pd.DataFrame) -> pd.Series:
    sales = products["月均销售金额(万元)"].fillna(0).rank(pct=True)
    growth_change = products["近3个月增长率"].abs().replace([np.inf, -np.inf], np.nan).fillna(0)
    growth = growth_change.rank(pct=True)
    inventory_deviation = products["库存覆盖缺口"].abs().fillna(0).rank(pct=True)
    stockout = products["断货次数"].fillna(0).rank(pct=True)
    customer = products["购买客户数"].fillna(0).rank(pct=True)
    score = sales * 35 + growth * 20 + inventory_deviation * 25 + stockout * 10 + customer * 10
    return score.round(0).clip(0, 100)


def _build_alerts(products: pd.DataFrame, config: AnalysisConfig) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in products.iterrows():
        identity = f"{row['品号']} · {row['品名']}".strip(" ·")
        if row["可用量可销月数"] < config.urgent_cover_months and row["月均销量"] > 0:
            rows.append(
                {
                    "级别": "高",
                    "类型": "供货风险",
                    "产品": identity,
                    "说明": f"可用库存仅覆盖 {row['可用量可销月数']:.1f} 个月",
                    "建议": "立即核对在途订单、到货日期和客户订单",
                    "经营优先分": row["经营优先分"],
                }
            )
        if row["合计可销月数"] >= row["目标可销月数"] * config.high_stock_multiple:
            rows.append(
                {
                    "级别": "高" if row["ABC分类"] == "C" else "中",
                    "类型": "库存积压",
                    "产品": identity,
                    "说明": f"库存覆盖 {row['合计可销月数']:.1f} 个月，目标 {row['目标可销月数']:.1f} 个月",
                    "建议": "暂停补货并制定客户定向去库存方案",
                    "经营优先分": row["经营优先分"],
                }
            )
        if pd.notna(row["近3个月增长率"]) and row["近3个月增长率"] <= config.decline_threshold:
            rows.append(
                {
                    "级别": "高" if row["ABC分类"] == "A" else "中",
                    "类型": "销量衰退",
                    "产品": identity,
                    "说明": f"近3个月较前3个月下降 {abs(row['近3个月增长率']):.1%}",
                    "建议": "检查大客户流失、季节性、价格和替代产品",
                    "经营优先分": row["经营优先分"],
                }
            )
        if row["断货次数"] > 0:
            rows.append(
                {
                    "级别": "高" if row["ABC分类"] == "A" else "中",
                    "类型": "历史断货",
                    "产品": identity,
                    "说明": f"统计期发生 {row['断货次数']:.0f} 次断货",
                    "建议": "复盘断货日期并校准安全库存",
                    "经营优先分": row["经营优先分"],
                }
            )
    if not rows:
        return pd.DataFrame(columns=["级别", "类型", "产品", "说明", "建议", "经营优先分"])
    alerts = pd.DataFrame(rows)
    severity = alerts["级别"].map({"高": 0, "中": 1, "低": 2}).fillna(3)
    alerts = alerts.assign(_severity=severity).sort_values(
        ["_severity", "经营优先分"], ascending=[True, False]
    )
    return alerts.drop(columns="_severity").reset_index(drop=True)


def analyze(source: ExcelLoadResult, config: AnalysisConfig | None = None) -> AnalysisResult:
    config = config or AnalysisConfig()
    raw = source.data.copy()
    mapping = source.columns
    products = pd.DataFrame(index=raw.index)
    products["_源数据行"] = raw.index.astype(int)

    product_id_col = mapping.get("product_id")
    product_name_col = mapping.get("product_name")
    products["品号"] = (
        raw[product_id_col].fillna("").astype(str).str.replace(r"\.0$", "", regex=True)
        if product_id_col
        else ""
    )
    products["品名"] = raw[product_name_col].fillna("").astype(str) if product_name_col else ""
    products["类型"] = raw[mapping.get("product_type")].fillna("").astype(str) if mapping.get("product_type") else ""
    products["规格"] = raw[mapping.get("spec")].fillna("").astype(str) if mapping.get("spec") else ""
    products["材料"] = raw[mapping.get("material")].fillna("").astype(str) if mapping.get("material") else ""

    monthly_columns = [column for _, column in mapping.monthly_sales]
    if monthly_columns:
        monthly = raw[monthly_columns].apply(pd.to_numeric, errors="coerce").fillna(0)
        derived_total = monthly.sum(axis=1)
        derived_average = monthly.mean(axis=1)
    else:
        monthly = pd.DataFrame(index=raw.index)
        derived_total = pd.Series(np.nan, index=raw.index)
        derived_average = pd.Series(np.nan, index=raw.index)

    monthly_output = monthly.copy()
    if not monthly_output.empty:
        monthly_output.columns = [
            month.strftime("%Y-%m") for month, _ in mapping.monthly_sales
        ]
    monthly_output.insert(0, "_源数据行", raw.index.astype(int))

    total_sales = _numeric(raw, mapping.get("total_sales_qty"))
    products["总销售数量"] = total_sales.where(total_sales.notna(), derived_total)
    avg_monthly = _numeric(raw, mapping.get("avg_monthly_qty"))
    products["月均销量"] = avg_monthly.where(avg_monthly.notna(), derived_average).fillna(0)

    window = min(config.recent_window, len(monthly_columns) // 2)
    if window > 0:
        recent = monthly.iloc[:, -window:].mean(axis=1)
        previous = monthly.iloc[:, -(window * 2) : -window].mean(axis=1)
        products["近3个月均量"] = recent
        products["前3个月均量"] = previous
        products["近3个月增长率"] = _safe_divide(recent, previous) - 1
        products["需求波动系数"] = _safe_divide(
            monthly.std(axis=1, ddof=0), monthly.mean(axis=1)
        )
    else:
        products["近3个月均量"] = np.nan
        products["前3个月均量"] = np.nan
        products["近3个月增长率"] = np.nan
        products["需求波动系数"] = np.nan

    price = _numeric(raw, mapping.get("reference_price"), default=0).fillna(0)
    products["参考售价"] = price
    sales_amount = _numeric(raw, mapping.get("monthly_sales_amount"))
    fallback_sales_amount = products["月均销量"] * price / 10_000
    products["月均销售金额(万元)"] = sales_amount.where(sales_amount.notna(), fallback_sales_amount).fillna(0)

    total_inventory = _numeric(raw, mapping.get("total_inventory"), default=0).fillna(0)
    total_available = _numeric(raw, mapping.get("total_available"), default=0).fillna(0)
    unfinished = _numeric(raw, mapping.get("unfinished_total"))
    if unfinished.isna().all():
        unfinished = (
            _numeric(raw, mapping.get("unfinished_qty"), default=0).fillna(0)
            + _numeric(raw, mapping.get("purchased_unrecorded"), default=0).fillna(0)
        )
    unfinished = unfinished.fillna(0)
    products["总在库数量"] = total_inventory
    products["总可用量"] = total_available
    products["合计未完成"] = unfinished

    available_cover = _numeric(raw, mapping.get("available_cover"))
    products["可用量可销月数"] = available_cover.where(
        available_cover.notna(), _safe_divide(total_available, products["月均销量"])
    )
    total_cover = _numeric(raw, mapping.get("total_cover"))
    fallback_cover = _safe_divide(total_available + unfinished, products["月均销量"])
    products["合计可销月数"] = total_cover.where(total_cover.notna(), fallback_cover)
    products["合计可销月数"] = products["合计可销月数"].replace([np.inf, -np.inf], np.nan)

    target = _numeric(raw, mapping.get("target_months"))
    products["目标可销月数"] = target.where(target > 0, config.default_target_months).fillna(
        config.default_target_months
    )
    products["库存覆盖缺口"] = products["合计可销月数"] - products["目标可销月数"]
    products["理论补货量"] = (
        (-products["库存覆盖缺口"]).clip(lower=0) * products["月均销量"]
    )
    moq = _numeric(raw, mapping.get("minimum_order_qty"), default=0).fillna(0)
    products["最低补货量"] = moq
    products["建议采购量"] = _round_to_moq(products["理论补货量"], moq)
    products["超储数量"] = (
        products["库存覆盖缺口"].clip(lower=0) * products["月均销量"]
    )
    products["缺口参考销售额"] = products["理论补货量"] * price
    products["超储参考销售额"] = products["超储数量"] * price

    total_amount = products["月均销售金额(万元)"].sum()
    products["销售贡献率"] = (
        products["月均销售金额(万元)"] / total_amount if total_amount > 0 else 0
    )
    order = products["销售贡献率"].sort_values(ascending=False).index
    cumulative = products.loc[order, "销售贡献率"].cumsum()
    contribution_sorted = products.loc[order, "销售贡献率"]
    cumulative_before = cumulative - contribution_sorted
    abc_sorted = pd.Series("C", index=order, dtype=object)
    abc_sorted.loc[cumulative_before < config.abc_b_threshold] = "B"
    abc_sorted.loc[cumulative_before < config.abc_a_threshold] = "A"
    abc = abc_sorted.reindex(products.index)
    products["ABC分类"] = abc

    sales_share = _numeric(raw, mapping.get("sales_share"))
    inventory_share = _numeric(raw, mapping.get("inventory_share"))
    fallback_sales_share = products["销售贡献率"]
    inventory_total = total_inventory.clip(lower=0).sum()
    fallback_inventory_share = (
        total_inventory.clip(lower=0) / inventory_total if inventory_total > 0 else 0
    )
    products["销售占比"] = sales_share.where(sales_share.notna(), fallback_sales_share)
    products["库存占比"] = inventory_share.where(inventory_share.notna(), fallback_inventory_share)
    products["销售库存错配指数"] = _safe_divide(products["销售占比"], products["库存占比"])

    customers = _numeric(raw, mapping.get("customer_count"), default=0).fillna(0)
    purchases = _numeric(raw, mapping.get("purchase_count"), default=0).fillna(0)
    products["购买客户数"] = customers
    products["购买次数"] = purchases
    products["客户复购频次"] = _safe_divide(purchases, customers)

    stockout = _numeric(raw, mapping.get("stockout_count"), default=0).fillna(0)
    products["断货次数"] = stockout
    period_count = max(len(monthly_columns), 12)
    products["断货率"] = stockout / period_count
    monthly_purchase = _numeric(raw, mapping.get("monthly_purchase_qty"), default=0).fillna(0)
    products["当月采购数量"] = monthly_purchase
    products["采购覆盖月数"] = _safe_divide(monthly_purchase, products["月均销量"])

    products["产品分层"] = products.apply(_classify, axis=1, config=config)
    products["经营优先分"] = _priority_score(products)
    products["建议动作"] = products.apply(_action, axis=1, config=config)

    products = products.replace([np.inf, -np.inf], np.nan)
    products = products.sort_values(["经营优先分", "月均销售金额(万元)"], ascending=[False, False])
    products = products.reset_index(drop=True)

    quality = list(source.warnings)
    zero_sales = int((products["月均销量"] <= 0).sum())
    negative_available = int((products["总可用量"] < 0).sum())
    missing_cover = int(products["合计可销月数"].isna().sum())
    if zero_sales:
        quality.append(f"{zero_sales} 个产品没有有效月均销量，无法可靠计算库存覆盖。")
    if negative_available:
        quality.append(f"{negative_available} 个产品的总可用量为负数，请检查预留、欠货或数据口径。")
    if missing_cover:
        quality.append(f"{missing_cover} 个产品缺少有效的合计可销月数。")
    if mapping.get("customer_count") and mapping.get("purchase_count"):
        equal_customer_purchase = (
            (products["购买客户数"] > 0)
            & (products["购买客户数"] == products["购买次数"])
        ).mean()
        if equal_customer_purchase > 0.8:
            quality.append("超过80%的产品“购买客户数”等于“购买次数”，建议核对两个字段是否重复导出。")

    summary: dict[str, float | int | str] = {
        "产品数": int(len(products)),
        "月均销售金额合计(万元)": round(float(products["月均销售金额(万元)"].sum()), 2),
        "目标以下产品数": int((products["库存覆盖缺口"] < 0).sum()),
        "高库存产品数": int((products["产品分层"] == "高库存促销品").sum()),
        "近3月增长产品数": int((products["近3个月增长率"] > 0).sum()),
        "近3月下降产品数": int((products["近3个月增长率"] < 0).sum()),
        "历史断货产品数": int((products["断货次数"] > 0).sum()),
        "缺口参考销售额": round(float(products["缺口参考销售额"].sum()), 2),
        "超储参考销售额": round(float(products["超储参考销售额"].sum()), 2),
        "数据质量提示数": len(quality),
    }

    return AnalysisResult(
        source=source,
        products=products,
        monthly_sales=monthly_output.reset_index(drop=True),
        summary=summary,
        alerts=_build_alerts(products, config),
        quality_messages=quality,
    )
