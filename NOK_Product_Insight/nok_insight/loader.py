from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .columns import ColumnMap, header_score, map_columns


SUPPORTED_SUFFIXES = {".xlsx", ".xlsm", ".xls", ".csv"}


@dataclass
class ExcelLoadResult:
    path: Path
    sheet_name: str
    header_row: int
    data: pd.DataFrame
    columns: ColumnMap
    warnings: list[str] = field(default_factory=list)


def _unique_headers(values: list[object]) -> list[str]:
    seen: dict[str, int] = {}
    result: list[str] = []
    for index, value in enumerate(values, start=1):
        base = str(value).strip() if pd.notna(value) and str(value).strip() else f"列{index}"
        count = seen.get(base, 0)
        seen[base] = count + 1
        result.append(base if count == 0 else f"{base}_{count + 1}")
    return result


def _choose_sheet_and_header(path: Path, requested_sheet: str | None) -> tuple[str, int]:
    if path.suffix.lower() == ".csv":
        preview = pd.read_csv(path, header=None, nrows=20, dtype=object, encoding_errors="ignore")
        scores = [header_score(preview.iloc[row].tolist()) for row in range(len(preview))]
        return "CSV", int(max(range(len(scores)), key=scores.__getitem__))

    engine = "xlrd" if path.suffix.lower() == ".xls" else "openpyxl"
    best: tuple[float, str, int] | None = None
    with pd.ExcelFile(path, engine=engine) as book:
        sheet_names = [requested_sheet] if requested_sheet else book.sheet_names
        for sheet_name in sheet_names:
            preview = pd.read_excel(
                book,
                sheet_name=sheet_name,
                header=None,
                nrows=20,
                dtype=object,
            )
            for row_index in range(len(preview)):
                score = header_score(preview.iloc[row_index].tolist())
                candidate = (score, str(sheet_name), row_index)
                if best is None or candidate[0] > best[0]:
                    best = candidate
    if best is None:
        raise ValueError("工作簿中没有可读取的工作表。")
    return best[1], best[2]


def load_excel(path: str | Path, sheet_name: str | None = None) -> ExcelLoadResult:
    source = Path(path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"找不到文件：{source}")
    if source.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError("仅支持 .xlsx、.xlsm、.xls 和 .csv 文件。")

    selected_sheet, header_row = _choose_sheet_and_header(source, sheet_name)
    if source.suffix.lower() == ".csv":
        raw = pd.read_csv(source, header=None, dtype=object, encoding_errors="ignore")
    else:
        engine = "xlrd" if source.suffix.lower() == ".xls" else "openpyxl"
        raw = pd.read_excel(
            source,
            sheet_name=selected_sheet,
            header=None,
            dtype=object,
            engine=engine,
        )

    if header_row >= len(raw):
        raise ValueError("无法识别表头。")
    headers = _unique_headers(raw.iloc[header_row].tolist())
    frame = raw.iloc[header_row + 1 :].copy()
    frame.columns = headers
    frame = frame.dropna(how="all").reset_index(drop=True)
    frame = frame.dropna(axis=1, how="all")
    mapping = map_columns(frame.columns)

    warnings: list[str] = []
    if not mapping.get("product_id") and not mapping.get("product_name"):
        raise ValueError("未找到“品号/产品编号”或“品名/产品名称”字段。")
    if not mapping.monthly_sales and not mapping.get("avg_monthly_qty"):
        raise ValueError("未找到月度销售数量或月平均销售数量字段。")
    if len(mapping.monthly_sales) < 6:
        warnings.append(
            f"只识别到 {len(mapping.monthly_sales)} 个销售月份，增长趋势和波动指标可靠性较低。"
        )
    if not mapping.get("reference_price"):
        warnings.append("未识别到参考售价，缺口和超储金额将无法计算。")
    if not mapping.get("total_cover") and not mapping.get("total_available"):
        warnings.append("未识别到合计可销月数或总可用量，库存覆盖指标可能缺失。")
    if header_row > 0:
        warnings.append(f"程序自动将第 {header_row + 1} 行识别为表头。")

    return ExcelLoadResult(
        path=source,
        sheet_name=selected_sheet,
        header_row=header_row + 1,
        data=frame,
        columns=mapping,
        warnings=warnings,
    )
