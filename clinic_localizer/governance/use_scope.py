from __future__ import annotations

import json
import sqlite3
from typing import Any, Iterable, Mapping

from clinic_localizer.cohorts.protocol import ContractError, DomainRecord, canonical_json, stable_hash, utc_now
from clinic_localizer.safety.applicability import APPROVING_DECISIONS, review_applicability


POLICY_KEYS = ("min_labelled_sample", "min_positive_labels", "max_missingness",
               "max_sensitivity_interval_width")


def _policy_snapshot(context: Mapping[str, Any] | None) -> dict[str, Any]:
    context = context or {}
    return {key: context[key] for key in POLICY_KEYS if key in context}


def prepare_scopes(connection: sqlite3.Connection) -> None:
    connection.execute("""CREATE TABLE IF NOT EXISTS use_scopes(
        scope_id TEXT PRIMARY KEY, population_group TEXT NOT NULL, intended_use TEXT NOT NULL,
        submitted_at TEXT NOT NULL, UNIQUE(population_group,intended_use)
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS scope_evidence(
        scope_id TEXT NOT NULL, cohort_id TEXT NOT NULL, version INTEGER NOT NULL,
        record_fingerprint TEXT NOT NULL, PRIMARY KEY(scope_id,cohort_id),
        FOREIGN KEY(scope_id) REFERENCES use_scopes(scope_id)
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS scope_issuances(
        issue_id TEXT PRIMARY KEY, scope_id TEXT NOT NULL, evidence_hash TEXT NOT NULL,
        evidence_json TEXT NOT NULL, issued_at TEXT NOT NULL,
        FOREIGN KEY(scope_id) REFERENCES use_scopes(scope_id)
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS scope_restrictions(
        restriction_id TEXT PRIMARY KEY, issue_id TEXT NOT NULL, reason TEXT NOT NULL,
        recorded_at TEXT NOT NULL, FOREIGN KEY(issue_id) REFERENCES scope_issuances(issue_id)
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS scope_reviews(
        review_id TEXT PRIMARY KEY, scope_id TEXT NOT NULL, trigger TEXT NOT NULL,
        decision TEXT NOT NULL, evidence_hash TEXT NOT NULL, review_json TEXT NOT NULL,
        recorded_at TEXT NOT NULL, FOREIGN KEY(scope_id) REFERENCES use_scopes(scope_id)
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS scope_reevaluations(
        reevaluation_id TEXT PRIMARY KEY, review_id TEXT NOT NULL, issue_id TEXT,
        previous_decision TEXT, decision TEXT, changed INTEGER NOT NULL,
        detail_json TEXT NOT NULL, recorded_at TEXT NOT NULL,
        FOREIGN KEY(review_id) REFERENCES scope_reviews(review_id),
        FOREIGN KEY(issue_id) REFERENCES scope_issuances(issue_id)
    )""")
    connection.execute("""CREATE TABLE IF NOT EXISTS scope_issue_reviews(
        issue_id TEXT PRIMARY KEY, review_id TEXT NOT NULL, approved_json TEXT NOT NULL,
        recorded_at TEXT NOT NULL, FOREIGN KEY(issue_id) REFERENCES scope_issuances(issue_id),
        FOREIGN KEY(review_id) REFERENCES scope_reviews(review_id)
    )""")


def register_scope(connection: sqlite3.Connection, scope_id: str, group: str, intended_use: str) -> None:
    prepare_scopes(connection)
    if not all(isinstance(value, str) and value.strip() for value in (scope_id, group, intended_use)):
        raise ContractError("use scope requires population and purpose")
    row = connection.execute("SELECT population_group,intended_use FROM use_scopes WHERE scope_id=?", (scope_id,)).fetchone()
    if row:
        if (row[0], row[1]) != (group, intended_use):
            raise ContractError("scope identity cannot be reassigned")
        return
    connection.execute("INSERT INTO use_scopes VALUES(?,?,?,?)", (scope_id, group, intended_use, utc_now()))


