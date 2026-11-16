from __future__ import annotations

import json
import sqlite3
from typing import Any

from clinic_localizer.cohorts.protocol import ContractError, canonical_json, stable_hash, utc_now


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
    return {"scope": dict(scope), "issuances": issuances}
