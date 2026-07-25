"""NOK Product Insight - Excel-based product and inventory analytics."""

from .config import AnalysisConfig
from .loader import ExcelLoadResult, load_excel
from .metrics import AnalysisResult, analyze

__all__ = [
    "AnalysisConfig",
    "AnalysisResult",
    "ExcelLoadResult",
    "analyze",
    "load_excel",
]

