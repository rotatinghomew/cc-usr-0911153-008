from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from clinic_localizer.cohorts.protocol import Decision, DomainRecord, stable_hash, utc_now
from clinic_localizer.statistics.stratified_reliability import compare_strata


def ensure_output(path: str | Path) -> Path:
    output = Path(path)
    output.mkdir(parents=True, exist_ok=True)
    return output


def write_json(path: Path, value: Any) -> str:
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
    path.write_text(body + "\n", encoding="utf-8")
    return stable_hash(value)


def write_records(path: Path, records: Iterable[DomainRecord], decisions: Mapping[str, Decision]) -> int:
    rows = []
    for record in records:
        decision = decisions.get(record.record_id)
        rows.append({"record_id": record.record_id, "state": record.state, "version": record.version,
                     "source": record.source, "fingerprint": record.fingerprint,
                     "outcome": decision.outcome if decision else "", "score": decision.score if decision else ""})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["record_id", "state", "version", "source", "fingerprint", "outcome", "score"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def write_rules(path: Path, decisions: Mapping[str, Decision]) -> int:
    count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["record_id", "code", "passed", "score", "severity", "message"])
        writer.writeheader()
        for record_id, decision in sorted(decisions.items()):
            for result in decision.rule_results:
                writer.writerow({"record_id": record_id, "code": result.code, "passed": result.passed,
                                 "score": result.score, "severity": result.severity, "message": result.message})
                count += 1
    return count


def build_summary(records: list[DomainRecord], decisions: Mapping[str, Decision], snapshot: Mapping[str, Any],
                  applicability: Mapping[str, Any] | None = None) -> dict[str, Any]:
    outcomes: dict[str, int] = {}
    for decision in decisions.values():
        outcomes[decision.outcome] = outcomes.get(decision.outcome, 0) + 1
    scores = [decision.score for decision in decisions.values()]
    summary = {"product": '东盟医疗人工智能本地化验证注册库', "entity": 'validation_cohort', "generated_at": utc_now(),
               "record_count": len(records), "decision_count": len(decisions), "outcomes": outcomes,
               "average_score": sum(scores) / len(scores) if scores else 0.0,
               "minimum_score": min(scores) if scores else 0.0, "maximum_score": max(scores) if scores else 0.0,
               "repository": snapshot}
    if applicability is not None:
        summary["applicability"] = {
            "purpose": applicability.get("purpose"),
            "supported_groups": applicability.get("supported_groups", []),
            "deferred_groups": applicability.get("deferred_groups", []),
            "blocked_groups": applicability.get("blocked_groups", []),
            "no_evidence_groups": applicability.get("no_evidence_groups", []),
            "all_groups_supported": applicability.get("all_groups_supported", False),
            "policy": applicability.get("policy"),
        }
        summary["approvable_range"] = {
            group: item["supported_conditions"]
            for group, item in applicability.get("groups", {}).items()
        }
    return summary


def write_strata(path: Path, applicability: Mapping[str, Any]) -> int:
    """Write one row per population group so review never relies on a pooled pass."""

    rows = []
    for group in sorted(applicability.get("groups", {})):
        item = applicability["groups"][group]
        rows.append({
            "population_group": group,
            "status": item["status"],
            "reliable": int(item["status"] == "supported"),
            "purpose": item.get("purpose") or "",
            "cohort_count": item["cohort_count"],
            "supported_conditions": ";".join(item["supported_conditions"]),
            "limitations": " | ".join(item["limitations"]),
            "conclusion": item["conclusion"],
        })
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["population_group", "status", "reliable", "purpose",
                                                    "cohort_count", "supported_conditions", "limitations", "conclusion"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def write_scope_ranges(path: Path, histories: Iterable[Mapping[str, Any]]) -> int:
    """Write one row per scope, including why its range is what it is."""

    rows = []
    for history in histories:
        scope = history["scope"]
        issuances = history.get("issuances") or []
        latest_issue = issuances[-1] if issuances else None
        reviews = history.get("reviews") or []
        latest_review = reviews[-1]["review"] if reviews else {}
        approved = (latest_issue or {}).get("approved_range") or {}
        restrictions = (latest_issue or {}).get("restrictions") or []
        rows.append({
            "scope_id": scope["scope_id"],
            "population_group": scope["population_group"],
            "purpose": scope["intended_use"],
            "decision": approved.get("decision") or latest_review.get("decision") or "unreviewed",
            "conditions": ";".join(approved.get("conditions") or []),
            "issued": int(bool(latest_issue)),
            "issue_id": (latest_issue or {}).get("issue_id", ""),
            "restriction_count": len(restrictions),
            "rationale": approved.get("reason") or latest_review.get("conclusion")
                         or "no applicability review recorded",
        })
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["scope_id", "population_group", "purpose", "decision",
                                                    "conditions", "issued", "issue_id", "restriction_count",
                                                    "rationale"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def export_bundle(output: str | Path, records: list[DomainRecord], decisions: Mapping[str, Decision],
                  snapshot: Mapping[str, Any], events: list[dict[str, Any]],
                  purpose: str | None = None,
                  applicability: Mapping[str, Any] | None = None,
                  scope_histories: Iterable[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    root = ensure_output(output)
    if applicability is None:
        applicability = compare_strata(records, purpose=purpose)
    summary = build_summary(records, decisions, snapshot, applicability)
    record_count = write_records(root / "records.csv", records, decisions)
    rule_count = write_rules(root / "rules.csv", decisions)
    strata_count = write_strata(root / "strata.csv", applicability)
    scope_count = write_scope_ranges(root / "scope-ranges.csv", scope_histories or [])
    summary_hash = write_json(root / "summary.json", summary)
    decision_hash = write_json(root / "decisions.json", [value.as_dict() for _, value in sorted(decisions.items())])
    applicability_hash = write_json(root / "applicability.json", applicability)
    event_hash = write_json(root / "audit-events.json", events)
    manifest = {"files": {"summary.json": summary_hash, "decisions.json": decision_hash,
                           "applicability.json": applicability_hash, "audit-events.json": event_hash},
                "record_rows": record_count, "rule_rows": rule_count, "strata_rows": strata_count,
                "scope_range_rows": scope_count, "created_at": utc_now()}
    manifest["manifest_hash"] = stable_hash(manifest)
    write_json(root / "manifest.json", manifest)
    return manifest


def verify_bundle(output: str | Path) -> list[str]:
    root = Path(output)
    errors: list[str] = []
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        return ["manifest.json is missing"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_manifest_hash = manifest.pop("manifest_hash", "")
    if stable_hash(manifest) != expected_manifest_hash:
        errors.append("manifest hash mismatch")
    for name, expected in manifest.get("files", {}).items():
        path = root / name
        if not path.is_file():
            errors.append(f"{name} is missing")
            continue
        value = json.loads(path.read_text(encoding="utf-8"))
        if stable_hash(value) != expected:
            errors.append(f"{name} hash mismatch")
    return errors
