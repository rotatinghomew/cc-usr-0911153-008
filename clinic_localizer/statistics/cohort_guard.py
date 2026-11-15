from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Iterable

from clinic_localizer.cohorts.protocol import DomainRecord, bounded, finite_number, normalized_text


def confusion_counts(record: DomainRecord) -> dict[str, float]:
    size = max(1.0, finite_number(record.payload.get("sample_size", 1.0)))
    prevalence = bounded(finite_number(record.payload.get("positive_rate", 0.0)))
    sensitivity = bounded(finite_number(record.payload.get("sensitivity", 0.0)))
    specificity = bounded(finite_number(record.payload.get("specificity", 0.0)))
    positives = size * prevalence
    negatives = size - positives
    return {"tp": positives * sensitivity, "fn": positives * (1.0 - sensitivity),
            "tn": negatives * specificity, "fp": negatives * (1.0 - specificity)}


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
    missing = bounded(finite_number(record.payload.get("missingness", 0.0)))
    adverse = max(0.0, finite_number(record.payload.get("adverse_events", 0.0)))
    return {"sensitivity_low": sensitivity_interval[0], "sensitivity_high": sensitivity_interval[1],
            "specificity_low": specificity_interval[0], "specificity_high": specificity_interval[1],
            "missingness": missing, "safety_signal": bounded(adverse / max(1.0, sum(counts.values())))}


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
