from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

from .activities_price import (
    activity_fetch_prices,
    activity_generate_price_report,
    activity_open_price_pr
)


@workflow.defn
class PriceMonitorWorkflow:
    """
    Workflow for monitoring product prices and generating reports.
    """
    
    @workflow.run
    async def run(self, create_pr: bool = True) -> dict:
        """
        Execute the price monitoring workflow.
        
        Args:
            create_pr: Whether to create a GitHub PR with the report
            
        Returns:
            Dictionary with workflow results
        """
        workflow.logger.info("Starting price monitoring workflow")
        
        # Configure retry policy for activities
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=3,
            backoff_coefficient=2.0
        )
        
        try:
            # Step 1: Fetch current prices
            workflow.logger.info("Fetching current prices for all watchlist items")
            price_data = await workflow.execute_activity(
                activity_fetch_prices,
                schedule_to_close_timeout=timedelta(minutes=10),
                retry_policy=retry_policy
            )
            
            if not price_data:
                workflow.logger.warning("No price data retrieved")
                return {
                    'status': 'completed',
                    'message': 'No price data retrieved',
                    'prices_fetched': 0,
                    'report_generated': False,
                    'pr_created': False
                }
            
            workflow.logger.info(f"Successfully fetched prices for {len(price_data)} items")
            
            # Step 2: Generate price report
            workflow.logger.info("Generating price monitoring report")
            report_path = await workflow.execute_activity(
                activity_generate_price_report,
                price_data,
                schedule_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy
            )
            
            workflow.logger.info(f"Price report generated: {report_path}")
            
            # Step 3: Create GitHub PR (if requested)
            pr_result = None
            if create_pr:
                workflow.logger.info("Creating GitHub PR with price report")
                pr_result = await workflow.execute_activity(
                    activity_open_price_pr,
                    report_path,
                    schedule_to_close_timeout=timedelta(minutes=5),
                    retry_policy=retry_policy
                )
                workflow.logger.info(f"PR creation result: {pr_result}")
            
            # Count successful price fetches
            successful_fetches = sum(1 for item in price_data if item['status'] == 'success')
            failed_fetches = len(price_data) - successful_fetches
            
            # Check for alerts
            alerts = []
            if report_path:
                import csv
                try:
                    with open(report_path, 'r', newline='', encoding='utf-8') as csvfile:
                        reader = csv.DictReader(csvfile)
                        for row in reader:
                            if row['alert'] and row['alert'] != 'N/A':
                                alerts.append({
                                    'sku': row['sku'],
                                    'alert': row['alert'],
                                    'current_price': row['current_price']
                                })
                except Exception as e:
                    workflow.logger.warning(f"Error reading report for alerts: {e}")
            
            result = {
                'status': 'completed',
                'message': f'Price monitoring completed successfully. {successful_fetches} prices fetched, {failed_fetches} failed.',
                'prices_fetched': successful_fetches,
                'prices_failed': failed_fetches,
                'report_generated': True,
                'report_path': report_path,
                'pr_created': create_pr,
                'pr_result': pr_result,
                'alerts': alerts,
                'total_items': len(price_data)
            }
            
            workflow.logger.info(f"Price monitoring workflow completed: {result}")
            return result
            
        except Exception as e:
            error_msg = f"Price monitoring workflow failed: {str(e)}"
            workflow.logger.error(error_msg)
            return {
                'status': 'failed',
                'message': error_msg,
                'prices_fetched': 0,
                'report_generated': False,
                'pr_created': False
            }


@workflow.defn
class ScheduledPriceMonitorWorkflow:
    """
    Workflow for scheduled price monitoring (e.g., daily runs).
    """
    
    @workflow.run
    async def run(self) -> dict:
        """
        Execute scheduled price monitoring with automatic PR creation.
        
        Returns:
            Dictionary with workflow results
        """
        workflow.logger.info("Starting scheduled price monitoring workflow")
        
        # Always create PR for scheduled runs
        return await PriceMonitorWorkflow().run(create_pr=True)