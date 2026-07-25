from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from typing import Iterable


ALIASES: dict[str, tuple[str, ...]] = {
    "rank": ("销售排名", "销量排名", "排名"),
    "product_id": ("品号", "产品编号", "物料编号", "SKU", "sku编码", "商品编码"),
    "product_name": ("品名", "产品名称", "商品名称", "物料名称"),
    "product_type": ("类型", "产品类型", "类别"),
    "spec": ("规格", "产品规格", "型号规格"),
    "material": ("材料", "材质"),
    "note": ("备注", "说明"),
    "reference_price": ("参考售价", "售价", "销售单价", "参考单价"),
    "monthly_sales_amount": ("月平均销售金额(万元)", "月平均销售金额", "月均销售金额", "月均销售额"),
    "total_sales_qty": ("总销售数量", "年度总销售数量", "12个月总销售数量", "2025年4月1日-2026年3月31日总销售数量"),
    "avg_monthly_qty": ("月平均销售数量", "月均销售数量", "平均月销量"),
    "total_inventory": ("总在库数量", "总库存数量", "库存总量"),
    "total_available": ("总可用量", "可用库存", "可用量"),
    "unfinished_qty": ("未完成数量", "在途数量", "未交数量"),
    "purchased_unrecorded": ("已采购未录入", "采购未入库", "已采购未入账"),
    "unfinished_total": ("合计未完成", "未完成合计", "在途合计"),
    "inventory_cover": ("库存可销售月", "库存覆盖月数"),
    "available_cover": ("可用量可销售月", "可用库存覆盖月数"),
    "unfinished_cover": ("未完成可销售月", "在途覆盖月数"),
    "total_cover": ("合计可销月数", "合计可销售月数", "总可销月数", "总覆盖月数"),
    "target_months": ("参考值(单位:月)", "目标可销月数", "目标库存月数", "目标月数"),
    "minimum_order_qty": ("最低补货量", "最小起订量", "最小采购量", "MOQ"),
    "sales_share": ("销售占比", "销售额占比"),
    "inventory_share": ("库存占比", "库存金额占比"),
    "last_inbound_date": ("最后一次进货时间", "最近入库时间"),
    "last_inbound_qty": ("最后一次进货数量", "最近入库数量"),
    "customer_count": ("购买客户数", "客户数", "购买客户数量"),
    "purchase_count": ("购买次数", "订单次数", "成交次数"),
    "monthly_purchase_qty": ("当月采购数量", "本月采购数量"),
    "monthly_purchase_amount": ("当月参考采购金额", "本月采购金额"),
    "recent_purchase_date": ("最近采购时间", "最后采购时间"),
    "recent_purchase_qty": ("最近采购数量", "最后采购数量"),
    "stockout_count": ("2025年4月1日-2026年3月31日断货次数", "断货次数", "缺货次数"),
}


def normalize_label(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).strip().lower()
    return re.sub(r"[\s_\-—–:：()（）/\\]+", "", text)


NORMALIZED_ALIASES = {
    key: tuple(normalize_label(alias) for alias in aliases)
    for key, aliases in ALIASES.items()
}


@dataclass
class ColumnMap:
    fields: dict[str, str] = field(default_factory=dict)
    monthly_sales: list[tuple[date, str]] = field(default_factory=list)
    unmatched_columns: list[str] = field(default_factory=list)

    def get(self, key: str) -> str | None:
        return self.fields.get(key)


def parse_month_column(label: object) -> date | None:
    raw = unicodedata.normalize("NFKC", str(label or "")).strip()
    compact = re.sub(r"\s+", "", raw)
    if not any(token in compact.lower() for token in ("销售", "销量", "出货", "sales")):
        return None
    patterns = (
        r"(?P<year>20\d{2})年(?P<month>1[0-2]|0?[1-9])月",
        r"(?P<year>20\d{2})[-/.](?P<month>1[0-2]|0?[1-9])",
        r"(?P<year>20\d{2})(?P<month>1[0-2]|0[1-9])",
    )
    for pattern in patterns:
        match = re.search(pattern, compact, flags=re.IGNORECASE)
        if match:
            return date(int(match.group("year")), int(match.group("month")), 1)
    return None


def map_columns(columns: Iterable[object]) -> ColumnMap:
    names = [str(column).strip() for column in columns]
    normalized = {name: normalize_label(name) for name in names}
    result = ColumnMap()
    used: set[str] = set()

    for field_name, aliases in NORMALIZED_ALIASES.items():
        exact = next(
            (name for name in names if normalized[name] in aliases and name not in used),
            None,
        )
        if exact is None:
            exact = next(
                (
                    name
                    for name in names
                    if name not in used
                    and any(
                        len(alias) >= 4
                        and (alias in normalized[name] or normalized[name] in alias)
                        for alias in aliases
                    )
                ),
                None,
            )
        if exact:
            result.fields[field_name] = exact
            used.add(exact)

    for name in names:
        parsed = parse_month_column(name)
        if parsed:
            result.monthly_sales.append((parsed, name))
            used.add(name)

    result.monthly_sales.sort(key=lambda item: item[0])
    result.unmatched_columns = [name for name in names if name not in used]
    return result


def header_score(values: Iterable[object]) -> float:
    labels = [str(value or "").strip() for value in values]
    mapping = map_columns(labels)
    recognized = len(mapping.fields)
    month_count = len(mapping.monthly_sales)
    nonempty = sum(bool(label and label.lower() != "nan") for label in labels)
    identity_bonus = 5 if mapping.get("product_id") or mapping.get("product_name") else 0
    return recognized * 2 + month_count * 1.5 + identity_bonus + min(nonempty, 20) * 0.05

