from __future__ import annotations

"""Stratified evidence reliability.

Every population group's evidence stays separate.  A pooled estimate is
reported for orientation only and is never an approval basis for an
individual group.

Missing outcome labels are excluded from both numerator and denominator; they
are never imputed as negative test results.  An unlabelled record therefore
cannot lower an observed sensitivity nor be counted as a success.
"""

import math
from collections import defaultdict
from typing import Any, Iterable, Mapping

from clinic_localizer.cohorts.protocol import DomainRecord, bounded, finite_number, normalized_text
from clinic_localizer.statistics.cohort_guard import wilson_interval

SUPPORTED = "supported"
SPARSE = "sparse"
BLOCKED = "blocked"
NO_EVIDENCE = "no_evidence"

CONSENT_ALLOWED = "allowed"
CONSENT_WITHDRAWN = "withdrawn"
CONSENT_MISSING = "missing"
CONSENT_NOT_ASSESSED = "not_assessed"

DEFAULT_MIN_LABELLED_SAMPLE = 30.0
DEFAULT_MIN_POSITIVE_LABELS = 5.0
DEFAULT_MAX_MISSINGNESS = 0.20
DEFAULT_MAX_INTERVAL_WIDTH = 0.35


def optional_number(value: Any) -> float | None:
    """Return a finite number or ``None`` for missing/malformed labels."""

    if value is None or value == "":
        return None
    try:
        number = float(finite_number(value))
    except (ValueError, TypeError, ArithmeticError):
        return None
    return number if math.isfinite(number) else None


def as_rate(value: Any) -> float | None:
    """Interpret a proportion, accepting percentages as a convenience."""

    number = optional_number(value)
    if number is None:
        return None
    if number > 1.0:
        number = number / 100.0 if number <= 100.0 else 1.0
    return bounded(number)


def normalize_missingness(value: Any) -> float | None:
    """Normalize missingness without ever defaulting it to zero."""

    return as_rate(value)


def consent_purposes(payload: Mapping[str, Any]) -> set[str]:
    text = normalized_text(payload.get("consent_scope"))
    if not text:
        return set()
    for separator in (";", "|"):
        text = text.replace(separator, ",")
    return {item.strip() for item in text.split(",") if item.strip()}


def consent_state_for_payload(payload: Mapping[str, Any], purpose: str | None) -> str:
    """Classify consent for a purpose.

    * ``not_assessed`` - no intended use was supplied, so consent coverage is
      unknown rather than assumed.
    * ``missing`` - a purpose was supplied but the record documents no consent.
    * ``withdrawn`` - the record documents consent, but not for this purpose.
    """

    if purpose is None or not normalized_text(purpose):
        return CONSENT_NOT_ASSESSED
    raw = payload.get("consent_scope")
    if raw is None or not normalized_text(raw):
        return CONSENT_MISSING
    purposes = consent_purposes(payload)
    return CONSENT_ALLOWED if normalized_text(purpose) in purposes or "all" in purposes else CONSENT_WITHDRAWN


def _threshold(context: Mapping[str, Any], key: str, default: float) -> float:
    number = optional_number(context.get(key))
    return default if number is None else number


def _limitation(code: str, message: str, **detail: Any) -> dict[str, Any]:
    return {"code": code, "message": message, "detail": detail}


