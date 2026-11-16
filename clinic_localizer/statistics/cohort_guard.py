from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Iterable

from clinic_localizer.cohorts.protocol import DomainRecord, bounded, finite_number, normalized_text


def _optional(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(finite_number(value))
    except (ValueError, TypeError, ArithmeticError):
        return None
    return number if math.isfinite(number) else None


def confusion_counts(record: DomainRecord) -> dict[str, float]:
    """Counts over *labelled* records only.

    Unlabelled records (missingness) and absent sensitivity labels are never
    folded into the negative class or into a zero-sensitivity result.  When a
    label is absent the returned counts expose no information: callers get an
    interval spanning [0, 1] instead of a false negative signal.
    """

    size = _optional(record.payload.get("sample_size"))
    prevalence = _optional(record.payload.get("positive_rate"))
    sensitivity = _optional(record.payload.get("sensitivity"))
    specificity = _optional(record.payload.get("specificity"))
    missingness = _optional(record.payload.get("missingness"))
    if size is None or size <= 0 or prevalence is None or sensitivity is None or specificity is None:
        return {"tp": 0.0, "fn": 0.0, "tn": 0.0, "fp": 0.0, "labelled": 0.0}
    labelled = size * (1.0 - bounded(missingness if missingness is not None else 0.0))
    if labelled <= 0:
        return {"tp": 0.0, "fn": 0.0, "tn": 0.0, "fp": 0.0, "labelled": 0.0}
    prevalence = bounded(prevalence)
    sensitivity = bounded(sensitivity)
    specificity = bounded(specificity)
    positives = labelled * prevalence
    negatives = labelled - positives
    return {"tp": positives * sensitivity, "fn": positives * (1.0 - sensitivity),
            "tn": negatives * specificity, "fp": negatives * (1.0 - specificity),
            "labelled": labelled}


def wilson_interval(successes: float, total: float, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return 0.0, 1.0
    proportion = successes / total
    denominator = 1.0 + z * z / total
    center = (proportion + z * z / (2.0 * total)) / denominator
    margin = z * math.sqrt(proportion * (1.0 - proportion) / total + z * z / (4.0 * total * total)) / denominator
    return bounded(center - margin), bounded(center + margin)


def cohort_metrics(record: DomainRecord) -> dict[str, float]:
    counts = confusion_counts(record)
    sensitivity_interval = wilson_interval(counts["tp"], counts["tp"] + counts["fn"])
    specificity_interval = wilson_interval(counts["tn"], counts["tn"] + counts["fp"])
    missing = _optional(record.payload.get("missingness"))
    adverse = _optional(record.payload.get("adverse_events"))
    total = sum(counts[key] for key in ("tp", "fn", "tn", "fp"))
    # Absent safety data widens to the full range instead of implying zero harm.
    safety = bounded(adverse / max(1.0, total)) if adverse is not None and total > 0 else 1.0
    return {"sensitivity_low": sensitivity_interval[0], "sensitivity_high": sensitivity_interval[1],
            "specificity_low": specificity_interval[0], "specificity_high": specificity_interval[1],
            "missingness": bounded(missing) if missing is not None else 1.0, "safety_signal": safety}


def consent_allows(record: DomainRecord, purpose: str) -> bool:
    scopes = {item.strip() for item in normalized_text(record.payload.get("consent_scope", "")).replace(";", ",").split(",") if item.strip()}
    return purpose in scopes or "all" in scopes


def stratified_gap(records: Iterable[DomainRecord]) -> dict[str, float]:
    groups: dict[str, list[float]] = defaultdict(list)
    for record in records:
        group = normalized_text(record.payload.get("population_group", "unknown"))
        groups[group].append(cohort_metrics(record)["sensitivity_low"])
    means = {group: sum(values) / len(values) for group, values in groups.items()}
    gap = max(means.values()) - min(means.values()) if means else 0.0
    return {"group_count": float(len(means)), "sensitivity_gap": gap, "stability": bounded(1.0 - gap)}


def derive_context(record: DomainRecord, repository: Any) -> dict[str, float]:
    rows = repository.list_records() or [record]
    metrics = cohort_metrics(record)
    gap = stratified_gap(rows)
    consent = 1.0 if consent_allows(record, "validation") else 0.0
    return {"cohort_representativeness_weight": 0.6 + gap["stability"] * 0.5,
            "consent_coverage_weight": 0.5 + consent * 0.6,
            "performance_stability_weight": 0.6 + metrics["sensitivity_low"] * 0.5,
            "safety_signal_weight": 0.8 + metrics["safety_signal"] * 0.7,
            "transferability_weight": 0.6 + gap["stability"] * 0.5}
