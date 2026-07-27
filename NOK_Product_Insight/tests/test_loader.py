from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nok_insight.loader import load_excel
from nok_insight.columns import parse_month_column

from .helpers import create_sample_workbook


class LoaderTests(unittest.TestCase):
    def test_detects_sheet_header_and_month_columns(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = create_sample_workbook(Path(temp_dir) / "sample.xlsx")
            loaded = load_excel(path)
            self.assertEqual(loaded.sheet_name, "GI采购分析")
            self.assertEqual(loaded.header_row, 3)
            self.assertEqual(loaded.columns.get("product_id"), "品号")
            self.assertEqual(loaded.columns.get("total_cover"), "合计可销月数")
            self.assertEqual(len(loaded.columns.monthly_sales), 6)
            self.assertEqual(len(loaded.data), 2)

    def test_total_period_column_is_not_treated_as_a_month(self) -> None:
        self.assertIsNone(
            parse_month_column("2025年4月1日-2026年3月31日总销售数量")
        )


if __name__ == "__main__":
    unittest.main()
