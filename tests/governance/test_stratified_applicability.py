from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from clinic_localizer.cohorts.protocol import DomainRecord
from clinic_localizer.evidence.registry import Repository
from clinic_localizer.safety.applicability import (
    BLOCKED_DECISION,
    DEFERRED,
    NARROWED,
    RETAINED,
    review_applicability,
)
from clinic_localizer.statistics.stratified_reliability import (
    BLOCKED,
    NO_EVIDENCE,
    SPARSE,
    SUPPORTED,
    cohort_reliability,
    compare_strata,
    consent_state_for_payload,
)
from clinic_localizer.submission.evidence_package import export_bundle, write_strata


def payload(group: str, *, n: float = 1000, prevalence: float = 0.10,
            sensitivity: float = 0.90, specificity: float = 0.90,
            missingness: float | None = 0.05, consent: str = "validation,research",
            condition: str | None = "condition-1") -> dict:
    value = {
        "hospital_code": "hospital-1",
        "population_group": group,
        "sample_size": n,
        "positive_rate": prevalence,
        "consent_scope": consent,
        "terminology_version": "v1",
        "missingness": missingness,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "adverse_events": 3,
        "review_board": "board-1",
    }
    if condition is not None:
        value["condition_code"] = condition
    return value


def record(record_id: str, group: str, **kwargs) -> DomainRecord:
    return DomainRecord(record_id, payload(group, **kwargs))


class StratifiedReliabilityTests(unittest.TestCase):
    def test_reliable_group_is_supported_with_own_interval(self):
        entry = cohort_reliability(record("a1", "group-a"), purpose="validation")
        self.assertEqual(entry["status"], SUPPORTED)
        self.assertLess(entry["sensitivity_low"], entry["sensitivity_high"])
        self.assertLessEqual(entry["labelled_size"], entry["sample_size"])
        self.assertEqual(entry["unlabelled_treatment"], "excluded_from_denominator")

    def test_small_group_is_sparse_not_approved(self):
        entry = cohort_reliability(record("a2", "group-a", n=20, prevalence=0.05),
                                   purpose="validation")
        self.assertEqual(entry["status"], SPARSE)
        codes = {item["code"] for item in entry["limitations"]}
        self.assertIn("labelled_sample_below_minimum", codes)
        self.assertIn("positive_labels_below_minimum", codes)

    def test_missing_sensitivity_is_blocking_and_not_negative(self):
        raw = record("a3", "group-a", sensitivity=None)
        entry = cohort_reliability(raw, purpose="validation")
        self.assertEqual(entry["status"], BLOCKED)
        self.assertIn("sensitivity_label_missing", {item["code"] for item in entry["blocking"]})
        self.assertIsNone(entry["sensitivity"])

    def test_missingness_defaults_to_reported_not_zero(self):
        entry = cohort_reliability(record("a4", "group-a", missingness=None), purpose="validation")
        self.assertEqual(entry["status"], BLOCKED)
        self.assertIn("missingness_not_reported", {item["code"] for item in entry["blocking"]})
        self.assertEqual(entry["labelled_size"], 0.0)

    def test_high_missingness_cannot_become_a_negative_label(self):
        entry = cohort_reliability(record("a5", "group-a", n=1000, prevalence=0.3, missingness=0.9),
                                   purpose="validation")
        self.assertEqual(entry["unlabelled_treatment"], "excluded_from_denominator")
        self.assertAlmostEqual(entry["labelled_size"], 100.0)
        self.assertAlmostEqual(entry["expected_positives"], 30.0)
        self.assertEqual(entry["status"], SPARSE)

    def test_consent_purpose_is_distinguished_from_missing_consent(self):
        self.assertEqual(consent_state_for_payload({"consent_scope": "validation"}, "validation"), "allowed")
        self.assertEqual(consent_state_for_payload({"consent_scope": "research"}, "validation"), "withdrawn")
        self.assertEqual(consent_state_for_payload({}, "validation"), "missing")
        self.assertEqual(consent_state_for_payload({"consent_scope": "validation"}, None), "not_assessed")

    def test_group_comparison_never_uses_pooled_result_as_approval(self):
        records = [record("a1", "group-a"), record("b1", "group-b", n=30, prevalence=0.04)]
        comparison = compare_strata(records, purpose="validation")
        self.assertEqual(comparison["supported_groups"], ["group-a"])
        self.assertIn("group-b", comparison["deferred_groups"])
        self.assertFalse(comparison["all_groups_supported"])
        self.assertIn("not an approval basis", comparison["pooled"]["note"])

    def test_reliable_group_without_matching_consent_is_not_supported(self):
        comparison = compare_strata([record("a1", "group-a", consent="research")],
                                    purpose="validation")
        self.assertEqual(comparison["groups"]["group-a"]["status"], BLOCKED)
        self.assertEqual(comparison["supported_groups"], [])
        self.assertEqual(comparison["groups"]["group-a"]["consent_excluded_cohort_ids"], ["a1"])

    def test_missing_group_label_is_blocked(self):
        unlabelled = DomainRecord("x", payload("") | {"population_group": ""})
        comparison = compare_strata([unlabelled], purpose="validation")
        self.assertEqual(comparison["groups"]["unknown"]["status"], BLOCKED)
        reasons = comparison["groups"]["unknown"]["cohorts"][0]["blocking"]
        self.assertIn("population_group_missing", {item["code"] for item in reasons})
        self.assertEqual(comparison["supported_groups"], [])

    def test_declared_but_absent_groups_are_reported(self):
        comparison = compare_strata([record("a1", "group-a")], purpose="validation",
                                    context={"population_groups": ["group-a", "group-z"]})
        self.assertEqual(comparison["groups"]["group-z"]["status"], NO_EVIDENCE)
        self.assertIn("group-z", comparison["no_evidence_groups"])


