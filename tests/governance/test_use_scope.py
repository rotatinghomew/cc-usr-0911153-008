from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from clinic_localizer.cohorts.protocol import ContractError, DomainRecord
from clinic_localizer.evidence.registry import Repository


class UseScopeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = Path(temporary.name) / "clinic.sqlite3"
        self.repository = Repository(self.database)
        self.record = DomainRecord("cohort-a", {"population_group": "group-a", "sample_size": 100})
        self.repository.save_record(self.record)
        self.repository.register_scope("scope-a", "group-a", "screening")

    def test_issued_evidence_stays_frozen_and_restrictions_append(self):
        self.repository.link_cohort("scope-a", "cohort-a")
        issued = self.repository.issue_scope("issue-a", "scope-a")
        self.assertEqual(self.repository.issue_scope("issue-a", "scope-a"), issued)
        self.repository.restrict_scope("restriction-a", "issue-a", "new evidence")
        changed = self.record.with_payload({"sample_size": 101})
        self.repository.save_record(changed, expected_version=1)
        history = Repository(self.database).scope_history("scope-a")
        self.assertEqual(history["issuances"][0]["evidence"][0]["version"], 1)
        self.assertEqual(history["issuances"][0]["restrictions"][0]["reason"], "new evidence")
        with self.assertRaisesRegex(ContractError, "already issued"):
            self.repository.link_cohort("scope-a", "cohort-a")

    def test_correction_before_issue_requires_refresh_and_population_matches(self):
        self.repository.link_cohort("scope-a", "cohort-a")
        self.repository.save_record(self.record.with_payload({"sample_size": 101}), expected_version=1)
        with self.assertRaisesRegex(ContractError, "changed before issue"):
            self.repository.issue_scope("issue-a", "scope-a")
        self.repository.link_cohort("scope-a", "cohort-a")
        self.assertEqual(self.repository.issue_scope("issue-a", "scope-a")["scope_id"], "scope-a")
        self.repository.save_record(DomainRecord("cohort-b", {"population_group": "group-b"}))
        with self.assertRaisesRegex(ContractError, "different population"):
            self.repository.link_cohort("scope-a", "cohort-b")
