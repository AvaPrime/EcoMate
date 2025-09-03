import yaml
import re
import operator
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .models import (
    ComplianceRule, RuleSet, RuleCondition, EvaluationResult, 
    RuleEvaluationResult, ComplianceReport, SystemSpecification,
    ComplianceStatus, RuleSeverity, RuleOperator, StandardType, SystemType
)

logger = logging.getLogger(__name__)

class ComplianceEngine:
    """Enhanced compliance evaluation engine with structured rule processing"""
    
    def __init__(self, rules_directory: str = "services/compliance/rules"):
        self.rules_directory = Path(rules_directory)
        self.operators = {
            RuleOperator.EQUALS: operator.eq,
            RuleOperator.NOT_EQUALS: operator.ne,
            RuleOperator.GREATER_THAN: operator.gt,
            RuleOperator.GREATER_EQUAL: operator.ge,
            RuleOperator.LESS_THAN: operator.lt,
            RuleOperator.LESS_EQUAL: operator.le,
        }
        self.rulesets: Dict[str, RuleSet] = {}
        self.load_all_rulesets()
    
    def load_all_rulesets(self) -> None:
        """Load all rulesets from the rules directory"""
        try:
            if not self.rules_directory.exists():
                logger.warning(f"Rules directory {self.rules_directory} does not exist")
                return
            
            for rule_file in self.rules_directory.glob("*.yaml"):
                try:
                    ruleset = self.load_ruleset(rule_file.stem)
                    if ruleset:
                        self.rulesets[ruleset.ruleset_id] = ruleset
                        logger.info(f"Loaded ruleset: {ruleset.ruleset_id} with {len(ruleset.rules)} rules")
                except Exception as e:
                    logger.error(f"Failed to load ruleset from {rule_file}: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading rulesets: {str(e)}")
    
    def load_ruleset(self, ruleset_name: str) -> Optional[RuleSet]:
        """Load a specific ruleset from YAML file"""
        rule_file = self.rules_directory / f"{ruleset_name}.yaml"
        
        if not rule_file.exists():
            logger.warning(f"Ruleset file {rule_file} does not exist")
            return None
        
        try:
            with open(rule_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            # Convert legacy format if needed
            if self._is_legacy_format(data):
                data = self._convert_legacy_format(data, ruleset_name)
            
            return RuleSet(**data)
        except Exception as e:
            logger.error(f"Error loading ruleset {ruleset_name}: {str(e)}")
            return None
    
    def _is_legacy_format(self, data: Dict) -> bool:
        """Check if the data is in legacy format"""
        return 'ruleset_id' not in data and ('min_' in str(data) or 'max_' in str(data))
    
    def _convert_legacy_format(self, data: Dict, ruleset_name: str) -> Dict:
        """Convert legacy format to new structured format"""
        rules = []
        
        for key, value in data.items():
            if key.startswith('min_'):
                field_name = key[4:]  # Remove 'min_' prefix
                rule = {
                    'rule_id': f"{ruleset_name.upper()}_{field_name.upper()}_MIN",
                    'name': f"Minimum {field_name.replace('_', ' ').title()}",
                    'description': f"Minimum required value for {field_name}",
                    'standard_type': StandardType.SANS if 'sans' in ruleset_name else StandardType.CUSTOM,
                    'system_types': [SystemType.WATER_TREATMENT],
                    'severity': RuleSeverity.HIGH,
                    'conditions': [{
                        'field': field_name,
                        'operator': RuleOperator.GREATER_EQUAL,
                        'value': value,
                        'description': f"Must be >= {value}"
                    }]
                }
                rules.append(rule)
            elif key.startswith('max_'):
                field_name = key[4:]  # Remove 'max_' prefix
                rule = {
                    'rule_id': f"{ruleset_name.upper()}_{field_name.upper()}_MAX",
                    'name': f"Maximum {field_name.replace('_', ' ').title()}",
                    'description': f"Maximum allowed value for {field_name}",
                    'standard_type': StandardType.SANS if 'sans' in ruleset_name else StandardType.CUSTOM,
                    'system_types': [SystemType.WATER_TREATMENT],
                    'severity': RuleSeverity.HIGH,
                    'conditions': [{
                        'field': field_name,
                        'operator': RuleOperator.LESS_EQUAL,
                        'value': value,
                        'description': f"Must be <= {value}"
                    }]
                }
                rules.append(rule)
        
        return {
            'ruleset_id': ruleset_name,
            'name': f"{ruleset_name.replace('_', ' ').title()} Rules",
            'description': f"Compliance rules for {ruleset_name}",
            'standard_type': StandardType.SANS if 'sans' in ruleset_name else StandardType.CUSTOM,
            'version': '1.0',
            'rules': rules
        }
    
    def evaluate_condition(self, condition: RuleCondition, spec_data: Dict[str, Any]) -> EvaluationResult:
        """Evaluate a single rule condition against specification data"""
        field_value = self._get_nested_value(spec_data, condition.field)
        
        # Handle missing field
        if field_value is None:
            if condition.operator == RuleOperator.EXISTS:
                passed = False
                message = f"Field '{condition.field}' does not exist"
            elif condition.operator == RuleOperator.NOT_EXISTS:
                passed = True
                message = f"Field '{condition.field}' correctly does not exist"
            else:
                passed = False
                message = f"Field '{condition.field}' is missing from specification"
        else:
            passed, message = self._evaluate_condition_logic(condition, field_value)
        
        return EvaluationResult(
            condition=condition,
            actual_value=field_value,
            expected_value=condition.value,
            passed=passed,
            message=message,
            severity=RuleSeverity.HIGH  # Default severity, can be overridden by rule
        )
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = field_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _evaluate_condition_logic(self, condition: RuleCondition, actual_value: Any) -> tuple[bool, str]:
        """Evaluate the condition logic and return (passed, message)"""
        try:
            if condition.operator in self.operators:
                op_func = self.operators[condition.operator]
                passed = op_func(actual_value, condition.value)
                message = f"{actual_value} {condition.operator.value} {condition.value}: {'PASS' if passed else 'FAIL'}"
            
            elif condition.operator == RuleOperator.CONTAINS:
                passed = str(condition.value).lower() in str(actual_value).lower()
                message = f"'{condition.value}' {'found' if passed else 'not found'} in '{actual_value}'"
            
            elif condition.operator == RuleOperator.NOT_CONTAINS:
                passed = str(condition.value).lower() not in str(actual_value).lower()
                message = f"'{condition.value}' {'correctly not found' if passed else 'incorrectly found'} in '{actual_value}'"
            
            elif condition.operator == RuleOperator.IN:
                passed = actual_value in condition.value if isinstance(condition.value, list) else False
                message = f"'{actual_value}' {'is' if passed else 'is not'} in allowed values {condition.value}"
            
            elif condition.operator == RuleOperator.NOT_IN:
                passed = actual_value not in condition.value if isinstance(condition.value, list) else True
                message = f"'{actual_value}' {'is correctly not' if passed else 'is incorrectly'} in restricted values {condition.value}"
            
            elif condition.operator == RuleOperator.REGEX:
                pattern = str(condition.value)
                passed = bool(re.match(pattern, str(actual_value)))
                message = f"'{actual_value}' {'matches' if passed else 'does not match'} pattern '{pattern}'"
            
            elif condition.operator == RuleOperator.EXISTS:
                passed = actual_value is not None
                message = f"Field {'exists' if passed else 'does not exist'}"
            
            elif condition.operator == RuleOperator.NOT_EXISTS:
                passed = actual_value is None
                message = f"Field {'correctly does not exist' if passed else 'incorrectly exists'}"
            
            else:
                passed = False
                message = f"Unknown operator: {condition.operator}"
            
            return passed, message
        
        except Exception as e:
            return False, f"Error evaluating condition: {str(e)}"
    
    def evaluate_rule(self, rule: ComplianceRule, spec_data: Dict[str, Any]) -> RuleEvaluationResult:
        """Evaluate a complete rule against specification data"""
        condition_results = []
        
        for condition in rule.conditions:
            result = self.evaluate_condition(condition, spec_data)
            result.severity = rule.severity  # Use rule's severity
            condition_results.append(result)
        
        # Apply logic operator (AND/OR)
        passed_conditions = sum(1 for r in condition_results if r.passed)
        total_conditions = len(condition_results)
        
        if rule.logic_operator.upper() == "OR":
            rule_passed = passed_conditions > 0
        else:  # Default to AND
            rule_passed = passed_conditions == total_conditions
        
        # Determine compliance status
        if rule_passed:
            status = ComplianceStatus.COMPLIANT
        elif passed_conditions > 0:
            status = ComplianceStatus.PARTIAL
        else:
            status = ComplianceStatus.NON_COMPLIANT
        
        compliance_score = (passed_conditions / total_conditions) * 100 if total_conditions > 0 else 0
        
        return RuleEvaluationResult(
            rule=rule,
            status=status,
            condition_results=condition_results,
            passed_conditions=passed_conditions,
            total_conditions=total_conditions,
            compliance_score=compliance_score,
            remediation_required=not rule_passed,
            remediation_priority=rule.severity
        )
    
    def evaluate_system(self, system_spec: SystemSpecification, ruleset_names: List[str]) -> ComplianceReport:
        """Evaluate a system against specified rulesets"""
        rule_results = []
        applicable_rules = []
        
        # Collect applicable rules from specified rulesets
        for ruleset_name in ruleset_names:
            if ruleset_name in self.rulesets:
                ruleset = self.rulesets[ruleset_name]
                for rule in ruleset.rules:
                    # Check if rule applies to this system type
                    if system_spec.system_type in rule.system_types or not rule.system_types:
                        applicable_rules.append(rule)
        
        # Evaluate each applicable rule
        for rule in applicable_rules:
            result = self.evaluate_rule(rule, system_spec.specifications)
            rule_results.append(result)
        
        # Calculate overall metrics
        total_rules = len(rule_results)
        passed_rules = sum(1 for r in rule_results if r.status == ComplianceStatus.COMPLIANT)
        failed_rules = sum(1 for r in rule_results if r.status == ComplianceStatus.NON_COMPLIANT)
        critical_failures = sum(1 for r in rule_results if r.rule.severity == RuleSeverity.CRITICAL and r.status != ComplianceStatus.COMPLIANT)
        high_priority_failures = sum(1 for r in rule_results if r.rule.severity == RuleSeverity.HIGH and r.status != ComplianceStatus.COMPLIANT)
        
        # Calculate overall score
        if total_rules > 0:
            overall_score = sum(r.compliance_score for r in rule_results) / total_rules
        else:
            overall_score = 100.0
        
        # Determine overall status
        if critical_failures > 0:
            overall_status = ComplianceStatus.NON_COMPLIANT
        elif failed_rules > 0:
            overall_status = ComplianceStatus.PARTIAL
        elif total_rules > 0:
            overall_status = ComplianceStatus.COMPLIANT
        else:
            overall_status = ComplianceStatus.UNKNOWN
        
        # Generate remediation items
        remediation_items = []
        for result in rule_results:
            if result.remediation_required:
                remediation_items.append({
                    'rule_id': result.rule.rule_id,
                    'rule_name': result.rule.name,
                    'severity': result.rule.severity.value,
                    'description': result.rule.description,
                    'guidance': result.rule.remediation_guidance,
                    'failed_conditions': [r.message for r in result.condition_results if not r.passed]
                })
        
        return ComplianceReport(
            report_id=f"compliance_{system_spec.system_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            system_id=system_spec.system_id,
            system_type=system_spec.system_type,
            rulesets_evaluated=ruleset_names,
            overall_status=overall_status,
            overall_score=overall_score,
            rule_results=rule_results,
            total_rules=total_rules,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            critical_failures=critical_failures,
            high_priority_failures=high_priority_failures,
            remediation_required=len(remediation_items) > 0,
            remediation_items=remediation_items,
            specification_data=system_spec.specifications
        )
    
    def get_available_rulesets(self) -> List[str]:
        """Get list of available ruleset names"""
        return list(self.rulesets.keys())
    
    def get_ruleset_info(self, ruleset_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific ruleset"""
        if ruleset_name not in self.rulesets:
            return None
        
        ruleset = self.rulesets[ruleset_name]
        return {
            'ruleset_id': ruleset.ruleset_id,
            'name': ruleset.name,
            'description': ruleset.description,
            'standard_type': ruleset.standard_type.value,
            'version': ruleset.version,
            'jurisdiction': ruleset.jurisdiction,
            'total_rules': len(ruleset.rules),
            'rule_severities': {severity.value: sum(1 for r in ruleset.rules if r.severity == severity) for severity in RuleSeverity},
            'system_types': list(set(st.value for rule in ruleset.rules for st in rule.system_types))
        }

# Legacy compatibility functions
def load_rules(name: str) -> dict:
    """Legacy function for backward compatibility"""
    engine = ComplianceEngine()
    ruleset = engine.load_ruleset(name)
    if not ruleset:
        return {}
    
    # Convert to legacy format
    legacy_rules = {}
    for rule in ruleset.rules:
        for condition in rule.conditions:
            if condition.operator == RuleOperator.GREATER_EQUAL:
                legacy_rules[f"min_{condition.field}"] = condition.value
            elif condition.operator == RuleOperator.LESS_EQUAL:
                legacy_rules[f"max_{condition.field}"] = condition.value
    
    return legacy_rules

def evaluate(spec: dict, rules: dict) -> list[dict]:
    """Legacy function for backward compatibility"""
    findings = []
    for key, value in rules.items():
        if key.startswith('min_'):
            field = key[4:]
            if field in spec:
                ok = spec[field] >= value
                findings.append({
                    "rule": field,
                    "ok": ok,
                    "value": spec[field],
                    "min": value
                })
        elif key.startswith('max_'):
            field = key[4:]
            if field in spec:
                ok = spec[field] <= value
                findings.append({
                    "rule": field,
                    "ok": ok,
                    "value": spec[field],
                    "max": value
                })
    return findings