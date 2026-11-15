from __future__ import annotations

import math
from typing import Any, Callable, Mapping

from clinic_localizer.cohorts.protocol import DomainRecord, RuleResult, bounded, finite_number, normalized_text

RuleFunction = Callable[[DomainRecord, Mapping[str, Any]], RuleResult]

def _number(record: DomainRecord, field: str) -> float:
    value = record.payload.get(field)
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return finite_number(value)
    text = normalized_text(value)
    if not text:
        return 0.0
    try:
        return finite_number(text)
    except ValueError:
        return float(sum(ord(ch) for ch in text) % 101)

def _context_number(context: Mapping[str, Any], key: str, default: float) -> float:
    try:
        return finite_number(context.get(key, default))
    except ValueError:
        return default

def _result(code: str, value: float, threshold: float, higher_is_better: bool, message: str, evidence: dict[str, Any]) -> RuleResult:
    distance = (value - threshold) if higher_is_better else (threshold - value)
    passed = distance >= 0
    scale = max(1.0, abs(threshold))
    score = bounded(0.5 + distance / (2.0 * scale))
    severity = 'info' if passed else ('critical' if score < 0.2 else 'error')
    return RuleResult(code, passed, score, severity, message, evidence)

def check_hospital_code_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'hospital_code')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_hospital_code_presence_threshold', 10.333)
    return _result('check_hospital_code_presence', adjusted, threshold, True, 'validates hospital_code presence',
                   {'field': 'hospital_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_hospital_code_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'hospital_code')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_hospital_code_range_threshold', 12.667)
    return _result('check_hospital_code_range', adjusted, threshold, True, 'validates hospital_code range',
                   {'field': 'hospital_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_hospital_code_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'hospital_code')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_hospital_code_stability_threshold', 15.0)
    return _result('check_hospital_code_stability', adjusted, threshold, False, 'validates hospital_code stability',
                   {'field': 'hospital_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_hospital_code_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'hospital_code')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_hospital_code_freshness_threshold', 17.333)
    return _result('check_hospital_code_freshness', adjusted, threshold, True, 'validates hospital_code freshness',
                   {'field': 'hospital_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_hospital_code_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'hospital_code')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_hospital_code_coverage_threshold', 19.667)
    return _result('check_hospital_code_coverage', adjusted, threshold, True, 'validates hospital_code coverage',
                   {'field': 'hospital_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_hospital_code_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'hospital_code')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_hospital_code_consistency_threshold', 22.0)
    return _result('check_hospital_code_consistency', adjusted, threshold, False, 'validates hospital_code consistency',
                   {'field': 'hospital_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_hospital_code_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'hospital_code')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_hospital_code_risk_threshold', 24.333)
    return _result('check_hospital_code_risk', adjusted, threshold, True, 'validates hospital_code risk',
                   {'field': 'hospital_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_hospital_code_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'hospital_code')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_hospital_code_confidence_threshold', 26.667)
    return _result('check_hospital_code_confidence', adjusted, threshold, True, 'validates hospital_code confidence',
                   {'field': 'hospital_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_hospital_code_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'hospital_code')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_hospital_code_dependency_threshold', 29.0)
    return _result('check_hospital_code_dependency', adjusted, threshold, False, 'validates hospital_code dependency',
                   {'field': 'hospital_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_hospital_code_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'hospital_code')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_hospital_code_readiness_threshold', 31.333)
    return _result('check_hospital_code_readiness', adjusted, threshold, True, 'validates hospital_code readiness',
                   {'field': 'hospital_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_population_group_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'population_group')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_population_group_presence_threshold', 9.333)
    return _result('check_population_group_presence', adjusted, threshold, True, 'validates population_group presence',
                   {'field': 'population_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_population_group_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'population_group')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_population_group_range_threshold', 11.667)
    return _result('check_population_group_range', adjusted, threshold, False, 'validates population_group range',
                   {'field': 'population_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_population_group_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'population_group')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_population_group_stability_threshold', 14.0)
    return _result('check_population_group_stability', adjusted, threshold, True, 'validates population_group stability',
                   {'field': 'population_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_population_group_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'population_group')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_population_group_freshness_threshold', 16.333)
    return _result('check_population_group_freshness', adjusted, threshold, True, 'validates population_group freshness',
                   {'field': 'population_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_population_group_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'population_group')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_population_group_coverage_threshold', 18.667)
    return _result('check_population_group_coverage', adjusted, threshold, False, 'validates population_group coverage',
                   {'field': 'population_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_population_group_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'population_group')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_population_group_consistency_threshold', 21.0)
    return _result('check_population_group_consistency', adjusted, threshold, True, 'validates population_group consistency',
                   {'field': 'population_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_population_group_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'population_group')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_population_group_risk_threshold', 23.333)
    return _result('check_population_group_risk', adjusted, threshold, True, 'validates population_group risk',
                   {'field': 'population_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_population_group_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'population_group')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_population_group_confidence_threshold', 25.667)
    return _result('check_population_group_confidence', adjusted, threshold, False, 'validates population_group confidence',
                   {'field': 'population_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_population_group_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'population_group')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_population_group_dependency_threshold', 28.0)
    return _result('check_population_group_dependency', adjusted, threshold, True, 'validates population_group dependency',
                   {'field': 'population_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_population_group_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'population_group')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_population_group_readiness_threshold', 30.333)
    return _result('check_population_group_readiness', adjusted, threshold, True, 'validates population_group readiness',
                   {'field': 'population_group', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_condition_code_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'condition_code')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_condition_code_presence_threshold', 8.333)
    return _result('check_condition_code_presence', adjusted, threshold, False, 'validates condition_code presence',
                   {'field': 'condition_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_condition_code_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'condition_code')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_condition_code_range_threshold', 10.667)
    return _result('check_condition_code_range', adjusted, threshold, True, 'validates condition_code range',
                   {'field': 'condition_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_condition_code_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'condition_code')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_condition_code_stability_threshold', 13.0)
    return _result('check_condition_code_stability', adjusted, threshold, True, 'validates condition_code stability',
                   {'field': 'condition_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_condition_code_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'condition_code')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_condition_code_freshness_threshold', 15.333)
    return _result('check_condition_code_freshness', adjusted, threshold, False, 'validates condition_code freshness',
                   {'field': 'condition_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_condition_code_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'condition_code')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_condition_code_coverage_threshold', 17.667)
    return _result('check_condition_code_coverage', adjusted, threshold, True, 'validates condition_code coverage',
                   {'field': 'condition_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_condition_code_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'condition_code')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_condition_code_consistency_threshold', 20.0)
    return _result('check_condition_code_consistency', adjusted, threshold, True, 'validates condition_code consistency',
                   {'field': 'condition_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_condition_code_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'condition_code')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_condition_code_risk_threshold', 22.333)
    return _result('check_condition_code_risk', adjusted, threshold, False, 'validates condition_code risk',
                   {'field': 'condition_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_condition_code_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'condition_code')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_condition_code_confidence_threshold', 24.667)
    return _result('check_condition_code_confidence', adjusted, threshold, True, 'validates condition_code confidence',
                   {'field': 'condition_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_condition_code_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'condition_code')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_condition_code_dependency_threshold', 27.0)
    return _result('check_condition_code_dependency', adjusted, threshold, True, 'validates condition_code dependency',
                   {'field': 'condition_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_condition_code_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'condition_code')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_condition_code_readiness_threshold', 29.333)
    return _result('check_condition_code_readiness', adjusted, threshold, False, 'validates condition_code readiness',
                   {'field': 'condition_code', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sample_size_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sample_size')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_sample_size_presence_threshold', 31.667)
    return _result('check_sample_size_presence', adjusted, threshold, True, 'validates sample_size presence',
                   {'field': 'sample_size', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sample_size_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sample_size')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_sample_size_range_threshold', 9.667)
    return _result('check_sample_size_range', adjusted, threshold, True, 'validates sample_size range',
                   {'field': 'sample_size', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sample_size_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sample_size')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_sample_size_stability_threshold', 12.0)
    return _result('check_sample_size_stability', adjusted, threshold, False, 'validates sample_size stability',
                   {'field': 'sample_size', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sample_size_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sample_size')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_sample_size_freshness_threshold', 14.333)
    return _result('check_sample_size_freshness', adjusted, threshold, True, 'validates sample_size freshness',
                   {'field': 'sample_size', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sample_size_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sample_size')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_sample_size_coverage_threshold', 16.667)
    return _result('check_sample_size_coverage', adjusted, threshold, True, 'validates sample_size coverage',
                   {'field': 'sample_size', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sample_size_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sample_size')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_sample_size_consistency_threshold', 19.0)
    return _result('check_sample_size_consistency', adjusted, threshold, False, 'validates sample_size consistency',
                   {'field': 'sample_size', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sample_size_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sample_size')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_sample_size_risk_threshold', 21.333)
    return _result('check_sample_size_risk', adjusted, threshold, True, 'validates sample_size risk',
                   {'field': 'sample_size', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sample_size_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sample_size')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_sample_size_confidence_threshold', 23.667)
    return _result('check_sample_size_confidence', adjusted, threshold, True, 'validates sample_size confidence',
                   {'field': 'sample_size', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sample_size_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sample_size')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_sample_size_dependency_threshold', 26.0)
    return _result('check_sample_size_dependency', adjusted, threshold, False, 'validates sample_size dependency',
                   {'field': 'sample_size', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sample_size_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sample_size')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_sample_size_readiness_threshold', 28.333)
    return _result('check_sample_size_readiness', adjusted, threshold, True, 'validates sample_size readiness',
                   {'field': 'sample_size', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_positive_rate_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'positive_rate')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_positive_rate_presence_threshold', 30.667)
    return _result('check_positive_rate_presence', adjusted, threshold, True, 'validates positive_rate presence',
                   {'field': 'positive_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_positive_rate_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'positive_rate')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_positive_rate_range_threshold', 8.667)
    return _result('check_positive_rate_range', adjusted, threshold, False, 'validates positive_rate range',
                   {'field': 'positive_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_positive_rate_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'positive_rate')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_positive_rate_stability_threshold', 11.0)
    return _result('check_positive_rate_stability', adjusted, threshold, True, 'validates positive_rate stability',
                   {'field': 'positive_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_positive_rate_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'positive_rate')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_positive_rate_freshness_threshold', 13.333)
    return _result('check_positive_rate_freshness', adjusted, threshold, True, 'validates positive_rate freshness',
                   {'field': 'positive_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_positive_rate_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'positive_rate')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_positive_rate_coverage_threshold', 15.667)
    return _result('check_positive_rate_coverage', adjusted, threshold, False, 'validates positive_rate coverage',
                   {'field': 'positive_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_positive_rate_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'positive_rate')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_positive_rate_consistency_threshold', 18.0)
    return _result('check_positive_rate_consistency', adjusted, threshold, True, 'validates positive_rate consistency',
                   {'field': 'positive_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_positive_rate_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'positive_rate')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_positive_rate_risk_threshold', 20.333)
    return _result('check_positive_rate_risk', adjusted, threshold, True, 'validates positive_rate risk',
                   {'field': 'positive_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_positive_rate_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'positive_rate')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_positive_rate_confidence_threshold', 22.667)
    return _result('check_positive_rate_confidence', adjusted, threshold, False, 'validates positive_rate confidence',
                   {'field': 'positive_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_positive_rate_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'positive_rate')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_positive_rate_dependency_threshold', 25.0)
    return _result('check_positive_rate_dependency', adjusted, threshold, True, 'validates positive_rate dependency',
                   {'field': 'positive_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_positive_rate_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'positive_rate')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_positive_rate_readiness_threshold', 27.333)
    return _result('check_positive_rate_readiness', adjusted, threshold, True, 'validates positive_rate readiness',
                   {'field': 'positive_rate', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_consent_scope_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'consent_scope')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_consent_scope_presence_threshold', 29.667)
    return _result('check_consent_scope_presence', adjusted, threshold, False, 'validates consent_scope presence',
                   {'field': 'consent_scope', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_consent_scope_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'consent_scope')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_consent_scope_range_threshold', 32.0)
    return _result('check_consent_scope_range', adjusted, threshold, True, 'validates consent_scope range',
                   {'field': 'consent_scope', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_consent_scope_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'consent_scope')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_consent_scope_stability_threshold', 10.0)
    return _result('check_consent_scope_stability', adjusted, threshold, True, 'validates consent_scope stability',
                   {'field': 'consent_scope', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_consent_scope_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'consent_scope')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_consent_scope_freshness_threshold', 12.333)
    return _result('check_consent_scope_freshness', adjusted, threshold, False, 'validates consent_scope freshness',
                   {'field': 'consent_scope', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_consent_scope_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'consent_scope')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_consent_scope_coverage_threshold', 14.667)
    return _result('check_consent_scope_coverage', adjusted, threshold, True, 'validates consent_scope coverage',
                   {'field': 'consent_scope', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_consent_scope_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'consent_scope')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_consent_scope_consistency_threshold', 17.0)
    return _result('check_consent_scope_consistency', adjusted, threshold, True, 'validates consent_scope consistency',
                   {'field': 'consent_scope', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_consent_scope_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'consent_scope')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_consent_scope_risk_threshold', 19.333)
    return _result('check_consent_scope_risk', adjusted, threshold, False, 'validates consent_scope risk',
                   {'field': 'consent_scope', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_consent_scope_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'consent_scope')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_consent_scope_confidence_threshold', 21.667)
    return _result('check_consent_scope_confidence', adjusted, threshold, True, 'validates consent_scope confidence',
                   {'field': 'consent_scope', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_consent_scope_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'consent_scope')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_consent_scope_dependency_threshold', 24.0)
    return _result('check_consent_scope_dependency', adjusted, threshold, True, 'validates consent_scope dependency',
                   {'field': 'consent_scope', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_consent_scope_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'consent_scope')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_consent_scope_readiness_threshold', 26.333)
    return _result('check_consent_scope_readiness', adjusted, threshold, False, 'validates consent_scope readiness',
                   {'field': 'consent_scope', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_terminology_version_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'terminology_version')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_terminology_version_presence_threshold', 28.667)
    return _result('check_terminology_version_presence', adjusted, threshold, True, 'validates terminology_version presence',
                   {'field': 'terminology_version', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_terminology_version_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'terminology_version')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_terminology_version_range_threshold', 31.0)
    return _result('check_terminology_version_range', adjusted, threshold, True, 'validates terminology_version range',
                   {'field': 'terminology_version', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_terminology_version_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'terminology_version')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_terminology_version_stability_threshold', 9.0)
    return _result('check_terminology_version_stability', adjusted, threshold, False, 'validates terminology_version stability',
                   {'field': 'terminology_version', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_terminology_version_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'terminology_version')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_terminology_version_freshness_threshold', 11.333)
    return _result('check_terminology_version_freshness', adjusted, threshold, True, 'validates terminology_version freshness',
                   {'field': 'terminology_version', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_terminology_version_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'terminology_version')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_terminology_version_coverage_threshold', 13.667)
    return _result('check_terminology_version_coverage', adjusted, threshold, True, 'validates terminology_version coverage',
                   {'field': 'terminology_version', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_terminology_version_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'terminology_version')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_terminology_version_consistency_threshold', 16.0)
    return _result('check_terminology_version_consistency', adjusted, threshold, False, 'validates terminology_version consistency',
                   {'field': 'terminology_version', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_terminology_version_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'terminology_version')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_terminology_version_risk_threshold', 18.333)
    return _result('check_terminology_version_risk', adjusted, threshold, True, 'validates terminology_version risk',
                   {'field': 'terminology_version', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_terminology_version_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'terminology_version')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_terminology_version_confidence_threshold', 20.667)
    return _result('check_terminology_version_confidence', adjusted, threshold, True, 'validates terminology_version confidence',
                   {'field': 'terminology_version', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_terminology_version_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'terminology_version')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_terminology_version_dependency_threshold', 23.0)
    return _result('check_terminology_version_dependency', adjusted, threshold, False, 'validates terminology_version dependency',
                   {'field': 'terminology_version', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_terminology_version_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'terminology_version')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_terminology_version_readiness_threshold', 25.333)
    return _result('check_terminology_version_readiness', adjusted, threshold, True, 'validates terminology_version readiness',
                   {'field': 'terminology_version', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_missingness_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'missingness')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_missingness_presence_threshold', 27.667)
    return _result('check_missingness_presence', adjusted, threshold, True, 'validates missingness presence',
                   {'field': 'missingness', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_missingness_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'missingness')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_missingness_range_threshold', 30.0)
    return _result('check_missingness_range', adjusted, threshold, False, 'validates missingness range',
                   {'field': 'missingness', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_missingness_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'missingness')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_missingness_stability_threshold', 8.0)
    return _result('check_missingness_stability', adjusted, threshold, True, 'validates missingness stability',
                   {'field': 'missingness', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_missingness_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'missingness')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_missingness_freshness_threshold', 10.333)
    return _result('check_missingness_freshness', adjusted, threshold, True, 'validates missingness freshness',
                   {'field': 'missingness', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_missingness_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'missingness')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_missingness_coverage_threshold', 12.667)
    return _result('check_missingness_coverage', adjusted, threshold, False, 'validates missingness coverage',
                   {'field': 'missingness', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_missingness_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'missingness')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_missingness_consistency_threshold', 15.0)
    return _result('check_missingness_consistency', adjusted, threshold, True, 'validates missingness consistency',
                   {'field': 'missingness', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_missingness_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'missingness')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_missingness_risk_threshold', 17.333)
    return _result('check_missingness_risk', adjusted, threshold, True, 'validates missingness risk',
                   {'field': 'missingness', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_missingness_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'missingness')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_missingness_confidence_threshold', 19.667)
    return _result('check_missingness_confidence', adjusted, threshold, False, 'validates missingness confidence',
                   {'field': 'missingness', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_missingness_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'missingness')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_missingness_dependency_threshold', 22.0)
    return _result('check_missingness_dependency', adjusted, threshold, True, 'validates missingness dependency',
                   {'field': 'missingness', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_missingness_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'missingness')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_missingness_readiness_threshold', 24.333)
    return _result('check_missingness_readiness', adjusted, threshold, True, 'validates missingness readiness',
                   {'field': 'missingness', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sensitivity_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sensitivity')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_sensitivity_presence_threshold', 26.667)
    return _result('check_sensitivity_presence', adjusted, threshold, False, 'validates sensitivity presence',
                   {'field': 'sensitivity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sensitivity_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sensitivity')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_sensitivity_range_threshold', 29.0)
    return _result('check_sensitivity_range', adjusted, threshold, True, 'validates sensitivity range',
                   {'field': 'sensitivity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sensitivity_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sensitivity')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_sensitivity_stability_threshold', 31.333)
    return _result('check_sensitivity_stability', adjusted, threshold, True, 'validates sensitivity stability',
                   {'field': 'sensitivity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sensitivity_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sensitivity')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_sensitivity_freshness_threshold', 9.333)
    return _result('check_sensitivity_freshness', adjusted, threshold, False, 'validates sensitivity freshness',
                   {'field': 'sensitivity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sensitivity_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sensitivity')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_sensitivity_coverage_threshold', 11.667)
    return _result('check_sensitivity_coverage', adjusted, threshold, True, 'validates sensitivity coverage',
                   {'field': 'sensitivity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sensitivity_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sensitivity')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_sensitivity_consistency_threshold', 14.0)
    return _result('check_sensitivity_consistency', adjusted, threshold, True, 'validates sensitivity consistency',
                   {'field': 'sensitivity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sensitivity_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sensitivity')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_sensitivity_risk_threshold', 16.333)
    return _result('check_sensitivity_risk', adjusted, threshold, False, 'validates sensitivity risk',
                   {'field': 'sensitivity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sensitivity_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sensitivity')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_sensitivity_confidence_threshold', 18.667)
    return _result('check_sensitivity_confidence', adjusted, threshold, True, 'validates sensitivity confidence',
                   {'field': 'sensitivity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sensitivity_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sensitivity')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_sensitivity_dependency_threshold', 21.0)
    return _result('check_sensitivity_dependency', adjusted, threshold, True, 'validates sensitivity dependency',
                   {'field': 'sensitivity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sensitivity_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sensitivity')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_sensitivity_readiness_threshold', 23.333)
    return _result('check_sensitivity_readiness', adjusted, threshold, False, 'validates sensitivity readiness',
                   {'field': 'sensitivity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_specificity_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'specificity')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_specificity_presence_threshold', 25.667)
    return _result('check_specificity_presence', adjusted, threshold, True, 'validates specificity presence',
                   {'field': 'specificity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_specificity_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'specificity')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_specificity_range_threshold', 28.0)
    return _result('check_specificity_range', adjusted, threshold, True, 'validates specificity range',
                   {'field': 'specificity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_specificity_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'specificity')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_specificity_stability_threshold', 30.333)
    return _result('check_specificity_stability', adjusted, threshold, False, 'validates specificity stability',
                   {'field': 'specificity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_specificity_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'specificity')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_specificity_freshness_threshold', 8.333)
    return _result('check_specificity_freshness', adjusted, threshold, True, 'validates specificity freshness',
                   {'field': 'specificity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_specificity_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'specificity')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_specificity_coverage_threshold', 10.667)
    return _result('check_specificity_coverage', adjusted, threshold, True, 'validates specificity coverage',
                   {'field': 'specificity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_specificity_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'specificity')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_specificity_consistency_threshold', 13.0)
    return _result('check_specificity_consistency', adjusted, threshold, False, 'validates specificity consistency',
                   {'field': 'specificity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_specificity_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'specificity')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_specificity_risk_threshold', 15.333)
    return _result('check_specificity_risk', adjusted, threshold, True, 'validates specificity risk',
                   {'field': 'specificity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_specificity_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'specificity')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_specificity_confidence_threshold', 17.667)
    return _result('check_specificity_confidence', adjusted, threshold, True, 'validates specificity confidence',
                   {'field': 'specificity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_specificity_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'specificity')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_specificity_dependency_threshold', 20.0)
    return _result('check_specificity_dependency', adjusted, threshold, False, 'validates specificity dependency',
                   {'field': 'specificity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_specificity_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'specificity')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_specificity_readiness_threshold', 22.333)
    return _result('check_specificity_readiness', adjusted, threshold, True, 'validates specificity readiness',
                   {'field': 'specificity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_adverse_events_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'adverse_events')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_adverse_events_presence_threshold', 24.667)
    return _result('check_adverse_events_presence', adjusted, threshold, True, 'validates adverse_events presence',
                   {'field': 'adverse_events', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_adverse_events_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'adverse_events')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_adverse_events_range_threshold', 27.0)
    return _result('check_adverse_events_range', adjusted, threshold, False, 'validates adverse_events range',
                   {'field': 'adverse_events', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_adverse_events_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'adverse_events')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_adverse_events_stability_threshold', 29.333)
    return _result('check_adverse_events_stability', adjusted, threshold, True, 'validates adverse_events stability',
                   {'field': 'adverse_events', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_adverse_events_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'adverse_events')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_adverse_events_freshness_threshold', 31.667)
    return _result('check_adverse_events_freshness', adjusted, threshold, True, 'validates adverse_events freshness',
                   {'field': 'adverse_events', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_adverse_events_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'adverse_events')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_adverse_events_coverage_threshold', 9.667)
    return _result('check_adverse_events_coverage', adjusted, threshold, False, 'validates adverse_events coverage',
                   {'field': 'adverse_events', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_adverse_events_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'adverse_events')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_adverse_events_consistency_threshold', 12.0)
    return _result('check_adverse_events_consistency', adjusted, threshold, True, 'validates adverse_events consistency',
                   {'field': 'adverse_events', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_adverse_events_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'adverse_events')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_adverse_events_risk_threshold', 14.333)
    return _result('check_adverse_events_risk', adjusted, threshold, True, 'validates adverse_events risk',
                   {'field': 'adverse_events', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_adverse_events_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'adverse_events')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_adverse_events_confidence_threshold', 16.667)
    return _result('check_adverse_events_confidence', adjusted, threshold, False, 'validates adverse_events confidence',
                   {'field': 'adverse_events', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_adverse_events_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'adverse_events')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_adverse_events_dependency_threshold', 19.0)
    return _result('check_adverse_events_dependency', adjusted, threshold, True, 'validates adverse_events dependency',
                   {'field': 'adverse_events', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_adverse_events_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'adverse_events')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_adverse_events_readiness_threshold', 21.333)
    return _result('check_adverse_events_readiness', adjusted, threshold, True, 'validates adverse_events readiness',
                   {'field': 'adverse_events', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_review_board_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'review_board')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_review_board_presence_threshold', 23.667)
    return _result('check_review_board_presence', adjusted, threshold, False, 'validates review_board presence',
                   {'field': 'review_board', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_review_board_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'review_board')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_review_board_range_threshold', 26.0)
    return _result('check_review_board_range', adjusted, threshold, True, 'validates review_board range',
                   {'field': 'review_board', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_review_board_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'review_board')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_review_board_stability_threshold', 28.333)
    return _result('check_review_board_stability', adjusted, threshold, True, 'validates review_board stability',
                   {'field': 'review_board', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_review_board_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'review_board')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_review_board_freshness_threshold', 30.667)
    return _result('check_review_board_freshness', adjusted, threshold, False, 'validates review_board freshness',
                   {'field': 'review_board', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_review_board_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'review_board')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_review_board_coverage_threshold', 8.667)
    return _result('check_review_board_coverage', adjusted, threshold, True, 'validates review_board coverage',
                   {'field': 'review_board', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_review_board_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'review_board')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_review_board_consistency_threshold', 11.0)
    return _result('check_review_board_consistency', adjusted, threshold, True, 'validates review_board consistency',
                   {'field': 'review_board', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_review_board_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'review_board')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_review_board_risk_threshold', 13.333)
    return _result('check_review_board_risk', adjusted, threshold, False, 'validates review_board risk',
                   {'field': 'review_board', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_review_board_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'review_board')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_review_board_confidence_threshold', 15.667)
    return _result('check_review_board_confidence', adjusted, threshold, True, 'validates review_board confidence',
                   {'field': 'review_board', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_review_board_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'review_board')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_review_board_dependency_threshold', 18.0)
    return _result('check_review_board_dependency', adjusted, threshold, True, 'validates review_board dependency',
                   {'field': 'review_board', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_review_board_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'review_board')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_review_board_readiness_threshold', 20.333)
    return _result('check_review_board_readiness', adjusted, threshold, False, 'validates review_board readiness',
                   {'field': 'review_board', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

RULES: tuple[RuleFunction, ...] = (
    check_hospital_code_presence,
    check_hospital_code_range,
    check_hospital_code_stability,
    check_hospital_code_freshness,
    check_hospital_code_coverage,
    check_hospital_code_consistency,
    check_hospital_code_risk,
    check_hospital_code_confidence,
    check_hospital_code_dependency,
    check_hospital_code_readiness,
    check_population_group_presence,
    check_population_group_range,
    check_population_group_stability,
    check_population_group_freshness,
    check_population_group_coverage,
    check_population_group_consistency,
    check_population_group_risk,
    check_population_group_confidence,
    check_population_group_dependency,
    check_population_group_readiness,
    check_condition_code_presence,
    check_condition_code_range,
    check_condition_code_stability,
    check_condition_code_freshness,
    check_condition_code_coverage,
    check_condition_code_consistency,
    check_condition_code_risk,
    check_condition_code_confidence,
    check_condition_code_dependency,
    check_condition_code_readiness,
    check_sample_size_presence,
    check_sample_size_range,
    check_sample_size_stability,
    check_sample_size_freshness,
    check_sample_size_coverage,
    check_sample_size_consistency,
    check_sample_size_risk,
    check_sample_size_confidence,
    check_sample_size_dependency,
    check_sample_size_readiness,
    check_positive_rate_presence,
    check_positive_rate_range,
    check_positive_rate_stability,
    check_positive_rate_freshness,
    check_positive_rate_coverage,
    check_positive_rate_consistency,
    check_positive_rate_risk,
    check_positive_rate_confidence,
    check_positive_rate_dependency,
    check_positive_rate_readiness,
    check_consent_scope_presence,
    check_consent_scope_range,
    check_consent_scope_stability,
    check_consent_scope_freshness,
    check_consent_scope_coverage,
    check_consent_scope_consistency,
    check_consent_scope_risk,
    check_consent_scope_confidence,
    check_consent_scope_dependency,
    check_consent_scope_readiness,
    check_terminology_version_presence,
    check_terminology_version_range,
    check_terminology_version_stability,
    check_terminology_version_freshness,
    check_terminology_version_coverage,
    check_terminology_version_consistency,
    check_terminology_version_risk,
    check_terminology_version_confidence,
    check_terminology_version_dependency,
    check_terminology_version_readiness,
    check_missingness_presence,
    check_missingness_range,
    check_missingness_stability,
    check_missingness_freshness,
    check_missingness_coverage,
    check_missingness_consistency,
    check_missingness_risk,
    check_missingness_confidence,
    check_missingness_dependency,
    check_missingness_readiness,
    check_sensitivity_presence,
    check_sensitivity_range,
    check_sensitivity_stability,
    check_sensitivity_freshness,
    check_sensitivity_coverage,
    check_sensitivity_consistency,
    check_sensitivity_risk,
    check_sensitivity_confidence,
    check_sensitivity_dependency,
    check_sensitivity_readiness,
    check_specificity_presence,
    check_specificity_range,
    check_specificity_stability,
    check_specificity_freshness,
    check_specificity_coverage,
    check_specificity_consistency,
    check_specificity_risk,
    check_specificity_confidence,
    check_specificity_dependency,
    check_specificity_readiness,
    check_adverse_events_presence,
    check_adverse_events_range,
    check_adverse_events_stability,
    check_adverse_events_freshness,
    check_adverse_events_coverage,
    check_adverse_events_consistency,
    check_adverse_events_risk,
    check_adverse_events_confidence,
    check_adverse_events_dependency,
    check_adverse_events_readiness,
    check_review_board_presence,
    check_review_board_range,
    check_review_board_stability,
    check_review_board_freshness,
    check_review_board_coverage,
    check_review_board_consistency,
    check_review_board_risk,
    check_review_board_confidence,
    check_review_board_dependency,
    check_review_board_readiness,
)

RULE_INDEX = {rule.__name__: rule for rule in RULES}

def evaluate(record: DomainRecord, context: Mapping[str, Any] | None = None) -> tuple[RuleResult, ...]:
    context = context or {}
    return tuple(rule(record, context) for rule in RULES)

def summarize(results: tuple[RuleResult, ...]) -> dict[str, Any]:
    if not results:
        return {'score': 0.0, 'passed': 0, 'failed': 0, 'critical': 0}
    return {'score': sum(item.score for item in results) / len(results),
            'passed': sum(item.passed for item in results),
            'failed': sum(not item.passed for item in results),
            'critical': sum(item.severity == 'critical' for item in results)}
