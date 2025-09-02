#!/usr/bin/env python3
"""
Data Quality Pipeline for Timeseries Validation and Gap Filling

This is the standardized pipeline for ensuring complete, gap-free timeseries data
for all tokens and pools. Run this for every new data ingestion.

Usage:
    python3 data_quality_pipeline.py --token BTC
    python3 data_quality_pipeline.py --pool uniswap-v3
    python3 data_quality_pipeline.py --all
"""

import json
import time
import requests
import os
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

API_KEY = os.getenv('DEFILLAMA_API_KEY')
if not API_KEY:
    print("Error: DEFILLAMA_API_KEY environment variable not set")
    exit(1)

BASE_URL = f'https://pro-api.llama.fi/{API_KEY}'

# Token contract mappings
TOKEN_CONTRACTS = {
    'BTC': 'coingecko:bitcoin',
    'ETH': 'coingecko:ethereum', 
    'SOL': 'coingecko:solana',
    'SUI': 'coingecko:sui'
}

# Pool ID mappings
POOL_IDS = {
    'uniswap-v3': 'c5599b3a-ea73-4017-a867-72eb971301d1',
    'orca-dex': 'a5c85bc8-eb41-45c0-a520-d18d7529c0d8',
    'cetus-amm': '1249e3d1-af05-4308-a9d8-75127ec2e4c2'
}

