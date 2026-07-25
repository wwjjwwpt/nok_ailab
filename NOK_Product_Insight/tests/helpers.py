from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook


def create_sample_workbook(path: Path) -> Path:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "GI采购分析"
    sheet.append(["NOK产品经营数据", None, None])
    sheet.append(["导出日期", "2026-04-01", None])
    headers = [
        "销售排名",
        "品号",
        "品名",
        "参考售价",
        "月平均销售金额(万元)",
        "2025年10月销售数量",
        "2025年11月销售数量",
        "2025年12月销售数量",
        "2026年1月销售数量",
        "2026年2月销售数量",
        "2026年3月销售数量",
        "月平均销售数量",
        "总在库数量",
        "总可用量",
        "合计未完成",
        "可用量可销售月",
        "合计可销月数",
        "参考值(单位:月)",
        "最低补货量",
        "销售占比",
        "库存占比",
        "购买客户数",
        "购买次数",
        "当月采购数量",
        "断货次数",
    ]
    sheet.append(headers)
    sheet.append(
        [
            1,
            "A-01",
            "增长款",
            10,
            10,
            100,
            100,
            100,
            200,
            200,
            200,
            150,
            150,
            150,
            75,
            1,
            1.5,
            4,
            100,
            0.67,
            0.25,
            50,
            80,
            200,
            1,
        ]
    )
    sheet.append(
        [
            2,
            "B-02",
            "积压款",
            20,
            5,
            200,
            200,
            200,
            100,
            100,
            100,
            150,
            1500,
            1200,
            300,
            8,
            10,
            4,
            50,
            0.33,
            0.75,
            10,
            10,
            0,
            0,
        ]
    )
    workbook.save(path)
    return path

