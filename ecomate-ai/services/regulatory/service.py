"""Regulatory service for compliance monitoring and standards tracking."""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any

from .client import RegulatoryClient
from .models import (
    StandardsBody,
    RegulatoryStandard,
    ComplianceCheck,
    ComplianceStatus,
    RegulatoryAlert,
    StandardsUpdate,
    ComplianceReport,
    RegulatoryQuery,
    RegulatoryResponse,
    BatchRegulatoryRequest,
    BatchRegulatoryResponse,
    StandardCategory,
    AlertSeverity
)

logger = logging.getLogger(__name__)


class RegulatoryService:
    """High-level service for regulatory compliance monitoring."""
    
    def __init__(
        self,
        client: RegulatoryClient,
        config: Dict[str, Any] = None
    ):
        """Initialize the regulatory service.
        
        Args:
            client: RegulatoryClient instance
            config: Service configuration
        """
        self.client = client
        self.config = config or {}
        self._compliance_cache = {}
        self._alert_handlers = []
        self._update_handlers = []
    
    async def monitor_compliance(
        self,
        entity_id: str,
        standards: List[str],
        check_interval: int = 3600
    ) -> Dict[str, Any]:
        """Monitor compliance for an entity against specified standards.
        
        Args:
            entity_id: Entity identifier
            standards: List of standard IDs to monitor
            check_interval: Check interval in seconds
            
        Returns:
            Compliance monitoring results
        """
        try:
            logger.info(f"Starting compliance monitoring for entity {entity_id}")
            
            compliance_results = []
            overall_status = ComplianceStatus.COMPLIANT
            
            async with self.client:
                for standard_id in standards:
                    # Determine standards body from standard ID
                    body = self._determine_standards_body(standard_id)
                    if not body:
                        logger.warning(f"Could not determine standards body for {standard_id}")
                        continue
                    
                    # Get standard details
                    standard = await self.client.get_standard(body, standard_id)
                    if not standard:
                        logger.warning(f"Could not retrieve standard {standard_id}")
                        continue
                    
                    # Perform compliance check
                    check_result = await self._perform_compliance_check(
                        entity_id, standard
                    )
                    compliance_results.append(check_result)
                    
                    # Update overall status
                    if check_result.status == ComplianceStatus.NON_COMPLIANT:
                        overall_status = ComplianceStatus.NON_COMPLIANT
                    elif (check_result.status == ComplianceStatus.PARTIALLY_COMPLIANT and 
                          overall_status == ComplianceStatus.COMPLIANT):
                        overall_status = ComplianceStatus.PARTIALLY_COMPLIANT
            
            # Generate alerts for non-compliant items
            alerts = await self._generate_compliance_alerts(
                entity_id, compliance_results
            )
            
            # Cache results
            cache_key = f"{entity_id}:{':'.join(standards)}"
            self._compliance_cache[cache_key] = {
                "results": compliance_results,
                "overall_status": overall_status,
                "timestamp": datetime.utcnow(),
                "alerts": alerts
            }
            
            return {
                "entity_id": entity_id,
                "overall_status": overall_status,
                "standards_checked": len(compliance_results),
                "compliant_count": len([r for r in compliance_results if r.status == ComplianceStatus.COMPLIANT]),
                "non_compliant_count": len([r for r in compliance_results if r.status == ComplianceStatus.NON_COMPLIANT]),
                "results": compliance_results,
                "alerts": alerts,
                "next_check": datetime.utcnow() + timedelta(seconds=check_interval)
            }
            
        except Exception as e:
            logger.error(f"Error monitoring compliance for {entity_id}: {e}")
            return {
                "entity_id": entity_id,
                "error": str(e),
                "timestamp": datetime.utcnow()
            }
    
    async def track_standards_updates(
        self,
        bodies: List[StandardsBody] = None,
        since: date = None,
        categories: List[StandardCategory] = None
    ) -> List[StandardsUpdate]:
        """Track updates across multiple standards bodies.
        
        Args:
            bodies: Standards bodies to monitor (all if None)
            since: Get updates since this date
            categories: Filter by categories
            
        Returns:
            List of standards updates
        """
        if not since:
            since = date.today() - timedelta(days=30)  # Last 30 days
        
        if not bodies:
            bodies = list(StandardsBody)
        
        all_updates = []
        
        async with self.client:
            # Get updates from each standards body
            tasks = [
                self.client.get_standards_updates(body, since)
                for body in bodies
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for body, result in zip(bodies, results):
                if isinstance(result, Exception):
                    logger.error(f"Error getting updates from {body.value}: {result}")
                    continue
                
                # Filter by categories if specified
                if categories:
                    filtered_updates = []
                    for update in result:
                        # Get standard details to check category
                        standard = await self.client.get_standard(body, update.standard_id)
                        if standard and standard.category in categories:
                            filtered_updates.append(update)
                    all_updates.extend(filtered_updates)
                else:
                    all_updates.extend(result)
        
        # Sort by publication date (newest first)
        all_updates.sort(key=lambda x: x.publication_date, reverse=True)
        
        # Process updates through handlers
        for handler in self._update_handlers:
            try:
                await handler(all_updates)
            except Exception as e:
                logger.error(f"Error in update handler: {e}")
        
        return all_updates
    
    async def generate_compliance_report(
        self,
        entity_id: str,
        entity_name: str,
        period_start: date,
        period_end: date,
        standards: List[str] = None
    ) -> ComplianceReport:
        """Generate comprehensive compliance report.
        
        Args:
            entity_id: Entity identifier
            entity_name: Entity name
            period_start: Report period start
            period_end: Report period end
            standards: Specific standards to include
            
        Returns:
            ComplianceReport object
        """
        try:
            logger.info(f"Generating compliance report for {entity_name}")
            
            # Get compliance data for the period
            compliance_data = await self._get_compliance_history(
                entity_id, period_start, period_end, standards
            )
            
            # Calculate statistics
            total_checks = len(compliance_data)
            compliant_checks = len([c for c in compliance_data if c.status == ComplianceStatus.COMPLIANT])
            non_compliant_checks = len([c for c in compliance_data if c.status == ComplianceStatus.NON_COMPLIANT])
            
            # Determine overall status
            if non_compliant_checks == 0:
                overall_status = ComplianceStatus.COMPLIANT
            elif compliant_checks == 0:
                overall_status = ComplianceStatus.NON_COMPLIANT
            else:
                overall_status = ComplianceStatus.PARTIALLY_COMPLIANT
            
            # Calculate overall score
            if total_checks > 0:
                overall_score = compliant_checks / total_checks
            else:
                overall_score = 0.0
            
            # Extract findings and recommendations
            findings = []
            recommendations = []
            action_items = []
            
            for check in compliance_data:
                findings.extend(check.findings)
                recommendations.extend(check.recommendations)
                if check.remediation_required:
                    action_items.append(
                        f"Remediate {check.requirement_id} by {check.remediation_deadline}"
                    )
            
            # Remove duplicates
            findings = list(set(findings))
            recommendations = list(set(recommendations))
            action_items = list(set(action_items))
            
            # Get unique standards assessed
            standards_assessed = list(set([
                check.requirement_id.split(':')[0] if ':' in check.requirement_id else check.requirement_id
                for check in compliance_data
            ]))
            
            return ComplianceReport(
                id=f"report_{entity_id}_{period_end.isoformat()}",
                title=f"Compliance Report - {entity_name}",
                entity_id=entity_id,
                entity_name=entity_name,
                report_date=date.today(),
                period_start=period_start,
                period_end=period_end,
                overall_status=overall_status,
                overall_score=overall_score,
                standards_assessed=standards_assessed,
                checks_performed=total_checks,
                compliant_checks=compliant_checks,
                non_compliant_checks=non_compliant_checks,
                findings=findings[:10],  # Top 10 findings
                recommendations=recommendations[:10],  # Top 10 recommendations
                action_items=action_items,
                next_assessment_date=period_end + timedelta(days=90),  # Quarterly
                assessor="EcoMate Regulatory Monitor",
                metadata={
                    "generated_by": "regulatory_service",
                    "version": "1.0",
                    "total_findings": len(findings),
                    "total_recommendations": len(recommendations)
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            raise
    
    async def get_regulatory_alerts(
        self,
        entity_id: str = None,
        severity: AlertSeverity = None,
        since: date = None,
        limit: int = 100
    ) -> List[RegulatoryAlert]:
        """Get regulatory alerts with filtering.
        
        Args:
            entity_id: Filter by entity
            severity: Filter by severity
            since: Get alerts since this date
            limit: Maximum results
            
        Returns:
            List of regulatory alerts
        """
        if not since:
            since = date.today() - timedelta(days=7)  # Last week
        
        async with self.client:
            alerts = await self.client.get_alerts(
                severity=severity,
                since=since,
                limit=limit
            )
        
        # Filter by entity if specified
        if entity_id:
            alerts = [
                alert for alert in alerts
                if entity_id in alert.affected_entities
            ]
        
        # Process alerts through handlers
        for handler in self._alert_handlers:
            try:
                await handler(alerts)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
        
        return alerts
    
    async def assess_regulatory_impact(
        self,
        entity_id: str,
        proposed_changes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess regulatory impact of proposed changes.
        
        Args:
            entity_id: Entity identifier
            proposed_changes: List of proposed changes
            
        Returns:
            Impact assessment results
        """
        try:
            logger.info(f"Assessing regulatory impact for entity {entity_id}")
            
            impact_results = []
            overall_risk = "low"
            affected_standards = set()
            
            for change in proposed_changes:
                change_type = change.get("type")
                description = change.get("description")
                scope = change.get("scope", [])
                
                # Analyze impact based on change type and scope
                impact = await self._analyze_change_impact(
                    entity_id, change_type, description, scope
                )
                impact_results.append(impact)
                
                # Update overall risk
                if impact["risk_level"] == "high":
                    overall_risk = "high"
                elif impact["risk_level"] == "medium" and overall_risk != "high":
                    overall_risk = "medium"
                
                # Collect affected standards
                affected_standards.update(impact.get("affected_standards", []))
            
            # Get compliance requirements for affected standards
            requirements = []
            async with self.client:
                for standard_id in affected_standards:
                    body = self._determine_standards_body(standard_id)
                    if body:
                        standard = await self.client.get_standard(body, standard_id)
                        if standard:
                            # Extract requirements (simplified)
                            requirements.append({
                                "standard_id": standard_id,
                                "title": standard.title,
                                "category": standard.category,
                                "requirements": ["Compliance verification required"]
                            })
            
            return {
                "entity_id": entity_id,
                "overall_risk": overall_risk,
                "changes_assessed": len(proposed_changes),
                "affected_standards": list(affected_standards),
                "impact_results": impact_results,
                "compliance_requirements": requirements,
                "recommendations": self._generate_impact_recommendations(
                    overall_risk, impact_results
                ),
                "assessment_date": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error assessing regulatory impact: {e}")
            return {
                "entity_id": entity_id,
                "error": str(e),
                "assessment_date": datetime.utcnow()
            }
    
    async def process_query(self, query: RegulatoryQuery) -> RegulatoryResponse:
        """Process a regulatory query.
        
        Args:
            query: RegulatoryQuery object
            
        Returns:
            RegulatoryResponse object
        """
        start_time = datetime.utcnow()
        
        try:
            if query.query_type == "search_standards":
                data = await self._search_standards_query(query)
            elif query.query_type == "get_updates":
                data = await self._get_updates_query(query)
            elif query.query_type == "check_compliance":
                data = await self._check_compliance_query(query)
            elif query.query_type == "get_alerts":
                data = await self._get_alerts_query(query)
            else:
                raise ValueError(f"Unknown query type: {query.query_type}")
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return RegulatoryResponse(
                success=True,
                message="Query processed successfully",
                data=data,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Error processing query: {e}")
            
            return RegulatoryResponse(
                success=False,
                message=f"Query processing failed: {str(e)}",
                processing_time=processing_time,
                errors=[str(e)]
            )
    
    async def process_batch_request(
        self,
        batch_request: BatchRegulatoryRequest
    ) -> BatchRegulatoryResponse:
        """Process batch regulatory requests.
        
        Args:
            batch_request: BatchRegulatoryRequest object
            
        Returns:
            BatchRegulatoryResponse object
        """
        batch_id = batch_request.batch_id or f"batch_{datetime.utcnow().timestamp()}"
        started_at = datetime.utcnow()
        
        logger.info(f"Processing batch request {batch_id} with {len(batch_request.requests)} queries")
        
        # Process requests concurrently
        tasks = [self.process_query(query) for query in batch_request.requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error responses
        processed_responses = []
        completed_count = 0
        failed_count = 0
        
        for response in responses:
            if isinstance(response, Exception):
                error_response = RegulatoryResponse(
                    success=False,
                    message=f"Request failed: {str(response)}",
                    errors=[str(response)]
                )
                processed_responses.append(error_response)
                failed_count += 1
            else:
                processed_responses.append(response)
                if response.success:
                    completed_count += 1
                else:
                    failed_count += 1
        
        completed_at = datetime.utcnow()
        total_processing_time = (completed_at - started_at).total_seconds()
        
        return BatchRegulatoryResponse(
            batch_id=batch_id,
            total_requests=len(batch_request.requests),
            completed_requests=completed_count,
            failed_requests=failed_count,
            responses=processed_responses,
            batch_status="completed",
            started_at=started_at,
            completed_at=completed_at,
            total_processing_time=total_processing_time
        )
    
    def add_alert_handler(self, handler):
        """Add alert handler function."""
        self._alert_handlers.append(handler)
    
    def add_update_handler(self, handler):
        """Add update handler function."""
        self._update_handlers.append(handler)
    
    # Private helper methods
    
    def _determine_standards_body(self, standard_id: str) -> Optional[StandardsBody]:
        """Determine standards body from standard ID."""
        if standard_id.startswith("SANS"):
            return StandardsBody.SANS
        elif standard_id.startswith("ISO"):
            return StandardsBody.ISO
        elif "EPA" in standard_id.upper():
            return StandardsBody.EPA
        elif "OSHA" in standard_id.upper():
            return StandardsBody.OSHA
        elif standard_id.startswith("ANSI"):
            return StandardsBody.ANSI
        elif standard_id.startswith("ASTM"):
            return StandardsBody.ASTM
        elif standard_id.startswith("IEC"):
            return StandardsBody.IEC
        elif standard_id.startswith("IEEE"):
            return StandardsBody.IEEE
        else:
            return None
    
    async def _perform_compliance_check(
        self,
        entity_id: str,
        standard: RegulatoryStandard
    ) -> ComplianceCheck:
        """Perform compliance check for a standard."""
        # This is a simplified implementation
        # In practice, this would involve complex compliance logic
        
        check_id = f"check_{entity_id}_{standard.id}_{datetime.utcnow().timestamp()}"
        
        # Simulate compliance check logic
        # This would typically involve:
        # 1. Retrieving entity data
        # 2. Applying standard requirements
        # 3. Evaluating compliance
        # 4. Generating findings and recommendations
        
        # For now, return a basic check result
        return ComplianceCheck(
            id=check_id,
            requirement_id=standard.id,
            entity_id=entity_id,
            status=ComplianceStatus.COMPLIANT,  # Simplified
            check_date=datetime.utcnow(),
            assessor="EcoMate Regulatory Monitor",
            score=0.85,  # Simplified score
            findings=["Standard requirements reviewed"],
            recommendations=["Continue monitoring for updates"],
            next_check_date=date.today() + timedelta(days=90)
        )
    
    async def _generate_compliance_alerts(
        self,
        entity_id: str,
        compliance_results: List[ComplianceCheck]
    ) -> List[RegulatoryAlert]:
        """Generate alerts for compliance issues."""
        alerts = []
        
        for check in compliance_results:
            if check.status == ComplianceStatus.NON_COMPLIANT:
                alert = RegulatoryAlert(
                    id=f"alert_{check.id}",
                    title=f"Non-compliance detected: {check.requirement_id}",
                    message=f"Entity {entity_id} is non-compliant with {check.requirement_id}",
                    severity=AlertSeverity.HIGH,
                    body=self._determine_standards_body(check.requirement_id) or StandardsBody.ISO,
                    standard_id=check.requirement_id,
                    alert_type="compliance_violation",
                    created_at=datetime.utcnow(),
                    affected_entities=[entity_id],
                    action_required=True,
                    action_deadline=check.remediation_deadline
                )
                alerts.append(alert)
        
        return alerts
    
    async def _get_compliance_history(
        self,
        entity_id: str,
        period_start: date,
        period_end: date,
        standards: List[str] = None
    ) -> List[ComplianceCheck]:
        """Get compliance history for reporting period."""
        # This would typically query a database
        # For now, return empty list
        return []
    
    async def _analyze_change_impact(
        self,
        entity_id: str,
        change_type: str,
        description: str,
        scope: List[str]
    ) -> Dict[str, Any]:
        """Analyze impact of a proposed change."""
        # Simplified impact analysis
        risk_keywords = ["chemical", "emission", "waste", "safety", "environmental"]
        
        risk_level = "low"
        if any(keyword in description.lower() for keyword in risk_keywords):
            risk_level = "medium"
        
        if change_type in ["process_change", "equipment_modification"]:
            risk_level = "high"
        
        return {
            "change_type": change_type,
            "description": description,
            "risk_level": risk_level,
            "affected_standards": scope,  # Simplified
            "recommendations": [
                "Review applicable standards",
                "Conduct compliance assessment",
                "Update documentation"
            ]
        }
    
    def _generate_impact_recommendations(
        self,
        overall_risk: str,
        impact_results: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on impact assessment."""
        recommendations = []
        
        if overall_risk == "high":
            recommendations.extend([
                "Conduct detailed regulatory review before implementation",
                "Engage with regulatory experts",
                "Consider phased implementation approach"
            ])
        elif overall_risk == "medium":
            recommendations.extend([
                "Review applicable standards and requirements",
                "Update compliance documentation",
                "Monitor for regulatory changes"
            ])
        else:
            recommendations.extend([
                "Maintain current compliance monitoring",
                "Document changes for audit trail"
            ])
        
        return recommendations
    
    async def _search_standards_query(self, query: RegulatoryQuery) -> List[Dict[str, Any]]:
        """Process standards search query."""
        results = []
        
        async with self.client:
            if query.body:
                standards = await self.client.search_standards(
                    query.body,
                    " ".join(query.keywords) if query.keywords else None,
                    query.category,
                    query.limit,
                    query.offset
                )
                results.extend([s.dict() for s in standards])
            else:
                # Search across all bodies
                for body in StandardsBody:
                    try:
                        standards = await self.client.search_standards(
                            body,
                            " ".join(query.keywords) if query.keywords else None,
                            query.category,
                            min(query.limit // len(StandardsBody), 20),
                            0
                        )
                        results.extend([s.dict() for s in standards])
                    except Exception as e:
                        logger.warning(f"Error searching {body.value}: {e}")
        
        return results[:query.limit]
    
    async def _get_updates_query(self, query: RegulatoryQuery) -> List[Dict[str, Any]]:
        """Process updates query."""
        updates = await self.track_standards_updates(
            [query.body] if query.body else None,
            query.date_from,
            [query.category] if query.category else None
        )
        
        return [u.dict() for u in updates[:query.limit]]
    
    async def _check_compliance_query(self, query: RegulatoryQuery) -> Dict[str, Any]:
        """Process compliance check query."""
        if not query.entity_id:
            raise ValueError("Entity ID required for compliance check")
        
        standards = [query.standard_id] if query.standard_id else []
        result = await self.monitor_compliance(query.entity_id, standards)
        
        return result
    
    async def _get_alerts_query(self, query: RegulatoryQuery) -> List[Dict[str, Any]]:
        """Process alerts query."""
        alerts = await self.get_regulatory_alerts(
            query.entity_id,
            None,  # severity not in query model
            query.date_from,
            query.limit
        )
        
        return [a.dict() for a in alerts]