def link_cohort(connection: sqlite3.Connection, scope_id: str, cohort_id: str) -> None:
    prepare_scopes(connection)
    scope = connection.execute("SELECT population_group FROM use_scopes WHERE scope_id=?", (scope_id,)).fetchone()
    evidence = connection.execute("SELECT * FROM records WHERE record_id=?", (cohort_id,)).fetchone()
    if scope is None or evidence is None:
        raise ContractError("scope and cohort must be registered")
    if str(json.loads(evidence["payload_json"]).get("population_group")) != scope[0]:
        raise ContractError("cohort belongs to a different population")
    if connection.execute("SELECT 1 FROM scope_issuances WHERE scope_id=?", (scope_id,)).fetchone():
        raise ContractError("already issued scope cannot change evidence")
    connection.execute("INSERT INTO scope_evidence VALUES(?,?,?,?) ON CONFLICT(scope_id,cohort_id) DO UPDATE SET version=excluded.version,record_fingerprint=excluded.record_fingerprint",
                       (scope_id, cohort_id, evidence["version"], evidence["fingerprint"]))


def issue_scope(connection: sqlite3.Connection, issue_id: str, scope_id: str) -> dict[str, Any]:
    prepare_scopes(connection)
    scope = connection.execute("SELECT * FROM use_scopes WHERE scope_id=?", (scope_id,)).fetchone()
    evidence = [dict(item) for item in connection.execute(
        "SELECT cohort_id,version,record_fingerprint FROM scope_evidence WHERE scope_id=? ORDER BY cohort_id", (scope_id,))]
    if scope is None or not evidence:
        raise ContractError("scope needs a registered cohort before issue")
    for row in evidence:
        current = connection.execute("SELECT version,fingerprint FROM records WHERE record_id=?", (row["cohort_id"],)).fetchone()
        if current is None or (current[0], current[1]) != (row["version"], row["record_fingerprint"]):
            raise ContractError("cohort evidence changed before issue")
    fingerprint = stable_hash({"scope_id": scope_id, "purpose": scope["intended_use"], "evidence": evidence})
    old = connection.execute("SELECT * FROM scope_issuances WHERE issue_id=?", (issue_id,)).fetchone()
    if old:
        if (old["scope_id"], old["evidence_hash"]) != (scope_id, fingerprint):
            raise ContractError("issued scope cannot be silently overwritten")
        return dict(old)
    connection.execute("INSERT INTO scope_issuances VALUES(?,?,?,?,?)",
                       (issue_id, scope_id, fingerprint, canonical_json(evidence), utc_now()))
    return dict(connection.execute("SELECT * FROM scope_issuances WHERE issue_id=?", (issue_id,)).fetchone())


def restrict_scope(connection: sqlite3.Connection, restriction_id: str, issue_id: str, reason: str) -> None:
    prepare_scopes(connection)
    if not reason.strip() or not connection.execute("SELECT 1 FROM scope_issuances WHERE issue_id=?", (issue_id,)).fetchone():
        raise ContractError("restriction requires issued scope and reason")
    previous = connection.execute("SELECT issue_id,reason FROM scope_restrictions WHERE restriction_id=?", (restriction_id,)).fetchone()
    if previous:
        if tuple(previous) != (issue_id, reason):
            raise ContractError("restriction identity conflict")
        return
    connection.execute("INSERT INTO scope_restrictions VALUES(?,?,?,?)",
                       (restriction_id, issue_id, reason, utc_now()))