class ApplicabilityTests(unittest.TestCase):
    def test_reliable_full_coverage_is_retained(self):
        review = review_applicability("group-a", "validation", [record("a1", "group-a")])
        self.assertEqual(review["decision"], RETAINED)
        self.assertEqual(review["approved_conditions"], ["condition-1"])

    def test_one_sparse_cohort_narrows_without_pooling(self):
        review = review_applicability(
            "group-a", "validation",
            [record("a1", "group-a", condition="condition-1"),
             record("a2", "group-a", n=40, prevalence=0.05, condition="condition-2")])
        self.assertEqual(review["decision"], NARROWED)
        self.assertEqual(review["approved_conditions"], ["condition-1"])
        self.assertIn("condition-2", review["excluded_conditions"])
        self.assertTrue(any(item["code"] == "condition_not_supported" for item in review["reasons"]))

    def test_consent_for_other_purpose_blocks_scope(self):
        review = review_applicability(
            "group-a", "validation",
            [record("a1", "group-a", consent="research")])
        self.assertEqual(review["decision"], BLOCKED_DECISION)
        self.assertEqual(review["approved_conditions"], [])
        self.assertTrue(any(item["code"] == "consent_withdrawn" for item in review["reasons"]))

    def test_absent_consent_is_not_assumed(self):
        review = review_applicability("group-a", "validation",
                                      [record("a1", "group-a", consent="")])
        self.assertEqual(review["decision"], BLOCKED_DECISION)
        self.assertTrue(any(item["code"] == "consent_missing" for item in review["reasons"]))

    def test_unstated_purpose_defers_even_with_reliable_labels(self):
        review = review_applicability("group-a", None, [record("a1", "group-a")])
        self.assertEqual(review["decision"], DEFERRED)
        self.assertFalse(review["consent_assessed"])

    def test_retained_group_records_excluded_cohort_rationale(self):
        review = review_applicability(
            "group-a", "validation",
            [record("a1", "group-a", condition="condition-1"),
             record("a2", "group-a", n=40, prevalence=0.05, condition="condition-1")])
        self.assertEqual(review["decision"], RETAINED)
        self.assertEqual(review["approved_conditions"], ["condition-1"])
        self.assertIn({"cohort_id": "a2", "kind": "limitation"},
                      [{"cohort_id": item["cohort_id"], "kind": item["kind"]}
                       for item in review["reasons"]])

    def test_group_pass_does_not_approve_other_groups(self):
        reviews = {
            "group-a": review_applicability("group-a", "validation", [record("a1", "group-a")]),
            "group-b": review_applicability("group-b", "validation",
                                            [record("b1", "group-b", n=40, prevalence=0.05)]),
        }
        self.assertEqual(reviews["group-a"]["decision"], RETAINED)
        self.assertEqual(reviews["group-b"]["decision"], DEFERRED)
        self.assertEqual(reviews["group-b"]["approved_conditions"], [])
        self.assertNotIn("group-a", reviews["group-b"]["approved_conditions"])

    def test_every_link_is_reasoned(self):
        review = review_applicability(
            "group-a", "validation",
            [record("a1", "group-a"),
             record("a2", "group-a", n=40, prevalence=0.05),
             record("a3", "group-a", sensitivity=None)])
        self.assertEqual(review["approved_conditions"], ["condition-1"])
        cohort_ids = {item["cohort_id"] for item in review["reasons"] if item["cohort_id"]}
        self.assertEqual(cohort_ids, {"a1", "a2", "a3"})
        self.assertTrue(all(item["kind"] in {"blocking", "limitation"} for item in review["reasons"]))


class ScopeLifecycleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = Path(temporary.name) / "governance.sqlite3"
        self.repository = Repository(self.database)

    def add(self, record_id: str, group: str, **kwargs) -> DomainRecord:
        value = record(record_id, group, **kwargs)
        self.repository.save_record(value)
        return value

    def save_change(self, record_id: str, **updates):
        current = self.repository.get_record(record_id)
        self.repository.save_record(current.with_payload(updates), expected_version=current.version)

    def test_checked_issue_refuses_unreliable_range(self):
        self.add("c1", "group-a", n=40, prevalence=0.05)
        self.repository.register_scope("s-a", "group-a", "validation")
        self.repository.link_cohort("s-a", "c1")
        result = self.repository.issue_scope_checked("i-a", "s-a", "r-a")
        self.assertFalse(result["issued"])
        self.assertEqual(result["review"]["decision"], DEFERRED)
        self.assertEqual(self.repository.scope_history("s-a")["issuances"], [])

    def test_checked_issue_records_narrowed_range(self):
        self.add("c1", "group-a", condition="condition-1")
        self.add("c2", "group-a", n=40, prevalence=0.05, condition="condition-2")
        self.repository.register_scope("s-a", "group-a", "validation")
        self.repository.link_cohort("s-a", "c1")
        self.repository.link_cohort("s-a", "c2")
        result = self.repository.issue_scope_checked("i-a", "s-a", "r-a")
        self.assertTrue(result["issued"])
        self.assertEqual(result["approved"]["decision"], NARROWED)
        self.assertEqual(result["approved"]["conditions"], ["condition-1"])
        history = self.repository.scope_history("s-a")
        self.assertEqual(history["issuances"][0]["approved_range"]["conditions"], ["condition-1"])

    def test_unissued_scope_is_reanalysed_after_label_correction(self):
        self.add("c1", "group-a", condition="condition-1")
        self.add("c2", "group-a", n=40, prevalence=0.05, condition="condition-2")
        self.repository.register_scope("s-a", "group-a", "validation")
        self.repository.link_cohort("s-a", "c1")
        self.repository.link_cohort("s-a", "c2")
        first = self.repository.recheck_scope("e1", "s-a", None, "rv1", "resubmission")
        self.assertEqual(first["decision"], NARROWED)
        self.assertFalse(first["changed"])  # first review establishes the pending range
        self.save_change("c2", sample_size=2000, missingness=0.02)
        second = self.repository.recheck_scope("e2", "s-a", None, "rv2", "label_correction")
        self.assertEqual(second["decision"], RETAINED)
        self.assertTrue(second["changed"])
        self.assertEqual(second["resulting_conditions"], ["condition-1", "condition-2"])
        self.assertEqual(self.repository.scope_history("s-a")["issuances"], [])

    def test_issued_scope_keeps_original_basis_and_records_restriction(self):
        self.add("c1", "group-a", condition="condition-1")
        self.repository.register_scope("s-a", "group-a", "validation")
        self.repository.link_cohort("s-a", "c1")
        issued = self.repository.issue_scope_checked("i-a", "s-a", "r-a")
        self.assertTrue(issued["issued"])
        original = self.repository.scope_history("s-a")["issuances"][0]
        self.save_change("c1", consent_scope="research")
        result = self.repository.recheck_scope("e1", "s-a", "i-a", "rv2", "consent_withdrawal")
        self.assertTrue(result["changed"])
        self.assertEqual(result["decision"], BLOCKED_DECISION)
        self.assertEqual(len(result["restrictions"]), 1)
        history = self.repository.scope_history("s-a")
        self.assertEqual(history["issuances"][0]["evidence_hash"], original["evidence_hash"])
        self.assertEqual(history["issuances"][0]["approved_range"]["conditions"], ["condition-1"])
        self.assertIn("consent_withdrawal", history["issuances"][0]["restrictions"][0]["reason"])
        self.assertEqual([(item["trigger"], item["decision"]) for item in history["reviews"]],
                         [("pre_issue", RETAINED), ("consent_withdrawal", BLOCKED_DECISION)])
        self.assertTrue(history["reevaluations"][0]["changed"])

    def test_correction_can_narrow_issued_conditions(self):
        self.add("c1", "group-a", condition="condition-1")
        self.add("c2", "group-a", condition="condition-2")
        self.repository.register_scope("s-a", "group-a", "validation")
        self.repository.link_cohort("s-a", "c1")
        self.repository.link_cohort("s-a", "c2")
        self.repository.issue_scope_checked("i-a", "s-a", "r-a")
        self.save_change("c2", missingness=0.85, sample_size=50)
        result = self.repository.recheck_scope("e1", "s-a", "i-a", "rv2", "label_correction")
        self.assertTrue(result["changed"])
        self.assertEqual(result["resulting_conditions"], ["condition-1"])
        history = self.repository.scope_history("s-a")
        self.assertEqual(len(history["issuances"][0]["restrictions"]), 1)
        self.assertIn("condition-2", history["issuances"][0]["restrictions"][0]["reason"])

    def test_recheck_all_reports_which_scopes_changed(self):
        self.add("c1", "group-a", condition="condition-1")
        self.add("d1", "group-b", condition="condition-1")
        self.repository.register_scope("s-a", "group-a", "validation")
        self.repository.register_scope("s-b", "group-b", "validation")
        self.repository.link_cohort("s-a", "c1")
        self.repository.link_cohort("s-b", "d1")
        self.repository.issue_scope_checked("i-a", "s-a", "r-a")
        self.repository.issue_scope_checked("i-b", "s-b", "r-b")
        self.save_change("c1", consent_scope="research")
        report = self.repository.recheck_all_scopes("consent_withdrawal", "bulk-1")
        self.assertEqual(report["changed_scope_ids"], ["s-a"])
        self.assertEqual(report["unchanged_scope_ids"], ["s-b"])
        self.assertTrue(all(item["issued"] for item in report["results"]))
        self.assertEqual(self.repository.scope_history("s-a")["issuances"][0]["approved_range"]["conditions"],
                         ["condition-1"])
        self.assertEqual(self.repository.scope_history("s-b")["issuances"][0]["restrictions"], [])

    def test_review_identity_cannot_be_overwritten(self):
        self.add("c1", "group-a")
        self.repository.register_scope("s-a", "group-a", "validation")
        self.repository.link_cohort("s-a", "c1")
        first = self.repository.review_scope("rv1", "s-a", "resubmission")
        self.assertEqual(self.repository.review_scope("rv1", "s-a", "resubmission"), first)
        self.save_change("c1", sample_size=1500)
        with self.assertRaisesRegex(Exception, "cannot be overwritten"):
            self.repository.review_scope("rv1", "s-a", "resubmission")


