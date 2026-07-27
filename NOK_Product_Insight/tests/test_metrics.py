from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nok_insight.config import AnalysisConfig
from nok_insight.loader import load_excel
from nok_insight.metrics import analyze

from .helpers import create_sample_workbook


class MetricTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        path = create_sample_workbook(Path(self.temp_dir.name) / "sample.xlsx")
        self.result = analyze(
            load_excel(path),
            AnalysisConfig(default_target_months=4, high_stock_multiple=2),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _product(self, product_id: str):
        return self.result.products.loc[self.result.products["品号"] == product_id].iloc[0]

    def test_growth_and_replenishment_metrics(self) -> None:
        growth = self._product("A-01")
        self.assertAlmostEqual(growth["近3个月增长率"], 1.0)
        self.assertAlmostEqual(growth["理论补货量"], 375.0)
        self.assertAlmostEqual(growth["建议采购量"], 400.0)
        self.assertEqual(growth["产品分层"], "明星守供品")

    def test_overstock_and_decline_metrics(self) -> None:
        overstock = self._product("B-02")
        self.assertAlmostEqual(overstock["近3个月增长率"], -0.5)
        self.assertEqual(overstock["产品分层"], "高库存促销品")
        self.assertAlmostEqual(overstock["超储数量"], 900.0)
        self.assertAlmostEqual(overstock["超储参考销售额"], 18_000.0)

    def test_summary_and_alerts(self) -> None:
        self.assertEqual(self.result.summary["产品数"], 2)
        self.assertEqual(self.result.summary["目标以下产品数"], 1)
        self.assertEqual(self.result.summary["高库存产品数"], 1)
        self.assertFalse(self.result.alerts.empty)

    def test_monthly_sales_are_linked_to_each_product(self) -> None:
        growth = self._product("A-01")
        monthly = self.result.monthly_sales.loc[
            self.result.monthly_sales["_源数据行"] == growth["_源数据行"]
        ].iloc[0]
        self.assertEqual(monthly["2025-10"], 100)
        self.assertEqual(monthly["2026-03"], 200)


if __name__ == "__main__":
    unittest.main()