def _load_cohorts(connection: sqlite3.Connection, scope_id: str) -> list[DomainRecord]:
    rows = connection.execute(
        "SELECT cohort_id FROM scope_evidence WHERE scope_id=? ORDER BY cohort_id", (scope_id,)).fetchall()
    cohorts: list[DomainRecord] = []
    for row in rows:
        stored = connection.execute("SELECT * FROM records WHERE record_id=?", (row["cohort_id"],)).fetchone()
        if stored is None:
            raise ContractError("linked cohort evidence is missing")
        cohorts.append(DomainRecord(record_id=stored["record_id"],
                                    payload=json.loads(stored["payload_json"]),
                                    state=stored["state"], version=stored["version"],
                                    occurred_at=stored["occurred_at"], source=stored["source"]))
    return cohorts


def _scope_purpose(connection: sqlite3.Connection, scope_id: str) -> tuple[str, str]:
    row = connection.execute("SELECT population_group,intended_use FROM use_scopes WHERE scope_id=?",
                             (scope_id,)).fetchone()
    if row is None:
        raise ContractError("unknown use scope")
    return str(row[0]), str(row[1])


def _issued_approval(connection: sqlite3.Connection, issue_id: str) -> dict[str, Any] | None:
    row = connection.execute("SELECT approved_json FROM scope_issue_reviews WHERE issue_id=?",
                             (issue_id,)).fetchone()
    return json.loads(row[0]) if row else None


