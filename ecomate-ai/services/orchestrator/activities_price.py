import os
import csv
from datetime import datetime
from typing import List, Dict
from temporalio import activity

from ..utils.price import (
    fetch_price,
    convert_currency,
    load_watchlist,
    save_price_history,
    calculate_price_change
)
from ..utils.github_pr import open_pr


@activity.defn
async def activity_fetch_prices() -> List[Dict]:
    """
    Fetch current prices for all items in the watchlist.
    
    Returns:
        List of price data with current prices
    """
    watchlist_path = os.path.join(os.getcwd(), 'data', 'price_watchlist.csv')
    watchlist = await load_watchlist(watchlist_path)
    
    results = []
    timeout = int(os.getenv('REQUEST_TIMEOUT_SEC', 20))
    
    for item in watchlist:
        sku = item['sku']
        url = item['url']
        selector = item['selector']
        currency = item['currency']
        target_price = item['target_price']
        
        activity.logger.info(f"Fetching price for {sku} from {url}")
        
        current_price = await fetch_price(url, selector, timeout)
        
        if current_price is not None:
            # Save to price history
            history_path = os.path.join(os.getcwd(), 'data', 'price_history.csv')
            await save_price_history(sku, current_price, currency, datetime.now(), history_path)
            
            results.append({
                'sku': sku,
                'url': url,
                'current_price': current_price,
                'currency': currency,
                'target_price': target_price,
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            })
        else:
            activity.logger.warning(f"Failed to fetch price for {sku}")
            results.append({
                'sku': sku,
                'url': url,
                'current_price': None,
                'currency': currency,
                'target_price': target_price,
                'timestamp': datetime.now().isoformat(),
                'status': 'failed'
            })
    
    return results


@activity.defn
async def activity_generate_price_report(price_data: List[Dict]) -> str:
    """
    Generate a price monitoring report.
    
    Args:
        price_data: List of current price data
        
    Returns:
        Path to the generated report file
    """
    report_path = os.path.join(os.getcwd(), 'data', 'price_report.csv')
    
    # Load previous prices for comparison
    history_path = os.path.join(os.getcwd(), 'data', 'price_history.csv')
    previous_prices = {}
    
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    sku = row['sku']
                    if sku not in previous_prices:
                        previous_prices[sku] = []
                    previous_prices[sku].append({
                        'price': float(row['price']),
                        'timestamp': row['timestamp']
                    })
        except Exception as e:
            activity.logger.warning(f"Error reading price history: {e}")
    
    # Generate report
    report_data = []
    deviation_threshold = float(os.getenv('PRICE_DEVIATION_ALERT', 0.10))
    default_currency = os.getenv('CURRENCY_DEFAULT', 'ZAR')
    
    for item in price_data:
        sku = item['sku']
        current_price = item['current_price']
        currency = item['currency']
        target_price = item['target_price']
        
        if current_price is None:
            report_data.append({
                'sku': sku,
                'current_price': 'N/A',
                'currency': currency,
                'target_price': target_price or 'N/A',
                'price_change_pct': 'N/A',
                'price_change_abs': 'N/A',
                'alert': 'FETCH_FAILED',
                'converted_price': 'N/A',
                'timestamp': item['timestamp']
            })
            continue
        
        # Convert to default currency if different
        converted_price = current_price
        if currency != default_currency:
            converted_price = await convert_currency(current_price, currency, default_currency)
        
        # Calculate price change if we have previous data
        price_change_pct = 'N/A'
        price_change_abs = 'N/A'
        alert = ''
        
        if sku in previous_prices and len(previous_prices[sku]) > 1:
            # Get the second-to-last price (previous price)
            prev_price = previous_prices[sku][-2]['price']
            change_info = calculate_price_change(prev_price, current_price)
            price_change_pct = change_info['percentage']
            price_change_abs = change_info['absolute']
            
            # Check for significant deviation
            if abs(price_change_pct) >= (deviation_threshold * 100):
                alert = f"PRICE_{change_info['direction'].upper()}"
        
        # Check target price alert
        if target_price and current_price <= target_price:
            alert = 'TARGET_REACHED'
        
        report_data.append({
            'sku': sku,
            'current_price': current_price,
            'currency': currency,
            'target_price': target_price or 'N/A',
            'price_change_pct': price_change_pct,
            'price_change_abs': price_change_abs,
            'alert': alert,
            'converted_price': round(converted_price, 2) if converted_price != current_price else current_price,
            'timestamp': item['timestamp']
        })
    
    # Write report to CSV
    try:
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'sku', 'current_price', 'currency', 'target_price',
                'price_change_pct', 'price_change_abs', 'alert',
                'converted_price', 'timestamp'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(report_data)
            
        activity.logger.info(f"Price report generated: {report_path}")
        return report_path
        
    except Exception as e:
        activity.logger.error(f"Error generating price report: {e}")
        raise


@activity.defn
async def activity_open_price_pr(report_path: str) -> str:
    """
    Open a GitHub PR with the price monitoring report.
    
    Args:
        report_path: Path to the price report CSV file
        
    Returns:
        PR URL or error message
    """
    try:
        repo = os.getenv('DOCS_REPO')
        if not repo:
            return "Error: DOCS_REPO environment variable not set"
        
        # Read the report file
        if not os.path.exists(report_path):
            return f"Error: Report file not found at {report_path}"
        
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        # Create branch name with timestamp
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        branch_name = f"price-monitor-{timestamp}"
        
        # Prepare commit message and PR details
        commit_message = f"Price monitoring report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        pr_title = f"🏷️ Price Monitor Report - {datetime.now().strftime('%Y-%m-%d')}"
        pr_body = f"""# Price Monitoring Report

Automated price monitoring report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.

## Report Summary

This report contains current pricing information for monitored products.

**Report file:** `price_reports/price_report_{timestamp}.csv`

---
*This PR was automatically generated by the EcoMate Price Monitor Agent*
"""
        
        # Target file path in the docs repo
        target_file = f"price_reports/price_report_{timestamp}.csv"
        
        result = await open_pr(
            repo=repo,
            branch_name=branch_name,
            file_path=target_file,
            file_content=report_content,
            commit_message=commit_message,
            pr_title=pr_title,
            pr_body=pr_body
        )
        
        activity.logger.info(f"Price monitoring PR result: {result}")
        return result
        
    except Exception as e:
        error_msg = f"Error opening price monitoring PR: {e}"
        activity.logger.error(error_msg)
        return error_msg