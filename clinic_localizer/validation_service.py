from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from clinic_localizer.cohorts.protocol import ContractError, Decision, DomainRecord, records_from_fixture, stable_hash
from clinic_localizer.evidence.registry import Repository
from clinic_localizer.governance.review_cycle import advance_for_outcome, decide
from clinic_localizer.statistics.cohort_guard import derive_context
from clinic_localizer.statistics.stratified_reliability import compare_strata
from clinic_localizer.submission.evidence_package import export_bundle, verify_bundle


class Application:
    def __init__(self, database: str | Path, context: Mapping[str, Any] | None = None):
        self.repository = Repository(database)
        self.context = dict(context or {})

    def ingest(self, record: DomainRecord) -> DomainRecord:
        current = self.repository.get_record(record.record_id)
        if current is None:
            self.repository.save_record(record)
            return record
        if current.fingerprint == record.fingerprint:
            return current
        replacement = DomainRecord(record.record_id, record.payload, current.state,
                                   current.version + 1, record.occurred_at, record.source)
        self.repository.save_record(replacement, expected_version=current.version)
        return replacement

    def process(self, record: DomainRecord) -> tuple[DomainRecord, Decision]:
        stored = self.ingest(record)
        context = dict(self.context)
        context.update(derive_context(stored, self.repository))
        decision = decide(stored, context)
        self.repository.save_decision(decision)
        advanced = advance_for_outcome(stored, decision)
        if advanced.fingerprint != stored.fingerprint:
            self.repository.save_record(advanced, expected_version=stored.version)
        return advanced, decision

    def run_fixture(self, fixture: Mapping[str, Any], output: str | Path) -> dict[str, Any]:
        records = records_from_fixture(fixture)
        fixture_hash = stable_hash(fixture)
        run_id = self.repository.begin_run(fixture_hash, len(records))
        completed = self.repository.completed_run(run_id)
        if completed is not None:
            return completed
        purpose = fixture.get("intended_use") or fixture.get("purpose")
        decisions: dict[str, Decision] = {}
        final_records: list[DomainRecord] = []
        for record in records:
            final_record, decision = self.process(record)
            final_records.append(final_record)
            decisions[record.record_id] = decision
        snapshot = self.repository.snapshot()
        if snapshot["chain_errors"]:
            raise ContractError("audit chain verification failed")
        applicability = compare_strata(final_records, purpose=purpose, context=self.context)
        scope_histories = []
        with self.repository.connect() as connection:
            scope_ids = [row[0] for row in connection.execute(
                "SELECT scope_id FROM use_scopes ORDER BY scope_id")]
        for scope_id in scope_ids:
            scope_histories.append(self.repository.scope_history(scope_id))
        manifest = export_bundle(output, final_records, decisions, snapshot, self.repository.event_rows(),
                                 purpose=purpose, applicability=applicability,
                                 scope_histories=scope_histories)
        result = {"run_id": run_id, "fixture_hash": fixture_hash, "records": len(final_records),
                  "decisions": len(decisions), "manifest": manifest, "snapshot": snapshot,
                  "supported_groups": applicability["supported_groups"],
                  "deferred_groups": applicability["deferred_groups"],
                  "blocked_groups": applicability["blocked_groups"],
                  "all_groups_supported": applicability["all_groups_supported"]}
        self.repository.finish_run(run_id, result)
        return result

    def inspect(self) -> dict[str, Any]:
        return {"snapshot": self.repository.snapshot(), "records": [record.__dict__ for record in self.repository.list_records()],
                "decisions": self.repository.decision_rows()}

    def stratified_review(self, purpose: str | None = None) -> dict[str, Any]:
        return self.repository.stratified_review(purpose=purpose, context=self.context)

    def scope_history(self, scope_id: str) -> dict[str, Any]:
        return self.repository.scope_history(scope_id)


def load_fixture(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read fixture: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError("fixture root must be an object")
    return value


def run(fixture_path: str | Path, database: str | Path, output: str | Path,
        context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return Application(database, context).run_fixture(load_fixture(fixture_path), output)


def verify(database: str | Path, output: str | Path) -> dict[str, Any]:
    repository = Repository(database)
    chain_errors = repository.verify_chain()
    bundle_errors = verify_bundle(output)
    return {"ok": not chain_errors and not bundle_errors, "chain_errors": chain_errors,
            "bundle_errors": bundle_errors, "snapshot": repository.snapshot()}
