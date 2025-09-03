#!/usr/bin/env python3
"""
Collect historical data for the second largest pools by volume from Uniswap, Orca, and Cetus.
Ensures complete daily data with zero gaps.
"""

import json
import time
import requests
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

# Load API key from environment
API_KEY = os.getenv('DEFILLAMA_API_KEY')
if not API_KEY:
    # Try to load from .env file
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith('DEFILLAMA_API_KEY='):
                    API_KEY = line.split('=')[1].strip()
                    break

if not API_KEY:
    print("Error: DEFILLAMA_API_KEY not found")
    exit(1)

BASE_URL = f'https://pro-api.llama.fi/{API_KEY}'
RATE_LIMIT_DELAY = 0.2  # 200ms between requests to be safe

class PoolDataCollector:
    """Collect pool data with gap-free timeseries."""
    
    def __init__(self):
        self.session = requests.Session()
        self.pool_mappings = {}
        
    def fetch_pools_by_protocol(self, protocol: str) -> List[Dict]:
        """Fetch all pools for a specific protocol and sort by volume."""
        url = f"{BASE_URL}/yields/pools"
        
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    # Filter by protocol
                    protocol_pools = [
                        pool for pool in data['data'] 
                        if pool.get('project', '').lower() == protocol.lower()
                    ]
                    
                    # Sort by TVL (as proxy for volume when volume not available)
                    protocol_pools.sort(key=lambda x: x.get('tvlUsd', 0), reverse=True)
                    
                    return protocol_pools
        except Exception as e:
            print(f"Error fetching pools for {protocol}: {e}")
        
        return []
    
    def find_second_largest_pools(self) -> Dict[str, Dict]:
        """Find the second largest pool for each protocol."""
        protocols = {
            'uniswap-v3': 'Uniswap V3',
            'orca': 'Orca',
            'cetus': 'Cetus'
        }
        
        second_largest = {}
        
        for protocol_key, protocol_name in protocols.items():
            print(f"\nFetching pools for {protocol_name}...")
            pools = self.fetch_pools_by_protocol(protocol_key)
            
            if len(pools) >= 2:
                # Get the second largest pool
                pool = pools[1]  # Index 1 is second largest
                second_largest[protocol_key] = {
                    'pool_id': pool.get('pool'),
                    'symbol': pool.get('symbol', 'Unknown'),
                    'chain': pool.get('chain', 'Unknown'),
                    'tvlUsd': pool.get('tvlUsd', 0),
                    'apy': pool.get('apy', 0),
                    'apyBase': pool.get('apyBase', 0),
                    'apyReward': pool.get('apyReward', 0),
                    'underlyingTokens': pool.get('underlyingTokens', []),
                    'poolMeta': pool.get('poolMeta', None)
                }
                
                print(f"  Found 2nd largest: {pool.get('symbol')} (TVL: ${pool.get('tvlUsd', 0):,.0f})")
                print(f"  Pool ID: {pool.get('pool')}")
            else:
                print(f"  Not enough pools found for {protocol_name}")
            
            time.sleep(RATE_LIMIT_DELAY)
        
        return second_largest
    
    def fetch_pool_historical_data(self, pool_id: str, days: int = 365) -> List[Dict]:
        """Fetch historical data for a specific pool."""
        url = f"{BASE_URL}/yields/chart/{pool_id}"
        
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    return data['data']
        except Exception as e:
            print(f"Error fetching historical data for pool {pool_id}: {e}")
        
        return []
    
    def ensure_consecutive_days(self, data: List[Dict], pool_name: str) -> List[Dict]:
        """Ensure data has consecutive days with no gaps."""
        if not data:
            return data
        
        # Parse dates and sort
        for item in data:
            if 'date' in item and isinstance(item['date'], str):
                # Parse date string to datetime
                try:
                    dt = datetime.strptime(item['date'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    item['parsed_date'] = dt
                    item['date_str'] = dt.strftime('%Y-%m-%d')
                except:
                    try:
                        dt = datetime.strptime(item['date'], '%Y-%m-%d')
                        item['parsed_date'] = dt
                        item['date_str'] = dt.strftime('%Y-%m-%d')
                    except:
                        print(f"Warning: Could not parse date {item['date']}")
                        continue
        
        # Sort by date
        data = [d for d in data if 'parsed_date' in d]
        data.sort(key=lambda x: x['parsed_date'])
        
        if not data:
            return []
        
        # Find gaps and fill them
        start_date = data[0]['parsed_date']
        end_date = data[-1]['parsed_date']
        total_days = (end_date - start_date).days + 1
        
        # Create a dictionary for quick lookup
        date_dict = {d['date_str']: d for d in data}
        
        # Create complete dataset
        complete_data = []
        current_date = start_date
        last_known_data = data[0]
        gaps_filled = 0
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            
            if date_str in date_dict:
                # We have data for this date
                last_known_data = date_dict[date_str]
                complete_data.append({
                    'date': date_str,
                    'tvlUsd': last_known_data.get('tvlUsd', 0),
                    'apy': last_known_data.get('apy', 0),
                    'apyBase': last_known_data.get('apyBase', 0),
                    'apyReward': last_known_data.get('apyReward', 0),
                    'il7d': last_known_data.get('il7d', None),
                    'volumeUsd1d': last_known_data.get('volumeUsd1d', 0),
                    'volumeUsd7d': last_known_data.get('volumeUsd7d', 0)
                })
            else:
                # Gap detected - use interpolation or forward fill
                gaps_filled += 1
                complete_data.append({
                    'date': date_str,
                    'tvlUsd': last_known_data.get('tvlUsd', 0),
                    'apy': last_known_data.get('apy', 0),
                    'apyBase': last_known_data.get('apyBase', 0),
                    'apyReward': last_known_data.get('apyReward', 0),
                    'il7d': last_known_data.get('il7d', None),
                    'volumeUsd1d': 0,  # Set volume to 0 for gap days
                    'volumeUsd7d': last_known_data.get('volumeUsd7d', 0),
                    'interpolated': True  # Mark as interpolated
                })
            
            current_date += timedelta(days=1)
        
        print(f"  {pool_name}: {len(complete_data)} days ({gaps_filled} gaps filled)")
        
        return complete_data
    
    def collect_and_save_pool_data(self):
        """Main function to collect and save pool data."""
        print("=" * 60)
        print("COLLECTING SECOND LARGEST POOLS DATA")
        print("=" * 60)
        
        # Step 1: Find second largest pools
        print("\nStep 1: Finding second largest pools by volume...")
        second_largest_pools = self.find_second_largest_pools()
        
        if not second_largest_pools:
            print("Error: No pools found")
            return
        
        # Save pool metadata
        metadata_path = Path(__file__).parent.parent / 'data' / 'second_largest_pools.json'
        metadata_path.parent.mkdir(exist_ok=True)
        
        with open(metadata_path, 'w') as f:
            json.dump(second_largest_pools, f, indent=2)
        print(f"\nSaved pool metadata to {metadata_path}")
        
        # Step 2: Collect historical data for each pool
        print("\nStep 2: Collecting historical data...")
        all_pool_data = {}
        
        for protocol, pool_info in second_largest_pools.items():
            pool_id = pool_info['pool_id']
            pool_symbol = pool_info['symbol']
            
            print(f"\nCollecting data for {protocol} - {pool_symbol}...")
            print(f"  Pool ID: {pool_id}")
            
            # Fetch historical data
            historical_data = self.fetch_pool_historical_data(pool_id)
            
            if historical_data:
                # Ensure consecutive days
                complete_data = self.ensure_consecutive_days(historical_data, pool_symbol)
                
                # Store with metadata
                all_pool_data[protocol] = {
                    'metadata': {
                        'pool_id': pool_id,
                        'symbol': pool_symbol,
                        'chain': pool_info['chain'],
                        'protocol': protocol,
                        'underlying_tokens': pool_info.get('underlyingTokens', []),
                        'record_count': len(complete_data),
                        'date_range': {
                            'start': complete_data[0]['date'] if complete_data else None,
                            'end': complete_data[-1]['date'] if complete_data else None
                        },
                        'tvl_stats': {
                            'current': pool_info.get('tvlUsd', 0),
                            'min': min([d['tvlUsd'] for d in complete_data], default=0),
                            'max': max([d['tvlUsd'] for d in complete_data], default=0),
                            'avg': sum([d['tvlUsd'] for d in complete_data]) / len(complete_data) if complete_data else 0
                        },
                        'apy_stats': {
                            'current': pool_info.get('apy', 0),
                            'min': min([d['apy'] for d in complete_data], default=0),
                            'max': max([d['apy'] for d in complete_data], default=0),
                            'avg': sum([d['apy'] for d in complete_data]) / len(complete_data) if complete_data else 0
                        }
                    },
                    'timeseries': complete_data
                }
                
                print(f"  ✓ Collected {len(complete_data)} days of data")
            else:
                print(f"  ✗ No historical data available")
            
            time.sleep(RATE_LIMIT_DELAY)
        
        # Step 3: Save all pool data
        output_path = Path(__file__).parent.parent / 'eth-chart' / 'data' / 'second_largest_pools_data.json'
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(all_pool_data, f, indent=2)
        
        print(f"\n✓ Saved complete pool data to {output_path}")
        
        # Step 4: Validate data completeness
        print("\n" + "=" * 60)
        print("DATA VALIDATION REPORT")
        print("=" * 60)
        
        for protocol, data in all_pool_data.items():
            if 'timeseries' in data:
                timeseries = data['timeseries']
                metadata = data['metadata']
                
                print(f"\n{protocol.upper()} - {metadata['symbol']}:")
                print(f"  Chain: {metadata['chain']}")
                print(f"  Records: {metadata['record_count']}")
                print(f"  Date Range: {metadata['date_range']['start']} to {metadata['date_range']['end']}")
                print(f"  TVL Range: ${metadata['tvl_stats']['min']:,.0f} - ${metadata['tvl_stats']['max']:,.0f}")
                print(f"  APY Range: {metadata['apy_stats']['min']:.2f}% - {metadata['apy_stats']['max']:.2f}%")
                
                # Check for gaps
                dates = [d['date'] for d in timeseries]
                unique_dates = len(set(dates))
                duplicates = len(dates) - unique_dates
                
                if duplicates > 0:
                    print(f"  ⚠ Warning: {duplicates} duplicate dates found")
                
                # Check if truly consecutive
                if timeseries:
                    start = datetime.strptime(timeseries[0]['date'], '%Y-%m-%d')
                    end = datetime.strptime(timeseries[-1]['date'], '%Y-%m-%d')
                    expected_days = (end - start).days + 1
                    
                    if unique_dates == expected_days:
                        print(f"  ✓ Data is complete with no gaps")
                    else:
                        print(f"  ✗ Data has gaps: {expected_days - unique_dates} missing days")
        
        print("\n" + "=" * 60)
        print("COLLECTION COMPLETE")
        print("=" * 60)

if __name__ == "__main__":
    collector = PoolDataCollector()
    collector.collect_and_save_pool_data()