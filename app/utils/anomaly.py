"""
Lightweight anomaly detection using Z-score analysis.

This module is intentionally dependency-free — no SQLAlchemy, no
Pydantic, no FastAPI.  It takes numbers in and returns results out.
This makes it trivial to unit test and easy to replace with a more
sophisticated model later.

The Z-score measures how many standard deviations a value is from
the mean.  Values beyond the threshold (default: 2.0) are flagged.
"""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class AnomalyResult:
    """
    Immutable result of an anomaly check on a single data point.

    Using a frozen dataclass here (instead of Pydantic) because this
    is an internal data structure, not an API contract.  Dataclasses
    are lighter — no validation overhead for data we already control.
    """

    value: int
    mean: float
    std_dev: float
    z_score: float
    is_anomaly: bool
    reason: str


def compute_z_scores(
    values: list[int],
    *,
    threshold: float = 2.0,
) -> list[AnomalyResult]:
    """
    Flag values whose Z-score exceeds *threshold*.

    Parameters
    ----------
    values:
        Raw observations (e.g. total_resources per player).
    threshold:
        Number of standard deviations beyond which a value is
        considered anomalous.  Defaults to 2.0.

    Returns
    -------
    A list of :class:`AnomalyResult`, one per input value,
    in the same order as the input.
    """
    n = len(values)
    if n < 2:
        return [
            AnomalyResult(
                value=v,
                mean=float(v),
                std_dev=0.0,
                z_score=0.0,
                is_anomaly=False,
                reason="insufficient data for analysis",
            )
            for v in values
        ]

    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    std_dev = math.sqrt(variance)

    results: list[AnomalyResult] = []
    for v in values:
        if std_dev == 0:
            z = 0.0
        else:
            z = (v - mean) / std_dev

        is_anomaly = abs(z) > threshold

        if is_anomaly:
            direction = "above" if z > 0 else "below"
            reason = (
                f"Total resources {v:,} is {abs(z):.1f} standard "
                f"deviations {direction} the mean ({mean:,.0f})"
            )
        else:
            reason = "within normal range"

        results.append(
            AnomalyResult(
                value=v,
                mean=round(mean, 2),
                std_dev=round(std_dev, 2),
                z_score=round(z, 2),
                is_anomaly=is_anomaly,
                reason=reason,
            )
        )

    return results