class SubmissionRangeTests(unittest.TestCase):
    def test_strata_artifact_has_one_row_per_group(self):
        records = [record("a1", "group-a"), record("b1", "group-b", n=30, prevalence=0.04)]
        applicability = compare_strata(records, purpose="validation")
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "strata.csv"
            count = write_strata(path, applicability)
            with path.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual(count, 2)
        by_group = {row["population_group"]: row for row in rows}
        self.assertEqual(by_group["group-a"]["status"], SUPPORTED)
        self.assertEqual(by_group["group-b"]["status"], SPARSE)
        self.assertEqual(by_group["group-b"]["reliable"], "0")

    def test_bundle_exposes_applicable_range(self):
        records = [record("a1", "group-a"), record("b1", "group-b", n=30, prevalence=0.04)]
        applicability = compare_strata(records, purpose="validation")
        with tempfile.TemporaryDirectory() as temporary:
            manifest = export_bundle(temporary, records, {}, {"counts": {}}, [],
                                     purpose="validation", applicability=applicability)
            summary = json.loads((Path(temporary) / "summary.json").read_text(encoding="utf-8"))
            stored = json.loads((Path(temporary) / "applicability.json").read_text(encoding="utf-8"))
        self.assertIn("applicability.json", manifest["files"])
        self.assertEqual(summary["applicability"]["supported_groups"], ["group-a"])
        self.assertEqual(summary["approvable_range"]["group-b"], [])
        self.assertFalse(summary["applicability"]["all_groups_supported"])
        self.assertEqual(stored["deferred_groups"], ["group-b"])


if __name__ == "__main__":
    unittest.main()