def cohort_reliability(record: DomainRecord, purpose: str | None = None,
                       context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Compute one cohort's label reliability.

    The verdict combines sample size, prevalence, label missingness and the
    resulting confidence interval.  Consent is recorded separately; the
    applicability review decides whether it permits the intended use.
    """

    context = context or {}
    payload = record.payload
    min_labelled = _threshold(context, "min_labelled_sample", DEFAULT_MIN_LABELLED_SAMPLE)
    min_positives = _threshold(context, "min_positive_labels", DEFAULT_MIN_POSITIVE_LABELS)
    max_missingness = _threshold(context, "max_missingness", DEFAULT_MAX_MISSINGNESS)
    max_width = _threshold(context, "max_sensitivity_interval_width", DEFAULT_MAX_INTERVAL_WIDTH)

    blocking: list[dict[str, Any]] = []
    limitations: list[dict[str, Any]] = []

    size = optional_number(payload.get("sample_size"))
    if size is None or size <= 0:
        blocking.append(_limitation(
            "sample_size_missing",
            "sample size is missing or zero; the cohort cannot support a conclusion"))
        size = 0.0

    missingness = normalize_missingness(payload.get("missingness"))
    if missingness is None:
        blocking.append(_limitation(
            "missingness_not_reported",
            "label missingness is not reported; unlabelled records cannot be counted as negative"))
        labelled = 0.0
    else:
        labelled = max(0.0, size * (1.0 - missingness))
        if missingness >= 1.0:
            blocking.append(_limitation(
                "no_labelled_outcomes",
                "no outcome labels are available; unlabelled records are not treated as negative",
                missingness=missingness))
        elif missingness > max_missingness:
            limitations.append(_limitation(
                "high_missingness",
                f"label missingness {missingness:.3f} exceeds the reliability limit {max_missingness:.3f}",
                missingness=missingness, limit=max_missingness,
                unlabelled=size - labelled))
        elif size - labelled > 0:
            limitations.append(_limitation(
                "unlabelled_excluded",
                f"{size - labelled:.3f} unlabelled records were excluded, not counted as negative",
                unlabelled=size - labelled))

    prevalence = as_rate(payload.get("positive_rate"))
    sensitivity = as_rate(payload.get("sensitivity"))
    specificity = as_rate(payload.get("specificity"))
    if prevalence is None:
        blocking.append(_limitation(
            "prevalence_missing",
            "positive rate (prevalence) is missing; sensitivity cannot be interpreted"))
    if sensitivity is None:
        blocking.append(_limitation(
            "sensitivity_label_missing",
            "sensitivity label is missing; missing labels are not treated as negative"))
    if specificity is None:
        blocking.append(_limitation(
            "specificity_label_missing",
            "specificity label is missing; missing labels are not treated as negative"))
    if payload.get("condition_code") in (None, ""):
        blocking.append(_limitation(
            "condition_code_missing",
            "condition code is missing; the cohort cannot be attributed to a covered condition"))

    effective_prevalence = prevalence if prevalence is not None else 0.0
    positives = labelled * effective_prevalence
    negatives = labelled * (1.0 - effective_prevalence)

    if sensitivity is not None and positives > 0:
        tp = positives * sensitivity
        fn = positives * (1.0 - sensitivity)
        sensitivity_low, sensitivity_high = wilson_interval(tp, positives)
    else:
        tp = fn = 0.0
        sensitivity_low, sensitivity_high = 0.0, 1.0

    if specificity is not None and negatives > 0:
        tn = negatives * specificity
        fp = negatives * (1.0 - specificity)
        specificity_low, specificity_high = wilson_interval(tn, negatives)
    else:
        tn = fp = 0.0
        specificity_low, specificity_high = 0.0, 1.0

    interval_width = sensitivity_high - sensitivity_low
    if not blocking:
        if labelled < min_labelled:
            limitations.append(_limitation(
                "labelled_sample_below_minimum",
                f"labelled sample {labelled:.3f} is below the reliability minimum {min_labelled:.3f}",
                labelled=labelled, minimum=min_labelled))
        if positives < min_positives:
            limitations.append(_limitation(
                "positive_labels_below_minimum",
                f"expected positive labels {positives:.3f} are below the reliability minimum "
                f"{min_positives:.3f} at prevalence {effective_prevalence:.3f}",
                positives=positives, minimum=min_positives, prevalence=effective_prevalence))
        if sensitivity is not None and interval_width > max_width:
            limitations.append(_limitation(
                "sensitivity_interval_too_wide",
                f"sensitivity interval width {interval_width:.3f} exceeds the reliability limit {max_width:.3f}",
                interval_width=interval_width, limit=max_width))

    sparse_codes = {"labelled_sample_below_minimum", "positive_labels_below_minimum",
                    "sensitivity_interval_too_wide", "high_missingness", "no_labelled_outcomes"}
    if blocking:
        status = BLOCKED
    elif any(item["code"] in sparse_codes for item in limitations):
        status = SPARSE
    else:
        status = SUPPORTED

    group_label = normalized_text(payload.get("population_group"))
    consent_state = consent_state_for_payload(payload, purpose)
    purpose_applicable = consent_state in (CONSENT_ALLOWED, CONSENT_NOT_ASSESSED)
    if status == SUPPORTED:
        conclusion = (
            f"group {group_label!r} has reliable labelled evidence: "
            f"labelled n={labelled:.1f}, prevalence={effective_prevalence:.3f}, "
            f"sensitivity interval [{sensitivity_low:.3f}, {sensitivity_high:.3f}]")
    elif status == SPARSE:
        conclusion = (
            f"group {group_label!r} evidence is too sparse to conclude: "
            f"labelled n={labelled:.1f}, expected positive labels={positives:.1f}, "
            f"sensitivity interval width={interval_width:.3f}")
    else:
        conclusion = (
            f"group {group_label!r} cannot be evaluated: "
            + "; ".join(item["message"] for item in blocking))

    return {
        "cohort_id": record.record_id,
        "population_group": group_label,
        "condition_code": normalized_text(payload.get("condition_code")) or None,
        "record_version": record.version,
        "record_fingerprint": record.fingerprint,
        "purpose": purpose,
        "sample_size": size,
        "labelled_size": labelled,
        "unlabelled_size": max(0.0, size - labelled),
        "missingness": missingness,
        "prevalence": prevalence,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "expected_positives": positives,
        "expected_negatives": negatives,
        "true_positives": tp,
        "false_negatives": fn,
        "true_negatives": tn,
        "false_positives": fp,
        "sensitivity_low": sensitivity_low,
        "sensitivity_high": sensitivity_high,
        "specificity_low": specificity_low,
        "specificity_high": specificity_high,
        "sensitivity_interval_width": interval_width,
        "consent_state": consent_state,
        "consent_purposes": sorted(consent_purposes(payload)),
        "purpose_applicable": purpose_applicable,
        "status": status,
        "blocking": blocking,
        "limitations": limitations,
        "conclusion": conclusion,
        "unlabelled_treatment": "excluded_from_denominator",
    }


def _group_summary(group: str, entries: list[dict[str, Any]], purpose: str | None) -> dict[str, Any]:
    reliable = [entry for entry in entries if entry["status"] == SUPPORTED]
    sparse = [entry for entry in entries if entry["status"] == SPARSE]
    blocked = [entry for entry in entries if entry["status"] == BLOCKED]
    usable = [entry for entry in reliable if entry["purpose_applicable"]]

    represented_conditions = sorted({entry["condition_code"] for entry in entries if entry.get("condition_code")})
    supported_conditions = sorted({entry["condition_code"] for entry in usable if entry.get("condition_code")})
    consent_excluded = [entry for entry in reliable if not entry["purpose_applicable"]]

    if usable:
        status = SUPPORTED
    elif reliable:
        # Reliable labels exist, but consent does not cover the stated purpose.
        status = BLOCKED
    elif sparse:
        status = SPARSE
    elif blocked:
        status = BLOCKED
    else:
        status = NO_EVIDENCE

    limitations = [f"{entry['cohort_id']}: {item['message']}"
                   for entry in entries for item in entry["blocking"] + entry["limitations"]]
    for entry in consent_excluded:
        limitations.append(f"{entry['cohort_id']}: reliable labels but consent does not cover "
                           f"intended use {purpose!r}")

    if status == SUPPORTED:
        conclusion = (f"group {group!r} has reliable labelled evidence usable for {purpose!r} from "
                      f"{len(usable)} cohort(s); covered conditions: {supported_conditions or 'unreported'}")
    elif status == SPARSE:
        conclusion = (f"group {group!r} evidence is sparse for {purpose!r}; conclusions are deferred "
                      f"until labelled sample and positive-label minimums are met")
    elif status == BLOCKED:
        conclusion = (f"group {group!r} cannot support {purpose!r}; missing labels and consent that does "
                      f"not cover the purpose are not treated as approval")
    else:
        conclusion = f"group {group!r} has no evidence"

    return {
        "group": group,
        "status": status,
        "purpose": purpose,
        "cohort_count": len(entries),
        "supported_cohort_ids": sorted(entry["cohort_id"] for entry in usable),
        "reliable_cohort_ids": sorted(entry["cohort_id"] for entry in reliable),
        "consent_excluded_cohort_ids": sorted(entry["cohort_id"] for entry in consent_excluded),
        "sparse_cohort_ids": sorted(entry["cohort_id"] for entry in sparse),
        "blocked_cohort_ids": sorted(entry["cohort_id"] for entry in blocked),
        "represented_conditions": represented_conditions,
        "supported_conditions": supported_conditions,
        "limitations": limitations,
        "conclusion": conclusion,
        "cohorts": entries,
    }


def compare_strata(records: Iterable[DomainRecord], purpose: str | None = None,
                   context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Compare label reliability by population group without pooling approvals.

    ``groups`` is the unit of conclusion.  The pooled estimate is descriptive
    only and explicitly must not be extrapolated to unsupported groups.
    """

    context = context or {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    all_entries: list[dict[str, Any]] = []
    for record in records:
        group = normalized_text(record.payload.get("population_group")) or "unknown"
        entry = cohort_reliability(record, purpose=purpose, context=context)
        if group == "unknown":
            entry["status"] = BLOCKED
            entry["blocking"] = list(entry["blocking"]) + [_limitation(
                "population_group_missing",
                "population group label is missing; evidence cannot be attributed to a group")]
            entry["conclusion"] = ("population group label is missing; "
                                   "evidence cannot be attributed to an approvable group")
        grouped[group].append(entry)
        all_entries.append(entry)

    summaries = {group: _group_summary(group, entries, purpose) for group, entries in grouped.items()}
    for raw_group in context.get("population_groups") or []:
        group = normalized_text(raw_group)
        if group and group not in summaries:
            missing = _group_summary(group, [], purpose)
            missing["limitations"] = ["no linked cohort evidence for this group"]
            summaries[group] = missing

    supported = sorted(group for group, item in summaries.items() if item["status"] == SUPPORTED)
    sparse = sorted(group for group, item in summaries.items() if item["status"] == SPARSE)
    blocked = sorted(group for group, item in summaries.items() if item["status"] == BLOCKED)
    no_evidence = sorted(group for group, item in summaries.items() if item["status"] == NO_EVIDENCE)

    total_tp = sum(entry["true_positives"] for entry in all_entries)
    total_positives = sum(entry["expected_positives"] for entry in all_entries
                          if entry["status"] != BLOCKED)
    pooled_low, pooled_high = wilson_interval(total_tp, total_positives) if total_positives else (0.0, 1.0)

    return {
        "purpose": purpose,
        "consent_assessed": bool(purpose and normalized_text(purpose)),
        "groups": summaries,
        "supported_groups": supported,
        "deferred_groups": sorted(set(sparse) | set(no_evidence)),
        "blocked_groups": blocked,
        "no_evidence_groups": no_evidence,
        "all_groups_supported": bool(summaries) and not (set(sparse) | set(blocked) | set(no_evidence)),
        "pooled": {
            "sensitivity_low": pooled_low,
            "sensitivity_high": pooled_high,
            "positive_labels": total_positives,
            "note": "pooled estimate is descriptive only; it is not an approval basis for any individual group",
        },
        "policy": "each group is concluded only from its own reliable labelled evidence",
    }


def group_conclusions(records: Iterable[DomainRecord], purpose: str | None = None,
                      context: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    comparison = compare_strata(records, purpose=purpose, context=context)
    return [comparison["groups"][group] for group in sorted(comparison["groups"])]


stratified_reliability = compare_strata
