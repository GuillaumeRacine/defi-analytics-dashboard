#!/usr/bin/env python3
"""
Fetch and analyze available pools from DeFillama to find the best pools for each protocol.
"""

import json
import time
import requests
import os
from pathlib import Path
from typing import List, Dict

# Load API key
API_KEY = os.getenv('DEFILLAMA_API_KEY')
if not API_KEY:
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

def fetch_all_pools():
    """Fetch all available pools from DeFillama."""
    url = f"{BASE_URL}/yields/pools"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"Response status: {data.get('status')}")
            
            if 'data' in data:
                pools = data['data']
                print(f"Total pools found: {len(pools)}")
                
                # Group by protocol
                protocols = {}
                for pool in pools:
                    project = pool.get('project', 'unknown')
                    if project not in protocols:
                        protocols[project] = []
                    protocols[project].append(pool)
                
                # Sort protocols by number of pools
                sorted_protocols = sorted(protocols.items(), key=lambda x: len(x[1]), reverse=True)
                
                print("\nProtocols with most pools:")
                for protocol, pools_list in sorted_protocols[:20]:
                    print(f"  {protocol}: {len(pools_list)} pools")
                
                # Look specifically for our target protocols
                target_protocols = ['uniswap-v3', 'uniswap', 'orca', 'cetus', 'raydium', 'curve', 'balancer-v2']
                
                print("\n" + "="*60)
                print("TARGET PROTOCOLS ANALYSIS")
                print("="*60)
                
                found_pools = {}
                
                for target in target_protocols:
                    matching_pools = []
                    for pool in data['data']:
                        project = pool.get('project', '').lower()
                        # Check various matching patterns
                        if target.lower() in project or project in target.lower():
                            matching_pools.append(pool)
                    
                    if matching_pools:
                        # Sort by TVL
                        matching_pools.sort(key=lambda x: x.get('tvlUsd', 0), reverse=True)
                        
                        print(f"\n{target.upper()} - Found {len(matching_pools)} pools")
                        print("Top 5 by TVL:")
                        for i, pool in enumerate(matching_pools[:5], 1):
                            symbol = pool.get('symbol', 'Unknown')
                            tvl = pool.get('tvlUsd', 0)
                            apy = pool.get('apy', 0)
                            chain = pool.get('chain', 'Unknown')
                            pool_id = pool.get('pool', 'No ID')
                            
                            print(f"  {i}. {symbol} on {chain}")
                            print(f"     TVL: ${tvl:,.0f}")
                            print(f"     APY: {apy:.2f}%")
                            print(f"     Pool ID: {pool_id}")
                        
                        # Save the second largest if available
                        if len(matching_pools) >= 2:
                            found_pools[target] = {
                                'second_largest': matching_pools[1],
                                'total_pools': len(matching_pools)
                            }
                
                # Save findings
                output_path = Path(__file__).parent.parent / 'data' / 'available_pools.json'
                output_path.parent.mkdir(exist_ok=True)
                
                with open(output_path, 'w') as f:
                    json.dump({
                        'total_protocols': len(protocols),
                        'target_pools': found_pools,
                        'timestamp': time.time()
                    }, f, indent=2)
                
                print(f"\n✓ Saved pool analysis to {output_path}")
                
                return found_pools
                
            else:
                print(f"Unexpected response structure: {list(data.keys())}")
                
    except Exception as e:
        print(f"Error fetching pools: {e}")
        import traceback
        traceback.print_exc()
    
    return {}

if __name__ == "__main__":
    print("Fetching all available pools from DeFillama...")
    pools = fetch_all_pools()