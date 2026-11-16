from __future__ import annotations

"""Applicability review for use scopes.

A use scope is approved only for the population, purpose and conditions that
have reliable labelled evidence *and* documented consent that names the
purpose.  Results are always reported per population group; a pooled or
overall pass never implies that every group passes.

All reasons are recorded, so a reviewer can trace why a range was retained,
narrowed, deferred or blocked.
"""

from typing import Any, Iterable, Mapping

from clinic_localizer.cohorts.protocol import DomainRecord, normalized_text, stable_hash
from clinic_localizer.statistics.stratified_reliability import (
    BLOCKED,
    CONSENT_ALLOWED,
    CONSENT_MISSING,
    CONSENT_WITHDRAWN,
    SPARSE,
    SUPPORTED,
    cohort_reliability,
    compare_strata,
)

RETAINED = "retained"
NARROWED = "narrowed"
DEFERRED = "deferred"
BLOCKED_DECISION = "blocked"

APPROVING_DECISIONS = (RETAINED, NARROWED)


def _evidence_digest(group: str, purpose: str, cohorts: Iterable[DomainRecord]) -> str:
    evidence = sorted(
        ({"cohort_id": record.record_id, "version": record.version,
          "fingerprint": record.fingerprint,
          "group": normalized_text(record.payload.get("population_group")),
          "consent_scope": record.payload.get("consent_scope")}
         for record in cohorts),
        key=lambda item: item["cohort_id"],
    )
    return stable_hash({"population_group": normalized_text(group),
                        "purposes": normalized_text(purpose), "evidence": evidence})


def _consent_reasons_entry(entry: dict[str, Any], purpose: str | None) -> list[dict[str, Any]]:
    if purpose is None or not normalized_text(purpose):
        return [{"code": "purpose_not_stated", "cohort_id": entry["cohort_id"],
                 "kind": "blocking",
                 "message": "no intended use was supplied; consent coverage cannot be verified"}]
    state = entry["consent_state"]
    if state == CONSENT_ALLOWED:
        return []
    if state == CONSENT_MISSING:
        return [{"code": "consent_missing", "cohort_id": entry["cohort_id"], "kind": "blocking",
                 "message": "consent is not documented; consent is not assumed"}]
    if state == CONSENT_WITHDRAWN:
        return [{"code": "consent_withdrawn", "cohort_id": entry["cohort_id"], "kind": "blocking",
                 "message": f"recorded consent does not cover intended use {purpose!r}",
                 "recorded_purposes": entry["consent_purposes"]}]
    return [{"code": "consent_not_assessed", "cohort_id": entry["cohort_id"], "kind": "blocking",
             "message": "consent coverage was not assessed"}]


