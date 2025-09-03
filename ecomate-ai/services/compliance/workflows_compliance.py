import logging
from datetime import timedelta
from typing import Dict, List, Any, Optional
from temporalio import workflow

from .activities_compliance import (
    activity_compliance,
    activity_enhanced_compliance_check,
    activity_compliance_metrics,
    activity_ruleset_info
)

logger = logging.getLogger(__name__)

@workflow.defn
class ComplianceWorkflow:
    """Legacy compliance workflow for backward compatibility"""
    
    @workflow.run
    async def run(self, system_id: str, rules: list[str]) -> dict:
        return await workflow.execute_activity(
            activity_compliance,
            args=[system_id, rules],
            start_to_close_timeout=timedelta(minutes=5)
        )

@workflow.defn
class EnhancedComplianceWorkflow:
    """Enhanced compliance workflow with structured evaluation"""
    
    @workflow.run
    async def run(
        self,
        system_id: str,
        system_type: str,
        specifications: Dict[str, Any],
        rulesets: List[str]
    ) -> Dict[str, Any]:
        """Run enhanced compliance check for a system"""
        return await workflow.execute_activity(
            activity_enhanced_compliance_check,
            args=[system_id, system_type, specifications, rulesets],
            start_to_close_timeout=timedelta(minutes=10)
        )

@workflow.defn
class ComplianceMetricsWorkflow:
    """Workflow for calculating compliance metrics across multiple systems"""
    
    @workflow.run
    async def run(
        self,
        system_ids: List[str],
        date_range_days: int = 30
    ) -> Dict[str, Any]:
        """Calculate compliance metrics for multiple systems"""
        return await workflow.execute_activity(
            activity_compliance_metrics,
            args=[system_ids, date_range_days],
            start_to_close_timeout=timedelta(minutes=15)
        )

@workflow.defn
class RulesetInfoWorkflow:
    """Workflow for retrieving ruleset information"""
    
    @workflow.run
    async def run(self, ruleset_name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about available rulesets"""
        return await workflow.execute_activity(
            activity_ruleset_info,
            args=[ruleset_name],
            start_to_close_timeout=timedelta(minutes=5)
        )

@workflow.defn
class BatchComplianceWorkflow:
    """Workflow for batch compliance evaluation across multiple systems"""
    
    @workflow.run
    async def run(
        self,
        systems: List[Dict[str, Any]],
        rulesets: List[str]
    ) -> Dict[str, Any]:
        """Run compliance checks for multiple systems in batch"""
        results = []
        
        for system in systems:
            try:
                result = await workflow.execute_activity(
                    activity_enhanced_compliance_check,
                    args=[
                        system["system_id"],
                        system["system_type"],
                        system["specifications"],
                        rulesets
                    ],
                    start_to_close_timeout=timedelta(minutes=10)
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error evaluating system {system.get('system_id', 'unknown')}: {str(e)}")
                results.append({
                    "system_id": system.get("system_id", "unknown"),
                    "error": str(e),
                    "status": "error"
                })
        
        # Calculate summary metrics
        total_systems = len(systems)
        successful_evaluations = len([r for r in results if "error" not in r])
        failed_evaluations = total_systems - successful_evaluations
        
        compliant_systems = len([r for r in results if r.get("overall_status") == "COMPLIANT"])
        non_compliant_systems = len([r for r in results if r.get("overall_status") == "NON_COMPLIANT"])
        partial_compliance_systems = len([r for r in results if r.get("overall_status") == "PARTIAL_COMPLIANCE"])
        
        return {
            "batch_summary": {
                "total_systems": total_systems,
                "successful_evaluations": successful_evaluations,
                "failed_evaluations": failed_evaluations,
                "compliant_systems": compliant_systems,
                "non_compliant_systems": non_compliant_systems,
                "partial_compliance_systems": partial_compliance_systems,
                "compliance_rate": (compliant_systems / successful_evaluations * 100) if successful_evaluations > 0 else 0
            },
            "system_results": results,
            "rulesets_evaluated": rulesets,
            "evaluation_timestamp": workflow.now().isoformat()
        }