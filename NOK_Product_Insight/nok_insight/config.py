from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisConfig:
    """User-adjustable business assumptions."""

    default_target_months: float = 7.7
    high_stock_multiple: float = 2.0
    recent_window: int = 3
    decline_threshold: float = -0.30
    growth_threshold: float = 0.20
    abc_a_threshold: float = 0.70
    abc_b_threshold: float = 0.90
    urgent_cover_months: float = 2.3

