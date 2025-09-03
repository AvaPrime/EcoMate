#!/usr/bin/env python3
"""
Regulatory Monitor Service - Example Usage

This script demonstrates how to use the Regulatory Monitor Service
for compliance tracking, standards monitoring, and regulatory reporting.

Usage:
    python example_usage.py

Requirements:
    - Service running on localhost:8080
    - Valid API keys configured
    - Redis available for caching
"""

import asyncio
import logging
from datetime import datetime, timedelta

from services.regulatory import (
    RegulatoryService,
    RegulatoryClient,
    RegulatoryConfig
)
from services.regulatory.models import (
    StandardsBody,
    ComplianceStatus,
    AlertSeverity,
    StandardCategory,
    RegulatoryQuery,
    BatchRegulatoryRequest
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RegulatoryMonitorDemo:
    """Demonstration class for Regulatory Monitor Service."""
    
    def __init__(self):
        """Initialize the demo with service configuration."""
        self.config = RegulatoryConfig(
            api_keys={
                "SANS": "demo_sans_key",
                "ISO": "demo_iso_key",
                "EPA": "demo_epa_key",
                "OSHA": "demo_osha_key"
            },
            cache_ttl=1800,  # 30 minutes
            max_retries=3,
            request_timeout=30,
            enable_background_updates=True,
            update_check_interval=3600,  # 1 hour
            alert_thresholds={
                "compliance_score": 0.75,
                "days_until_expiry": 30
            }
        )
        
        self.service = RegulatoryService(config=self.config)
        self.entity_id = "demo-company-001"
        
    async def demonstrate_basic_operations(self):
        """Demonstrate basic regulatory operations."""
        logger.info("=== Basic Operations Demo ===")
        
        # 1. Search for standards
        logger.info("1. Searching for security standards...")
        
        async with RegulatoryClient(self.config) as client:
            # Search ISO standards
            iso_results = await client.search_standards(
                standards_body=StandardsBody.ISO,
                query="information security",
                category=StandardCategory.INFORMATION_SECURITY,
                limit=5
            )
            
            logger.info(f"Found {len(iso_results)} ISO security standards:")
            for standard in iso_results[:3]:
                logger.info(f"  - {standard.standard_id}: {standard.title}")
            
            # Get specific standard details
            if iso_results:
                standard_detail = await client.get_standard(
                    standard_id=iso_results[0].standard_id
                )
                logger.info(f"\nDetailed info for {standard_detail.standard_id}:")
                logger.info(f"  Status: {standard_detail.status}")
                logger.info(f"  Last Updated: {standard_detail.last_updated}")
                logger.info(f"  Requirements: {len(standard_detail.requirements)}")
    
    async def demonstrate_compliance_monitoring(self):
        """Demonstrate compliance monitoring capabilities."""
        logger.info("\n=== Compliance Monitoring Demo ===")
        
        # Define standards to monitor
        standards_to_monitor = [
            "ISO-27001",  # Information Security Management
            "ISO-14001",  # Environmental Management
            "SANS-20",    # Critical Security Controls
            "EPA-CAA"     # Clean Air Act
        ]
        
        logger.info(f"2. Setting up compliance monitoring for {self.entity_id}...")
        
        # Start compliance monitoring
        monitoring_result = await self.service.monitor_compliance(
            entity_id=self.entity_id,
            standards=standards_to_monitor,
            check_interval_hours=24
        )
        
        logger.info(f"Monitoring setup: {monitoring_result.monitoring_id}")
        logger.info(f"Overall status: {monitoring_result.overall_status}")
        
        # Check current compliance status
        logger.info("\n3. Checking current compliance status...")
        
        compliance_status = await self.service.check_compliance(
            entity_id=self.entity_id,
            standards=standards_to_monitor
        )
        
        logger.info(f"Compliance checks completed: {len(compliance_status.checks)}")
        for check in compliance_status.checks:
            status_emoji = "✅" if check.status == ComplianceStatus.COMPLIANT else "❌"
            logger.info(f"  {status_emoji} {check.standard_id}: {check.status.value}")
            if check.issues:
                for issue in check.issues[:2]:  # Show first 2 issues
                    logger.info(f"    - Issue: {issue}")
    
    async def demonstrate_standards_updates(self):
        """Demonstrate standards update tracking."""
        logger.info("\n=== Standards Updates Demo ===")
        
        logger.info("4. Tracking standards updates...")
        
        # Track updates from multiple standards bodies
        since_date = (datetime.now() - timedelta(days=30)).isoformat()
        
        updates_result = await self.service.track_standards_updates(
            standards_bodies=[StandardsBody.ISO, StandardsBody.SANS, StandardsBody.EPA],
            categories=[StandardCategory.INFORMATION_SECURITY, StandardCategory.ENVIRONMENTAL],
            since_date=since_date
        )
        
        logger.info(f"Found {len(updates_result.updates)} recent updates:")
        for update in updates_result.updates[:5]:  # Show first 5
            logger.info(f"  📋 {update.standard_id}: {update.title}")
            logger.info(f"     Type: {update.update_type.value}, Date: {update.update_date}")
            if update.summary:
                logger.info(f"     Summary: {update.summary[:100]}...")
    
    async def demonstrate_compliance_reporting(self):
        """Demonstrate compliance report generation."""
        logger.info("\n=== Compliance Reporting Demo ===")
        
        logger.info("5. Generating comprehensive compliance report...")
        
        report = await self.service.generate_compliance_report(
            entity_id=self.entity_id,
            standards=["ISO-27001", "ISO-14001", "SANS-20"],
            include_recommendations=True,
            include_historical_data=True
        )
        
        logger.info(f"Report generated: {report.report_id}")
        logger.info(f"Overall compliance score: {report.overall_compliance_score:.2f}")
        logger.info(f"Standards evaluated: {len(report.standard_results)}")
        
        # Show summary by standard
        for result in report.standard_results:
            score_emoji = "🟢" if result.compliance_score > 0.8 else "🟡" if result.compliance_score > 0.6 else "🔴"
            logger.info(f"  {score_emoji} {result.standard_id}: {result.compliance_score:.2f}")
            logger.info(f"     Compliant: {result.compliant_requirements}, Non-compliant: {result.non_compliant_requirements}")
        
        # Show recommendations
        if report.recommendations:
            logger.info("\nTop recommendations:")
            for rec in report.recommendations[:3]:
                logger.info(f"  💡 {rec.title}")
                logger.info(f"     Priority: {rec.priority}, Impact: {rec.estimated_impact}")
    
    async def demonstrate_regulatory_alerts(self):
        """Demonstrate regulatory alert system."""
        logger.info("\n=== Regulatory Alerts Demo ===")
        
        logger.info("6. Retrieving regulatory alerts...")
        
        # Get high-priority alerts
        alerts = await self.service.get_regulatory_alerts(
            entity_id=self.entity_id,
            severity=AlertSeverity.HIGH,
            limit=10
        )
        
        logger.info(f"Found {len(alerts)} high-priority alerts:")
        for alert in alerts:
            severity_emoji = {
                AlertSeverity.LOW: "🔵",
                AlertSeverity.MEDIUM: "🟡",
                AlertSeverity.HIGH: "🟠",
                AlertSeverity.CRITICAL: "🔴"
            }.get(alert.severity, "⚪")
            
            logger.info(f"  {severity_emoji} {alert.title}")
            logger.info(f"     Standard: {alert.standard_id}, Created: {alert.created_at}")
            if alert.description:
                logger.info(f"     Description: {alert.description[:100]}...")
    
    async def demonstrate_impact_assessment(self):
        """Demonstrate regulatory impact assessment."""
        logger.info("\n=== Regulatory Impact Assessment Demo ===")
        
        logger.info("7. Assessing regulatory impact of proposed changes...")
        
        # Simulate proposed changes
        proposed_changes = [
            "Implement new multi-factor authentication system",
            "Upgrade data encryption to AES-256",
            "Establish new environmental monitoring procedures",
            "Update incident response procedures"
        ]
        
        affected_standards = ["ISO-27001", "ISO-14001", "SANS-20"]
        
        impact_assessment = await self.service.assess_regulatory_impact(
            proposed_changes=proposed_changes,
            affected_standards=affected_standards,
            implementation_timeline="2024-06-01"
        )
        
        logger.info(f"Impact assessment completed: {impact_assessment.assessment_id}")
        logger.info(f"Overall impact score: {impact_assessment.overall_impact_score:.2f}")
        
        # Show impact by standard
        for impact in impact_assessment.standard_impacts:
            impact_emoji = "🟢" if impact.impact_score < 0.3 else "🟡" if impact.impact_score < 0.7 else "🔴"
            logger.info(f"  {impact_emoji} {impact.standard_id}: Impact {impact.impact_score:.2f}")
            if impact.affected_requirements:
                logger.info(f"     Affected requirements: {len(impact.affected_requirements)}")
        
        # Show recommendations
        if impact_assessment.recommendations:
            logger.info("\nImplementation recommendations:")
            for rec in impact_assessment.recommendations[:3]:
                logger.info(f"  📋 {rec}")
    
    async def demonstrate_batch_processing(self):
        """Demonstrate batch query processing."""
        logger.info("\n=== Batch Processing Demo ===")
        
        logger.info("8. Processing batch regulatory queries...")
        
        # Create batch queries
        queries = [
            RegulatoryQuery(
                query_id="security_standards",
                standards_body=StandardsBody.ISO,
                query_text="cybersecurity framework",
                filters={"category": "information_security"}
            ),
            RegulatoryQuery(
                query_id="environmental_regs",
                standards_body=StandardsBody.EPA,
                query_text="air quality monitoring",
                filters={"category": "environmental"}
            ),
            RegulatoryQuery(
                query_id="safety_standards",
                standards_body=StandardsBody.OSHA,
                query_text="workplace safety",
                filters={"category": "occupational_safety"}
            )
        ]
        
        batch_request = BatchRegulatoryRequest(queries=queries)
        
        batch_result = await self.service.process_batch_request(batch_request)
        
        logger.info(f"Batch processing completed: {batch_result.batch_id}")
        logger.info(f"Successful queries: {batch_result.successful_count}/{batch_result.total_count}")
        
        # Show results summary
        for result in batch_result.results:
            status_emoji = "✅" if result.success else "❌"
            logger.info(f"  {status_emoji} {result.query_id}: {len(result.standards) if result.standards else 0} standards found")
            if result.error:
                logger.info(f"     Error: {result.error}")
    
    async def demonstrate_service_info(self):
        """Demonstrate service information retrieval."""
        logger.info("\n=== Service Information Demo ===")
        
        logger.info("9. Retrieving service information...")
        
        # Get supported standards bodies
        supported_bodies = await self.service.get_supported_standards_bodies()
        logger.info(f"Supported standards bodies: {[body.value for body in supported_bodies]}")
        
        # Get supported categories
        supported_categories = await self.service.get_supported_categories()
        logger.info(f"Supported categories: {[cat.value for cat in supported_categories]}")
        
        # Service health check
        async with RegulatoryClient(self.config) as client:
            # This would typically be a health check endpoint
            logger.info("Service health: ✅ Operational")
    
    async def run_complete_demo(self):
        """Run the complete demonstration."""
        logger.info("🚀 Starting Regulatory Monitor Service Demo")
        logger.info("=" * 50)
        
        try:
            await self.demonstrate_basic_operations()
            await self.demonstrate_compliance_monitoring()
            await self.demonstrate_standards_updates()
            await self.demonstrate_compliance_reporting()
            await self.demonstrate_regulatory_alerts()
            await self.demonstrate_impact_assessment()
            await self.demonstrate_batch_processing()
            await self.demonstrate_service_info()
            
            logger.info("\n" + "=" * 50)
            logger.info("✅ Demo completed successfully!")
            logger.info("\n📊 Summary of capabilities demonstrated:")
            logger.info("  • Standards search and retrieval")
            logger.info("  • Compliance monitoring and checking")
            logger.info("  • Standards update tracking")
            logger.info("  • Compliance report generation")
            logger.info("  • Regulatory alert management")
            logger.info("  • Regulatory impact assessment")
            logger.info("  • Batch query processing")
            logger.info("  • Service information retrieval")
            
        except Exception as e:
            logger.error(f"❌ Demo failed with error: {e}")
            raise


async def main():
    """Main function to run the demo."""
    demo = RegulatoryMonitorDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())