class DataQualityPipeline:
    """Standardized data quality validation and gap filling."""
    
    def __init__(self):
        self.rate_limit_delay = 0.15
        self.batch_size = 50
    
    def parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object."""
        formats = ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ']
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        try:
            return datetime.fromtimestamp(float(date_str))
        except (ValueError, TypeError):
            pass
        
        raise ValueError(f"Unable to parse date: {date_str}")
    
    def validate_consecutive_days(self, dates: List[str]) -> Dict[str, Any]:
        """Validate that dates form consecutive sequence."""
        if not dates:
            return {'valid': False, 'error': 'No dates provided'}
        
        try:
            parsed_dates = sorted([self.parse_date(date) for date in dates])
            start_date = parsed_dates[0]
            end_date = parsed_dates[-1]
            
            expected_days = (end_date - start_date).days + 1
            actual_days = len(parsed_dates)
            
            # Find missing days
            missing_days = []
            current_date = start_date
            date_set = set(parsed_dates)
            
            while current_date <= end_date:
                if current_date not in date_set:
                    missing_days.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
            
            return {
                'valid': len(missing_days) == 0,
                'total_days': actual_days,
                'expected_days': expected_days,
                'missing_days': missing_days,
                'date_range': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d')
                },
                'gaps_found': len(missing_days)
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def fetch_token_price(self, symbol: str, date_str: str) -> Optional[Dict]:
        """Fetch single token price for specific date."""
        contract_id = TOKEN_CONTRACTS.get(symbol)
        if not contract_id:
            return None
        
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').replace(hour=12)
            timestamp = int(date_obj.timestamp())
            
            url = f"{BASE_URL}/coins/prices/historical/{timestamp}/{contract_id}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'coins' in data:
                    coin_data = next(iter(data['coins'].values()), {})
                    if 'price' in coin_data:
                        return {
                            'date': date_str,
                            'price': coin_data['price'],
                            'confidence': coin_data.get('confidence', 0.99)
                        }
        except Exception as e:
            print(f"    Error fetching {symbol} {date_str}: {e}")
        
        return None
    
    def fill_token_gaps(self, symbol: str) -> bool:
        """Fill all gaps for a specific token."""
        print(f"\n=== PROCESSING TOKEN: {symbol} ===")
        
        data_file = '../eth-chart/data/all_tokens_data.json'
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        if symbol not in data or 'timeseries' not in data[symbol]:
            print(f"No data found for {symbol}")
            return False
        
        dates = [item['date'] for item in data[symbol]['timeseries']]
        validation = self.validate_consecutive_days(dates)
        
        if validation['valid']:
            print(f"✓ {symbol} already complete ({validation['total_days']} days)")
            return True
        
        print(f"Found {validation['gaps_found']} missing days")
        missing_dates = validation['missing_days']
        
        # Process in batches
        filled_count = 0
        for i in range(0, len(missing_dates), self.batch_size):
            batch = missing_dates[i:i + self.batch_size]
            print(f"  Batch {i//self.batch_size + 1}: Processing {len(batch)} dates")
            
            for date_str in batch:
                price_data = self.fetch_token_price(symbol, date_str)
                if price_data:
                    data[symbol]['timeseries'].append(price_data)
                    filled_count += 1
                
                time.sleep(self.rate_limit_delay)
            
            # Save progress
            self._update_token_metadata(data[symbol])
            with open(data_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"    Filled {filled_count} gaps so far")
        
        print(f"✓ {symbol} complete: Filled {filled_count} missing dates")
        return filled_count > 0
    
    def _update_token_metadata(self, token_data: Dict):
        """Update token metadata after adding new data."""
        if not token_data['timeseries']:
            return
        
        # Sort and deduplicate
        token_data['timeseries'].sort(key=lambda x: x['date'])
        seen_dates = set()
        unique_data = []
        for item in token_data['timeseries']:
            if item['date'] not in seen_dates:
                seen_dates.add(item['date'])
                unique_data.append(item)
        
        token_data['timeseries'] = unique_data
        
        # Update metadata
        prices = [item['price'] for item in unique_data]
        token_data['metadata']['record_count'] = len(unique_data)
        token_data['metadata']['date_range']['start'] = unique_data[0]['date']
        token_data['metadata']['date_range']['end'] = unique_data[-1]['date']
        token_data['metadata']['price_stats'] = {
            'min': min(prices),
            'max': max(prices),
            'avg': sum(prices) / len(prices),
            'volatility': (max(prices) - min(prices)) / sum(prices) * len(prices)
        }
    
    def validate_all_data(self):
        """Validate all token and pool data for completeness."""
        print("=== DATA QUALITY VALIDATION ===")
        
        # Validate tokens
        with open('../eth-chart/data/all_tokens_data.json', 'r') as f:
            token_data = json.load(f)
        
        token_results = {}
        for token, data in token_data.items():
            if data and 'timeseries' in data:
                dates = [item['date'] for item in data['timeseries']]
                token_results[token] = self.validate_consecutive_days(dates)
        
        # Validate pools
        try:
            with open('../eth-chart/data/pool_data.json', 'r') as f:
                pool_data = json.load(f)
            
            pool_results = {}
            for pool, data in pool_data.items():
                if data and 'timeseries' in data:
                    dates = [item['date'] for item in data['timeseries']]
                    pool_results[pool] = self.validate_consecutive_days(dates)
        except FileNotFoundError:
            pool_results = {}
        
        # Print results
        print("\nTOKEN DATA VALIDATION:")
        all_valid = True
        for token, result in token_results.items():
            if 'error' in result:
                print(f"  {token}: ERROR - {result['error']}")
                all_valid = False
            else:
                status = "✓ PASS" if result['valid'] else "✗ FAIL"
                print(f"  {token}: {status} ({result['total_days']}/{result['expected_days']} days)")
                if not result['valid']:
                    all_valid = False
                    print(f"    Missing {result['gaps_found']} days")
        
        print("\nPOOL DATA VALIDATION:")
        for pool, result in pool_results.items():
            if 'error' in result:
                print(f"  {pool}: ERROR - {result['error']}")
                all_valid = False
            else:
                status = "✓ PASS" if result['valid'] else "✗ FAIL"
                print(f"  {pool}: {status} ({result['total_days']}/{result['expected_days']} days)")
                if not result['valid']:
                    all_valid = False
                    print(f"    Missing {result['gaps_found']} days")
        
        if all_valid:
            print("\n✅ ALL DATA VALIDATED - NO GAPS FOUND")
        else:
            print("\n❌ GAPS DETECTED - RUN GAP FILLING")
        
        return all_valid

def main():
    parser = argparse.ArgumentParser(description='Data Quality Pipeline')
    parser.add_argument('--token', help='Process specific token (BTC, ETH, SOL, SUI)')
    parser.add_argument('--pool', help='Process specific pool (uniswap-v3, orca-dex, cetus-amm)')
    parser.add_argument('--all', action='store_true', help='Process all tokens and pools')
    parser.add_argument('--validate-only', action='store_true', help='Only validate, do not fill gaps')
    
    args = parser.parse_args()
    pipeline = DataQualityPipeline()
    
    if args.validate_only:
        pipeline.validate_all_data()
        return
    
    if args.all:
        for token in TOKEN_CONTRACTS.keys():
            pipeline.fill_token_gaps(token)
        print("\n=== FINAL VALIDATION ===")
        pipeline.validate_all_data()
    elif args.token:
        if args.token in TOKEN_CONTRACTS:
            pipeline.fill_token_gaps(args.token)
        else:
            print(f"Unknown token: {args.token}")
    elif args.pool:
        print(f"Pool processing not yet implemented for {args.pool}")
    else:
        pipeline.validate_all_data()

if __name__ == "__main__":
    main()