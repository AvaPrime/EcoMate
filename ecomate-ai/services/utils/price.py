import csv
import os
from typing import List, Dict, Optional
import httpx
from selectolax.parser import HTMLParser
from datetime import datetime
import re


async def fetch_price(url: str, selector: str, timeout: int = 20) -> Optional[float]:
    """
    Fetch price from a URL using CSS selector.
    
    Args:
        url: The URL to fetch price from
        selector: CSS selector to find the price element
        timeout: Request timeout in seconds
        
    Returns:
        Price as float or None if not found
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            parser = HTMLParser(response.text)
            price_element = parser.css_first(selector)
            
            if not price_element:
                return None
                
            price_text = price_element.text().strip()
            
            # Extract numeric value from price text
            price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
            if price_match:
                return float(price_match.group())
                
    except Exception as e:
        print(f"Error fetching price from {url}: {e}")
        return None
    
    return None


async def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
    """
    Convert currency using a free exchange rate API.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code
        
    Returns:
        Converted amount
    """
    if from_currency == to_currency:
        return amount
        
    try:
        # Using exchangerate-api.com (free tier)
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if to_currency in data['rates']:
                rate = data['rates'][to_currency]
                return amount * rate
                
    except Exception as e:
        print(f"Error converting currency: {e}")
        
    return amount  # Return original amount if conversion fails


async def load_watchlist(file_path: str) -> List[Dict]:
    """
    Load price watchlist from CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        List of watchlist items
    """
    watchlist = []
    
    if not os.path.exists(file_path):
        return watchlist
        
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                watchlist.append({
                    'sku': row['sku'],
                    'url': row['url'],
                    'selector': row['selector'],
                    'currency': row['currency'],
                    'target_price': float(row['target_price']) if row['target_price'] else None
                })
    except Exception as e:
        print(f"Error loading watchlist: {e}")
        
    return watchlist


async def save_price_history(sku: str, price: float, currency: str, timestamp: datetime, file_path: str):
    """
    Save price data to history file.
    
    Args:
        sku: Product SKU
        price: Current price
        currency: Currency code
        timestamp: When the price was fetched
        file_path: Path to save the history
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Check if file exists to determine if we need headers
        file_exists = os.path.exists(file_path)
        
        with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['sku', 'price', 'currency', 'timestamp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
                
            writer.writerow({
                'sku': sku,
                'price': price,
                'currency': currency,
                'timestamp': timestamp.isoformat()
            })
            
    except Exception as e:
        print(f"Error saving price history: {e}")


def calculate_price_change(old_price: float, new_price: float) -> Dict:
    """
    Calculate price change percentage and absolute difference.
    
    Args:
        old_price: Previous price
        new_price: Current price
        
    Returns:
        Dictionary with change information
    """
    if old_price == 0:
        return {'percentage': 0, 'absolute': 0, 'direction': 'stable'}
        
    absolute_change = new_price - old_price
    percentage_change = (absolute_change / old_price) * 100
    
    if percentage_change > 0:
        direction = 'increase'
    elif percentage_change < 0:
        direction = 'decrease'
    else:
        direction = 'stable'
        
    return {
        'percentage': round(percentage_change, 2),
        'absolute': round(absolute_change, 2),
        'direction': direction
    }