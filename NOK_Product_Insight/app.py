from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from nok_insight.config import AnalysisConfig
from nok_insight.exporter import export_analysis
from nok_insight.loader import load_excel
from nok_insight.metrics import analyze


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NOK 产品经营分析")
    parser.add_argument("file", nargs="?", help="启动界面后自动分析的 Excel 文件")
    parser.add_argument("--analyze", metavar="FILE", help="无界面分析指定 Excel")
    parser.add_argument("--output", metavar="XLSX", help="无界面模式导出结果")
    parser.add_argument("--target-months", type=float, default=7.7, help="缺少目标字段时采用的目标月数")
    parser.add_argument("--high-stock-multiple", type=float, default=2.0, help="高库存判定倍数")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.analyze:
        config = AnalysisConfig(
            default_target_months=args.target_months,
            high_stock_multiple=args.high_stock_multiple,
        )
        result = analyze(load_excel(args.analyze), config)
        payload = {
            "source": str(result.source.path),
            "sheet": result.source.sheet_name,
            "summary": result.summary,
            "quality_messages": result.quality_messages,
        }
        if args.output:
            payload["output"] = str(export_analysis(result, args.output))
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    from nok_insight.ui import run_app

    run_app(args.file)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"错误：{exc}", file=sys.stderr)
        raise SystemExit(1)

