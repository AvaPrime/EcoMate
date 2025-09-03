import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from temporalio import activity

from .engine import ComplianceEngine, load_rules, evaluate
from .models import (
    SystemSpecification, ComplianceMetrics, SystemType, ComplianceStatus
)
from ..shared.github_client import GitHubClient

logger = logging.getLogger(__name__)

@activity.defn
async def activity_compliance(system_id: str, rules: list[str]) -> dict:
    """Legacy compliance activity for backward compatibility"""
    findings = []
    for rule_name in rules:
        rule_data = load_rules(rule_name)
        # Mock system spec - in real implementation, fetch from database
        system_spec = {"uv_dose_mj_cm2": 40}
        rule_findings = evaluate(system_spec, rule_data)
        findings.extend(rule_findings)
    
    return {"system_id": system_id, "findings": findings}

@activity.defn
async def activity_enhanced_compliance_check(
    system_id: str, 
    system_type: str,
    specifications: Dict[str, Any],
    rulesets: List[str]
) -> Dict[str, Any]:
    """Enhanced compliance checking with structured evaluation"""
    try:
        engine = ComplianceEngine()
        
        # Create system specification
        system_spec = SystemSpecification(
            system_id=system_id,
            system_type=SystemType(system_type),
            specifications=specifications,
            location="Default Location",  # Could be passed as parameter
            installation_date=datetime.now().date()
        )
        
        # Evaluate compliance
        report = engine.evaluate_system(system_spec, rulesets)
        
        # Create GitHub PR with compliance report
        github_client = GitHubClient()
        
        # Generate compliance report content
        report_content = {
            "compliance_report": {
                "report_id": report.report_id,
                "system_id": report.system_id,
                "system_type": report.system_type.value,
                "evaluation_date": report.evaluation_date.isoformat(),
                "overall_status": report.overall_status.value,
                "overall_score": report.overall_score,
                "summary": {
                    "total_rules": report.total_rules,
                    "passed_rules": report.passed_rules,
                    "failed_rules": report.failed_rules,
                    "critical_failures": report.critical_failures,
                    "high_priority_failures": report.high_priority_failures
                },
                "rulesets_evaluated": report.rulesets_evaluated,
                "remediation_required": report.remediation_required,
                "remediation_items": report.remediation_items
            },
            "rule_details": [
                {
                    "rule_id": result.rule.rule_id,
                    "rule_name": result.rule.name,
                    "status": result.status.value,
                    "compliance_score": result.compliance_score,
                    "severity": result.rule.severity.value,
                    "passed_conditions": result.passed_conditions,
                    "total_conditions": result.total_conditions,
                    "condition_results": [
                        {
                            "field": cond_result.condition.field,
                            "operator": cond_result.condition.operator.value,
                            "expected_value": cond_result.expected_value,
                            "actual_value": cond_result.actual_value,
                            "passed": cond_result.passed,
                            "message": cond_result.message
                        }
                        for cond_result in result.condition_results
                    ]
                }
                for result in report.rule_results
            ]
        }
        
        # Create PR with compliance report
        pr_title = f"Compliance Report - {system_id} ({report.overall_status.value})"
        pr_body = f"""# Compliance Evaluation Report

**System ID:** {system_id}
**System Type:** {system_type}
**Overall Status:** {report.overall_status.value}
**Overall Score:** {report.overall_score:.1f}%
**Evaluation Date:** {report.evaluation_date.strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Total Rules Evaluated:** {report.total_rules}
- **Passed Rules:** {report.passed_rules}
- **Failed Rules:** {report.failed_rules}
- **Critical Failures:** {report.critical_failures}
- **High Priority Failures:** {report.high_priority_failures}

## Rulesets Evaluated
{', '.join(report.rulesets_evaluated)}

## Remediation Required
{'Yes' if report.remediation_required else 'No'}

{f'### Remediation Items ({len(report.remediation_items)})' if report.remediation_items else ''}
{''.join([f'- **{item["rule_name"]}** ({item["severity"]}): {item["description"]}' + '\n' for item in report.remediation_items])}

See attached JSON file for detailed evaluation results.
"""
        
        file_path = f"compliance_reports/{report.report_id}.json"
        pr_url = await github_client.create_pr_with_file(
            title=pr_title,
            body=pr_body,
            file_path=file_path,
            file_content=json.dumps(report_content, indent=2, default=str),
            branch_name=f"compliance-report-{system_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )
        
        return {
            "report_id": report.report_id,
            "system_id": system_id,
            "overall_status": report.overall_status.value,
            "overall_score": report.overall_score,
            "total_rules": report.total_rules,
            "passed_rules": report.passed_rules,
            "failed_rules": report.failed_rules,
            "critical_failures": report.critical_failures,
            "remediation_required": report.remediation_required,
            "pr_url": pr_url,
            "evaluation_date": report.evaluation_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in enhanced compliance check: {str(e)}")
        return {
            "error": str(e),
            "system_id": system_id,
            "status": "error"
        }

@activity.defn
async def activity_compliance_metrics(
    system_ids: List[str],
    date_range_days: int = 30
) -> Dict[str, Any]:
    """Calculate compliance metrics across multiple systems"""
    try:
        engine = ComplianceEngine()
        
        # Mock data - in real implementation, fetch from database
        mock_systems = [
            {
                "system_id": sys_id,
                "system_type": "WATER_TREATMENT",
                "specifications": {
                    "uv_dose_mj_cm2": 45,
                    "storage_days": 7,
                    "water_monitoring_enabled": True,
                    "energy_efficiency_rating": 0.85
                }
            }
            for sys_id in system_ids
        ]
        
        total_systems = len(mock_systems)
        compliant_systems = 0
        non_compliant_systems = 0
        partial_compliance_systems = 0
        critical_failures_total = 0
        high_priority_failures_total = 0
        
        system_reports = []
        
        for system_data in mock_systems:
            system_spec = SystemSpecification(
                system_id=system_data["system_id"],
                system_type=SystemType(system_data["system_type"]),
                specifications=system_data["specifications"],
                location="Default Location",
                installation_date=datetime.now().date()
            )
            
            # Evaluate against available rulesets
            available_rulesets = engine.get_available_rulesets()
            report = engine.evaluate_system(system_spec, available_rulesets)
            
            system_reports.append({
                "system_id": report.system_id,
                "status": report.overall_status.value,
                "score": report.overall_score,
                "critical_failures": report.critical_failures,
                "high_priority_failures": report.high_priority_failures
            })
            
            if report.overall_status == ComplianceStatus.COMPLIANT:
                compliant_systems += 1
            elif report.overall_status == ComplianceStatus.NON_COMPLIANT:
                non_compliant_systems += 1
            else:
                partial_compliance_systems += 1
            
            critical_failures_total += report.critical_failures
            high_priority_failures_total += report.high_priority_failures
        
        # Calculate metrics
        compliance_rate = (compliant_systems / total_systems * 100) if total_systems > 0 else 0
        average_score = sum(r["score"] for r in system_reports) / len(system_reports) if system_reports else 0
        
        metrics = ComplianceMetrics(
            total_systems=total_systems,
            compliant_systems=compliant_systems,
            non_compliant_systems=non_compliant_systems,
            partial_compliance_systems=partial_compliance_systems,
            compliance_rate=compliance_rate,
            average_compliance_score=average_score,
            critical_failures_total=critical_failures_total,
            high_priority_failures_total=high_priority_failures_total,
            evaluation_period_days=date_range_days
        )
        
        return {
            "metrics": {
                "total_systems": metrics.total_systems,
                "compliant_systems": metrics.compliant_systems,
                "non_compliant_systems": metrics.non_compliant_systems,
                "partial_compliance_systems": metrics.partial_compliance_systems,
                "compliance_rate": metrics.compliance_rate,
                "average_compliance_score": metrics.average_compliance_score,
                "critical_failures_total": metrics.critical_failures_total,
                "high_priority_failures_total": metrics.high_priority_failures_total,
                "evaluation_period_days": metrics.evaluation_period_days
            },
            "system_reports": system_reports,
            "available_rulesets": engine.get_available_rulesets(),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error calculating compliance metrics: {str(e)}")
        return {
            "error": str(e),
            "status": "error"
        }

@activity.defn
async def activity_ruleset_info(ruleset_name: Optional[str] = None) -> Dict[str, Any]:
    """Get information about available rulesets"""
    try:
        engine = ComplianceEngine()
        
        if ruleset_name:
            # Get specific ruleset info
            info = engine.get_ruleset_info(ruleset_name)
            if not info:
                return {
                    "error": f"Ruleset '{ruleset_name}' not found",
                    "available_rulesets": engine.get_available_rulesets()
                }
            return {"ruleset_info": info}
        else:
            # Get all rulesets info
            available_rulesets = engine.get_available_rulesets()
            rulesets_info = {}
            
            for ruleset_id in available_rulesets:
                info = engine.get_ruleset_info(ruleset_id)
                if info:
                    rulesets_info[ruleset_id] = info
            
            return {
                "available_rulesets": available_rulesets,
                "rulesets_info": rulesets_info,
                "total_rulesets": len(available_rulesets)
            }
            
    except Exception as e:
        logger.error(f"Error getting ruleset info: {str(e)}")
        return {
            "error": str(e),
            "status": "error"
        }