def record_scope_review(connection: sqlite3.Connection, review_id: str, scope_id: str,
                        trigger: str, context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Evaluate a scope against current evidence and store the applicable range.

    Evaluation is idempotent for an unchanged evidence/trigger combination.
    A repeated review never silently replaces the recorded decision.
    """

    prepare_scopes(connection)
    group, purpose = _scope_purpose(connection, scope_id)
    if not trigger.strip():
        raise ContractError("review trigger is required")
    cohorts = _load_cohorts(connection, scope_id)
    policy = _policy_snapshot(context)
    review = review_applicability(group, purpose, cohorts, context or {})
    review["scope_id"] = scope_id
    review["trigger"] = trigger
    review["policy"] = policy
    evidence_hash = stable_hash({"scope_id": scope_id, "trigger": trigger,
                                 "policy": policy, "review": review["evidence_hash"]})
    previous = connection.execute("SELECT * FROM scope_reviews WHERE review_id=?", (review_id,)).fetchone()
    body = canonical_json(review)
    if previous:
        if previous["evidence_hash"] != evidence_hash or previous["review_json"] != body:
            raise ContractError("scope review identity cannot be overwritten")
        return json.loads(previous["review_json"])
    connection.execute("INSERT INTO scope_reviews VALUES(?,?,?,?,?,?,?)",
                       (review_id, scope_id, trigger, review["decision"], evidence_hash, body, utc_now()))
    row = connection.execute("SELECT * FROM scope_reviews WHERE review_id=?", (review_id,)).fetchone()
    return json.loads(row["review_json"])


def apply_scope_decision(connection: sqlite3.Connection, issue_id: str, scope_id: str,
                         review_id: str, approved: Mapping[str, Any]) -> None:
    """Attach a review to an issuance, recording what it actually approved."""

    prepare_scopes(connection)
    if connection.execute("SELECT 1 FROM scope_issue_reviews WHERE issue_id=?", (issue_id,)).fetchone():
        raise ContractError("issued scope already has a recorded applicability decision")
    connection.execute("INSERT INTO scope_issue_reviews VALUES(?,?,?,?)",
                       (issue_id, review_id, canonical_json(dict(approved)), utc_now()))


def issue_scope_checked(connection: sqlite3.Connection, issue_id: str, scope_id: str,
                        review_id: str, context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Issue a scope only for the range supported by reliable evidence.

    Deferred, blocked and narrowed groups produce a recorded review but no new
    issuance that would claim wider coverage.  Existing issuances are never
    overwritten.
    """

    prepare_scopes(connection)
    existing = connection.execute("SELECT * FROM scope_issuances WHERE issue_id=?", (issue_id,)).fetchone()
    if existing:
        return {"issued": False, "issuance": dict(existing), "review": None,
                "reason": "issuance already exists and is immutable"}
    review = record_scope_review(connection, review_id, scope_id, "pre_issue", context)
    if review["decision"] not in APPROVING_DECISIONS or not review["approved_conditions"]:
        return {"issued": False, "issuance": None, "review": review,
                "reason": f"applicability decision is {review['decision']}; no scope is issued"}
    issued = issue_scope(connection, issue_id, scope_id)
    approved = {"decision": review["decision"], "conditions": review["approved_conditions"],
                "population_group": review["scope_group"], "purpose": review["purpose"],
                "supported_cohort_ids": review["supported_cohort_ids"],
                "excluded_conditions": review["excluded_conditions"]}
    apply_scope_decision(connection, issue_id, scope_id, review_id, approved)
    return {"issued": True, "issuance": issued, "review": review, "approved": approved, "reason": "within supported range"}


def recheck_scope(connection: sqlite3.Connection, reevaluation_id: str, scope_id: str,
                  issue_id: str | None, review_id: str, trigger: str,
                  context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Re-evaluate a scope after resubmission, label correction or consent withdrawal.

    * Unissued scopes are re-evaluated so that their pending range reflects the
      corrected evidence.
    * Issued conclusions keep their original basis; the new review adds a
      restriction when the corrected evidence narrows or blocks the range.
    * The result records exactly which scopes changed and which did not.
    """

    prepare_scopes(connection)
    group, purpose = _scope_purpose(connection, scope_id)
    previous_issue = None
    previous_decision = None
    previous_conditions: list[str] = []
    original_basis_known = False
    if issue_id is not None:
        row = connection.execute("SELECT * FROM scope_issuances WHERE issue_id=?", (issue_id,)).fetchone()
        if row is None or row["scope_id"] != scope_id:
            raise ContractError("issuance does not belong to scope")
        previous_issue = dict(row)
        approved = _issued_approval(connection, issue_id)
        if approved is not None:
            original_basis_known = True
            previous_decision = approved["decision"]
            previous_conditions = list(approved["conditions"])

    review = record_scope_review(connection, review_id, scope_id, trigger, context)
    decision = review["decision"]
    conditions = list(review["approved_conditions"]) if decision in APPROVING_DECISIONS else []

    restrictions: list[dict[str, Any]] = []
    if previous_issue is not None:
        if decision not in APPROVING_DECISIONS:
            basis = previous_conditions or "unrecorded"
            reason = (f"reevaluation after {trigger}: {decision}; previously issued range "
                      f"{basis} is no longer supported")
            restrict_scope(connection, f"{reevaluation_id}-restriction", issue_id, reason)
            restrictions.append({"restriction_id": f"{reevaluation_id}-restriction", "reason": reason})
        elif not original_basis_known:
            reason = (f"reevaluation after {trigger}: original issuance recorded no applicability range; "
                      f"verified range is {decision} with conditions {conditions}")
            restrict_scope(connection, f"{reevaluation_id}-restriction", issue_id, reason)
            restrictions.append({"restriction_id": f"{reevaluation_id}-restriction", "reason": reason})
        elif set(conditions) != set(previous_conditions):
            removed = sorted(set(previous_conditions) - set(conditions))
            reason = (f"reevaluation after {trigger}: {decision}; removed conditions {removed}; "
                      f"remaining {conditions}; original issuance basis retained")
            restrict_scope(connection, f"{reevaluation_id}-restriction", issue_id, reason)
            restrictions.append({"restriction_id": f"{reevaluation_id}-restriction", "reason": reason})

    if previous_issue is None:
        prior = connection.execute(
            "SELECT review_json FROM scope_reviews WHERE scope_id=? AND review_id<>? "
            "ORDER BY recorded_at DESC, review_id DESC LIMIT 1", (scope_id, review_id)).fetchone()
        prior_review = json.loads(prior[0]) if prior else None
        prior_conditions = (list(prior_review.get("approved_conditions") or [])
                            if prior_review else [])
        prior_decision = prior_review.get("decision") if prior_review else None
        changed = bool(prior_review) and (
            prior_decision != decision or set(prior_conditions) != set(conditions))
        detail = {"previous_decision": prior_decision, "previous_conditions": prior_conditions,
                  "resulting_conditions": conditions, "trigger": trigger,
                  "review_decision": decision, "restrictions": restrictions}
        existing = connection.execute("SELECT * FROM scope_reevaluations WHERE reevaluation_id=?",
                                      (reevaluation_id,)).fetchone()
        if existing:
            if existing["detail_json"] != canonical_json(detail) or existing["decision"] != decision:
                raise ContractError("reevaluation identity conflict")
            detail = json.loads(existing["detail_json"])
            changed = bool(existing["changed"])
        else:
            connection.execute("INSERT INTO scope_reevaluations VALUES(?,?,?,?,?,?,?,?)",
                               (reevaluation_id, review_id, None, prior_decision, decision,
                                int(changed), canonical_json(detail), utc_now()))
    else:
        if not original_basis_known:
            # No original range was recorded, so there is nothing to compare
            # against; the scope is flagged through a limitation, not as changed.
            changed = False
        else:
            changed = (decision not in APPROVING_DECISIONS
                       or set(conditions) != set(previous_conditions))
        detail = {"previous_conditions": previous_conditions, "resulting_conditions": conditions,
                  "trigger": trigger, "review_decision": decision, "restrictions": restrictions,
                  "original_basis_recorded": original_basis_known}
        existing = connection.execute("SELECT * FROM scope_reevaluations WHERE reevaluation_id=?",
                                      (reevaluation_id,)).fetchone()
        if existing:
            if existing["detail_json"] != canonical_json(detail) or existing["decision"] != decision:
                raise ContractError("reevaluation identity conflict")
            detail = json.loads(existing["detail_json"])
            changed = bool(existing["changed"])
        else:
            connection.execute("INSERT INTO scope_reevaluations VALUES(?,?,?,?,?,?,?,?)",
                               (reevaluation_id, review_id, issue_id, previous_decision, decision,
                                int(changed), canonical_json(detail), utc_now()))

    return {
        "scope_id": scope_id,
        "group": group,
        "purpose": purpose,
        "trigger": trigger,
        "decision": decision,
        "changed": changed,
        "issued": previous_issue is not None,
        "previous_conditions": previous_conditions,
        "resulting_conditions": conditions,
        "retained_issue_id": issue_id if previous_issue is not None else None,
        "original_basis_recorded": original_basis_known,
        "review": review,
        "restrictions": restrictions,
        "reason": _reevaluation_reason(previous_issue is not None, changed, decision, trigger,
                                       previous_conditions, conditions, restrictions),
    }


def _reevaluation_reason(issued: bool, changed: bool, decision: str, trigger: str,
                         previous: list[str], current: list[str],
                         restrictions: list[dict[str, Any]]) -> str:
    if not issued:
        return (f"unissued scope re-evaluated after {trigger}; pending range is {decision} "
                f"with conditions {current}")
    if not changed:
        if restrictions:
            return (f"issued scope kept its original basis after {trigger}; a limitation was recorded "
                    f"for the reviewer")
        return f"issued scope unchanged after {trigger}; original basis retained"
    if set(current) != set(previous):
        return (f"issued scope narrowed after {trigger}; original basis retained with restriction; "
                f"conditions {previous} -> {current}")
    return f"issued scope no longer supported after {trigger}; original basis retained with restriction"


def recheck_all_scopes(connection: sqlite3.Connection, trigger: str, review_prefix: str,
                       changed_cohort_ids: Iterable[str] | None = None,
                       context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Re-evaluate every scope affected by a correction and report real changes.

    ``changed_cohort_ids`` limits the pass to scopes that link one of those
    cohorts.  Issued scopes keep their original basis; any narrowing or
    withdrawal is recorded as a restriction, never by overwriting history.
    """

    prepare_scopes(connection)
    wanted = {str(item) for item in changed_cohort_ids} if changed_cohort_ids is not None else None
    scopes = [row["scope_id"] for row in connection.execute("SELECT scope_id FROM use_scopes ORDER BY scope_id")]
    results: list[dict[str, Any]] = []
    for scope_id in scopes:
        linked = {row[0] for row in connection.execute(
            "SELECT cohort_id FROM scope_evidence WHERE scope_id=?", (scope_id,))}
        if wanted is not None and not (linked & wanted):
            continue
        issue_ids = [row["issue_id"] for row in connection.execute(
            "SELECT issue_id FROM scope_issuances WHERE scope_id=? ORDER BY issued_at, issue_id",
            (scope_id,))]
        if not issue_ids:
            review_id = f"{review_prefix}:{scope_id}:review"
            result = recheck_scope(connection, f"{review_prefix}:{scope_id}", scope_id, None,
                                   review_id, trigger, context)
            results.append({
                "scope_id": scope_id,
                "issued": False,
                "issue_id": None,
                "decision": result["decision"],
                "changed": result["changed"],
                "previous_conditions": result["previous_conditions"],
                "resulting_conditions": result["resulting_conditions"],
                "reason": result["reason"],
            })
            continue
        for issue_id in issue_ids:
            reevaluation_id = f"{review_prefix}:{scope_id}:{issue_id}"
            review_id = f"{review_prefix}:{scope_id}:{issue_id}:review"
            result = recheck_scope(connection, reevaluation_id, scope_id, issue_id, review_id,
                                   trigger, context)
            results.append({
                "scope_id": scope_id,
                "issued": True,
                "issue_id": issue_id,
                "decision": result["decision"],
                "changed": result["changed"],
                "previous_conditions": result["previous_conditions"],
                "resulting_conditions": result["resulting_conditions"],
                "reason": result["reason"],
            })
    return {
        "trigger": trigger,
        "scopes_reviewed": len({item["scope_id"] for item in results}),
        "changed_scope_ids": sorted({item["scope_id"] for item in results if item["changed"]}),
        "unchanged_scope_ids": sorted({item["scope_id"] for item in results if not item["changed"]}),
        "results": results,
    }


def scope_history(connection: sqlite3.Connection, scope_id: str) -> dict[str, Any]:
    prepare_scopes(connection)
    scope = connection.execute("SELECT * FROM use_scopes WHERE scope_id=?", (scope_id,)).fetchone()
    if scope is None:
        raise ContractError("unknown use scope")
    issuances = [dict(row) for row in connection.execute(
        "SELECT * FROM scope_issuances WHERE scope_id=? ORDER BY issued_at,issue_id", (scope_id,))]
    for item in issuances:
        item["evidence"] = json.loads(item.pop("evidence_json"))
        item["restrictions"] = [dict(row) for row in connection.execute(
            "SELECT * FROM scope_restrictions WHERE issue_id=? ORDER BY recorded_at,restriction_id", (item["issue_id"],))]
        approved = _issued_approval(connection, item["issue_id"])
        item["approved_range"] = approved
    reviews = [dict(row) for row in connection.execute(
        "SELECT * FROM scope_reviews WHERE scope_id=? ORDER BY recorded_at,review_id", (scope_id,))]
    for item in reviews:
        item["review"] = json.loads(item.pop("review_json"))
    reevaluations = [dict(row) for row in connection.execute(
        "SELECT * FROM scope_reevaluations WHERE review_id IN (SELECT review_id FROM scope_reviews WHERE scope_id=?) "
        "ORDER BY recorded_at,reevaluation_id", (scope_id,))]
    for item in reevaluations:
        item["detail"] = json.loads(item.pop("detail_json"))
        item["changed"] = bool(item["changed"])
    return {"scope": dict(scope), "issuances": issuances, "reviews": reviews,
            "reevaluations": reevaluations}
