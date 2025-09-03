#!/usr/bin/env python3
"""
Analyze total unique pools over $1M TVL in DeFillama API.
"""

import json
import requests
import os
from pathlib import Path
from collections import Counter, defaultdict

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

def analyze_all_pools():
    """Analyze all pools in DeFillama to find unique pools over $1M TVL."""
    
    print("=" * 60)
    print("ANALYZING ALL POOLS IN DEFILLAMA API")
    print("=" * 60)
    
    url = f"{BASE_URL}/yields/pools"
    
    try:
        print("Fetching all pools from DeFillama...")
        response = requests.get(url, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                pools = data['data']
                total_pools = len(pools)
                
                print(f"Total pools in API: {total_pools:,}")
                
                # Analyze pools
                over_1m_pools = []
                protocol_counts = Counter()
                chain_counts = Counter()
                tvl_ranges = defaultdict(int)
                
                for pool in pools:
                    tvl = pool.get('tvlUsd', 0)
                    protocol = pool.get('project', 'unknown')
                    chain = pool.get('chain', 'unknown')
                    
                    # Count by protocol and chain
                    protocol_counts[protocol] += 1
                    chain_counts[chain] += 1
                    
                    # TVL ranges
                    if tvl >= 1000000000:  # $1B+
                        tvl_ranges['$1B+'] += 1
                    elif tvl >= 100000000:  # $100M+
                        tvl_ranges['$100M-$1B'] += 1
                    elif tvl >= 10000000:  # $10M+
                        tvl_ranges['$10M-$100M'] += 1
                    elif tvl >= 1000000:  # $1M+
                        tvl_ranges['$1M-$10M'] += 1
                    elif tvl >= 100000:  # $100K+
                        tvl_ranges['$100K-$1M'] += 1
                    else:
                        tvl_ranges['<$100K'] += 1
                    
                    # Pools over $1M
                    if tvl >= 1000000:
                        over_1m_pools.append({
                            'pool_id': pool.get('pool'),
                            'name': pool.get('symbol', 'Unknown'),
                            'protocol': protocol,
                            'chain': chain,
                            'tvl': tvl,
                            'apy': pool.get('apy', 0)
                        })
                
                # Sort pools by TVL
                over_1m_pools.sort(key=lambda x: x['tvl'], reverse=True)
                
                print(f"\n📊 POOLS OVER $1M TVL: {len(over_1m_pools):,} pools")
                print(f"Percentage of total: {len(over_1m_pools)/total_pools*100:.1f}%")
                
                print("\n💰 TVL DISTRIBUTION:")
                for range_name in ['$1B+', '$100M-$1B', '$10M-$100M', '$1M-$10M', '$100K-$1M', '<$100K']:
                    count = tvl_ranges[range_name]
                    percentage = count/total_pools*100
                    print(f"  {range_name:12} {count:6,} pools ({percentage:5.1f}%)")
                
                print(f"\n🏆 TOP 20 POOLS BY TVL:")
                for i, pool in enumerate(over_1m_pools[:20], 1):
                    tvl_formatted = f"${pool['tvl']:,.0f}"
                    print(f"  {i:2d}. {pool['name']:<20} {tvl_formatted:>15} ({pool['protocol']} on {pool['chain']})")
                
                print(f"\n🔗 TOP PROTOCOLS (with pools >$1M TVL):")
                protocol_over_1m = Counter()
                for pool in over_1m_pools:
                    protocol_over_1m[pool['protocol']] += 1
                
                for protocol, count in protocol_over_1m.most_common(15):
                    total_protocol_pools = protocol_counts[protocol]
                    percentage = count/total_protocol_pools*100 if total_protocol_pools > 0 else 0
                    print(f"  {protocol:25} {count:4} of {total_protocol_pools:4} pools ({percentage:4.1f}%)")
                
                print(f"\n⛓️  TOP CHAINS (with pools >$1M TVL):")
                chain_over_1m = Counter()
                total_tvl_by_chain = defaultdict(float)
                
                for pool in over_1m_pools:
                    chain_over_1m[pool['chain']] += 1
                    total_tvl_by_chain[pool['chain']] += pool['tvl']
                
                for chain, count in chain_over_1m.most_common(10):
                    total_tvl = total_tvl_by_chain[chain]
                    avg_tvl = total_tvl / count if count > 0 else 0
                    print(f"  {chain:15} {count:4} pools, ${total_tvl:13,.0f} TVL (avg ${avg_tvl:8,.0f})")
                
                # Calculate some interesting stats
                print(f"\n📈 INTERESTING STATS:")
                
                # APY analysis for >$1M pools
                high_apy_pools = [p for p in over_1m_pools if p['apy'] > 50]
                medium_apy_pools = [p for p in over_1m_pools if 10 <= p['apy'] <= 50]
                
                print(f"  Pools >$1M with >50% APY:  {len(high_apy_pools):4} pools")
                print(f"  Pools >$1M with 10-50% APY: {len(medium_apy_pools):4} pools")
                
                # Mega pools
                mega_pools = [p for p in over_1m_pools if p['tvl'] >= 100000000]  # $100M+
                print(f"  Mega pools (>$100M TVL):   {len(mega_pools):4} pools")
                
                # Total TVL in >$1M pools
                total_tvl_over_1m = sum(p['tvl'] for p in over_1m_pools)
                print(f"  Total TVL in >$1M pools:   ${total_tvl_over_1m:,.0f}")
                
                # Save detailed analysis
                output_data = {
                    'analysis_date': '2025-09-03',
                    'total_pools': total_pools,
                    'pools_over_1m_tvl': len(over_1m_pools),
                    'percentage_over_1m': len(over_1m_pools)/total_pools*100,
                    'tvl_distribution': dict(tvl_ranges),
                    'top_protocols': dict(protocol_over_1m.most_common(20)),
                    'top_chains': dict(chain_over_1m.most_common(15)),
                    'top_20_pools': over_1m_pools[:20],
                    'total_tvl_over_1m': total_tvl_over_1m,
                    'mega_pools_count': len(mega_pools),
                    'high_apy_pools_count': len(high_apy_pools)
                }
                
                output_path = Path(__file__).parent.parent / 'data' / 'defillama_pool_analysis.json'
                with open(output_path, 'w') as f:
                    json.dump(output_data, f, indent=2)
                
                print(f"\n✓ Detailed analysis saved to {output_path}")
                
                return len(over_1m_pools)
                
            else:
                print(f"Unexpected response structure: {list(data.keys())}")
                
        else:
            print(f"API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    return 0

if __name__ == "__main__":
    unique_pools_over_1m = analyze_all_pools()
    print(f"\n🎯 FINAL ANSWER: {unique_pools_over_1m:,} unique pools over $1M TVL")