def review_applicability(group: str, purpose: str | None, cohorts: Iterable[DomainRecord],
                         context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Decide whether a use scope can be retained, narrowed, deferred or blocked.

    ``cohorts`` are the records currently linked to the scope.  Each record is
    evaluated separately; the scope decision is derived from the set of fully
    supported cohorts, never from a pooled estimate.
    """

    context = context or {}
    cohort_list = list(cohorts)
    entries = [cohort_reliability(record, purpose=purpose, context=context) for record in cohort_list]
    group_key = normalized_text(group)

    reasons: list[dict[str, Any]] = []
    for entry in entries:
        if entry["population_group"] != group_key:
            entry["status"] = BLOCKED
            entry["blocking"].append({
                "code": "population_mismatch",
                "message": f"cohort group {entry['population_group']!r} does not match "
                           f"scope group {group_key!r}",
                "detail": {"scope_group": group_key, "cohort_group": entry["population_group"]}})
        for item in entry["blocking"]:
            reasons.append({"code": item["code"], "cohort_id": entry["cohort_id"],
                            "message": item["message"], "kind": "blocking"})
        for item in entry["limitations"]:
            reasons.append({"code": item["code"], "cohort_id": entry["cohort_id"],
                            "message": item["message"], "kind": "limitation"})

    reliable = [entry for entry in entries if entry["status"] == SUPPORTED]
    sparse = [entry for entry in entries if entry["status"] == SPARSE]
    blocked = [entry for entry in entries if entry["status"] == BLOCKED]

    consent_stated = bool(purpose and normalized_text(purpose))
    consent_reasons = [reason for entry in reliable for reason in _consent_reasons_entry(entry, purpose)]
    reasons.extend(consent_reasons)
    consent_blocked_ids = {reason["cohort_id"] for reason in consent_reasons}
    if consent_stated:
        approved = [entry for entry in reliable if entry["cohort_id"] not in consent_blocked_ids]
    else:
        approved = []

    represented_conditions = sorted({entry["condition_code"] for entry in entries if entry["condition_code"]})
    approved_conditions = sorted({entry["condition_code"] for entry in approved if entry["condition_code"]})
    excluded_conditions = sorted(set(represented_conditions) - set(approved_conditions))

    if not cohort_list:
        decision = DEFERRED
        reasons.append({"code": "no_linked_evidence", "cohort_id": None, "kind": "blocking",
                        "message": "no cohort evidence is linked; review is deferred"})
    elif approved and approved_conditions and set(approved_conditions) == set(represented_conditions):
        decision = RETAINED
        excluded_cohorts = [entry["cohort_id"] for entry in entries
                            if entry["cohort_id"] not in {item["cohort_id"] for item in approved}]
        for cohort_id in sorted(excluded_cohorts):
            reasons.append({"code": "cohort_excluded", "cohort_id": cohort_id, "kind": "limitation",
                            "message": "cohort is excluded from approval; its condition is still covered "
                                       "by another reliable cohort with matching consent"})
    elif approved and approved_conditions:
        decision = NARROWED
        for condition in excluded_conditions:
            reasons.append({"code": "condition_not_supported", "cohort_id": None, "kind": "limitation",
                            "message": f"condition {condition!r} is not covered by reliable labelled evidence "
                                       f"with matching consent"})
    elif reliable and not consent_stated:
        decision = DEFERRED
        reasons.append({"code": "purpose_not_stated", "cohort_id": None, "kind": "blocking",
                        "message": "intended use is not stated; the applicable range cannot be approved"})
    elif reliable and consent_blocked_ids:
        decision = BLOCKED_DECISION
        reasons.append({"code": "consent_blocks_range", "cohort_id": None, "kind": "blocking",
                        "message": "reliable cohorts exist but consent does not cover the intended use"})
    elif sparse:
        decision = DEFERRED
        reasons.append({"code": "evidence_sparse", "cohort_id": None, "kind": "blocking",
                        "message": "no cohort is reliable yet; approval is deferred until labelled evidence grows"})
    elif blocked:
        decision = BLOCKED_DECISION
        reasons.append({"code": "evidence_blocked", "cohort_id": None, "kind": "blocking",
                        "message": "every linked cohort is blocked by missing labels or missing identity"})
    else:
        decision = DEFERRED
        reasons.append({"code": "no_conclusion", "cohort_id": None, "kind": "blocking",
                        "message": "no supported conclusion is available for this scope"})

    if decision in APPROVING_DECISIONS and not approved_conditions:
        decision = DEFERRED
        reasons.append({"code": "condition_not_identified", "cohort_id": None, "kind": "blocking",
                        "message": "no supported cohort names a condition code; approval cannot be scoped"})

    summary = compare_strata(cohort_list, purpose=purpose, context=context)
    group_summary = summary["groups"].get(group_key)
    if group_summary is None:
        group_summary = {"group": group_key, "status": DEFERRED, "cohort_count": len(cohort_list)}

    effective_conditions = approved_conditions if decision in APPROVING_DECISIONS else []
    return {
        "scope_group": group_key,
        "purpose": purpose,
        "decision": decision,
        "consent_assessed": consent_stated,
        "approved_conditions": effective_conditions,
        "excluded_conditions": excluded_conditions,
        "represented_conditions": represented_conditions,
        "supported_cohort_ids": sorted(entry["cohort_id"] for entry in approved),
        "reliable_cohort_ids": sorted(entry["cohort_id"] for entry in reliable),
        "consent_excluded_cohort_ids": sorted(consent_blocked_ids - {None}),
        "sparse_cohort_ids": sorted(entry["cohort_id"] for entry in sparse),
        "blocked_cohort_ids": sorted(entry["cohort_id"] for entry in blocked),
        "cohorts": entries,
        "group_summary": group_summary,
        "reasons": reasons,
        "evidence_hash": _evidence_digest(group, purpose or "", cohort_list),
        "pooled_note": summary["pooled"]["note"],
        "effective_use": {"population_group": group_key, "purpose": purpose,
                          "conditions": effective_conditions},
        "conclusion": _conclusion(decision, group_key, purpose, effective_conditions,
                                  approved, sparse, blocked, consent_reasons, entries),
    }


def _conclusion(decision: str, group: str, purpose: str | None, approved_conditions: list[str],
                approved: list[dict[str, Any]], sparse: list[dict[str, Any]],
                blocked: list[dict[str, Any]], consent_reasons: list[dict[str, Any]],
                entries: list[dict[str, Any]]) -> str:
    if decision == RETAINED:
        return (f"retain {group!r} for {purpose!r}: {len(approved)} cohort(s) meet labelled evidence and "
                f"consent requirements for conditions {approved_conditions}")
    if decision == NARROWED:
        approved_ids = {entry["cohort_id"] for entry in approved}
        excluded = len([entry for entry in entries if entry["cohort_id"] not in approved_ids])
        return (f"narrow {group!r} for {purpose!r}: only conditions {approved_conditions} are covered by "
                f"reliable evidence with matching consent; {excluded} linked cohort(s) are excluded")
    if decision == DEFERRED:
        return (f"defer {group!r} for {purpose!r}: {len(sparse)} sparse and {len(blocked)} blocked cohort(s); "
                f"no group-wide conclusion is supported")
    detail = (f"{len(consent_reasons)} consent issue(s)" if consent_reasons
              else f"{len(blocked)} cohort(s) have missing labels or identity")
    return (f"block {group!r} for {purpose!r}: {detail}; missing evidence is not treated as approval")
