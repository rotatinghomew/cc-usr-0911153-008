from __future__ import annotations

import unittest
from clinic_localizer.cohorts.protocol import DomainRecord
from clinic_localizer.statistics.cohort_guard import cohort_metrics, consent_allows, stratified_gap, wilson_interval


class CohortGuardTests(unittest.TestCase):
    def record(self, key, group="a"):
        return DomainRecord(key, {"hospital_code": "h", "population_group": group, "condition_code": "c", "sample_size": 200,
            "positive_rate": .2, "consent_scope": "validation,research", "terminology_version": "1", "missingness": .05,
            "sensitivity": .9, "specificity": .85, "adverse_events": 1, "review_board": "rb"})

    def test_intervals_and_consent(self):
        low, high = wilson_interval(90, 100)
        self.assertLess(low, high)
        self.assertTrue(consent_allows(self.record("a"), "validation"))
        self.assertGreater(cohort_metrics(self.record("a"))["sensitivity_low"], 0.0)

    def test_stratified_gap(self):
        self.assertEqual(stratified_gap([self.record("a", "x"), self.record("b", "y")])["group_count"], 2.0)

    def test_missing_labels_are_not_counted_as_negative(self):
        complete = self.record("a")
        missing = DomainRecord("b", dict(complete.payload) | {"missingness": 1.0})
        self.assertGreater(cohort_metrics(complete)["sensitivity_low"], 0.0)
        metrics = cohort_metrics(missing)
        self.assertEqual(metrics["sensitivity_low"], 0.0)
        self.assertEqual(metrics["sensitivity_high"], 1.0)

    def test_absent_sensitivity_is_not_treated_as_zero(self):
        record = self.record("a")
        without = DomainRecord("b", {key: value for key, value in record.payload.items()
                                     if key != "sensitivity"})
        self.assertEqual(cohort_metrics(without)["sensitivity_low"], 0.0)
        self.assertEqual(cohort_metrics(without)["sensitivity_high"], 1.0)
