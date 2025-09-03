#!/usr/bin/env python3
"""
Build a comprehensive pool directory with all pools over $1M TVL from DeFillama.
Synchronous version using requests library.
"""

import json
import time
import requests
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import argparse

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

class ComprehensivePoolCollector:
    """Collect comprehensive pool data for all pools over $1M TVL."""
    
    def __init__(self, batch_size=25, rate_limit_delay=0.15):
        self.batch_size = batch_size
        self.rate_limit_delay = rate_limit_delay
        self.session = requests.Session()
        self.directory = {
            "version": "2.0.0",
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": None,
            "total_pools": 0,
            "pools_over_1m_tvl": 0,
            "filters_applied": {
                "min_tvl_usd": 1000000,
                "status": "active"
            },
            "data_sources": {
                "defillama": {
                    "endpoint": "/yields/pools",
                    "api_version": "pro-api",
                    "rate_limit": f"{1/rate_limit_delay:.1f} req/sec"
                }
            },
            "pools": {},
            "metadata": {
                "by_protocol": {},
                "by_chain": {},
                "tvl_ranges": {},
                "apy_ranges": {}
            }
        }
        self.progress_file = Path(__file__).parent.parent / 'data' / 'collection_progress_comprehensive.json'
        self.output_file = Path(__file__).parent.parent / 'data' / 'comprehensive_pool_directory.json'
    
    def load_progress(self):
        """Load previous progress if available."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)
                    print(f"📂 Loaded progress: {progress.get('processed_pools', 0)} pools processed")
                    return progress
            except Exception as e:
                print(f"⚠️  Could not load progress: {e}")
        return {"processed_pools": 0, "last_batch": 0, "completed_pools": []}
    
    def save_progress(self, progress: Dict):
        """Save progress to disk."""
        try:
            self.progress_file.parent.mkdir(exist_ok=True)
            with open(self.progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save progress: {e}")
    
    def fetch_all_pools(self):
        """Fetch all pools from DeFillama API."""
        url = f"{BASE_URL}/yields/pools"
        
        print("🔄 Fetching all pools from DeFillama...")
        try:
            response = self.session.get(url, timeout=60)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    pools = data['data']
                    print(f"✅ Fetched {len(pools):,} total pools")
                    
                    # Filter pools over $1M TVL and sort by TVL
                    filtered_pools = [
                        pool for pool in pools 
                        if pool.get('tvlUsd', 0) >= 1000000
                    ]
                    
                    # Sort by TVL descending
                    filtered_pools.sort(key=lambda x: x.get('tvlUsd', 0), reverse=True)
                    
                    print(f"📊 Found {len(filtered_pools):,} pools over $1M TVL")
                    return filtered_pools
                else:
                    print(f"❌ Unexpected response structure: {list(data.keys())}")
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text}")
                    
        except Exception as e:
            print(f"❌ Error fetching pools: {e}")
        
        return []
    
    def extract_pool_contract_address(self, pool_data: Dict) -> str:
        """Extract the best available contract address."""
        pool_id = pool_data.get('pool', '')
        chain = pool_data.get('chain', '').lower()
        
        # For EVM chains, try to extract 0x addresses
        if chain in ['ethereum', 'base', 'arbitrum', 'optimism', 'polygon', 'bsc', 'avalanche']:
            # Check if pool_id is already a valid address
            if pool_id.startswith('0x') and len(pool_id) == 42:
                return pool_id.lower()
            
            # Check poolMeta for address
            pool_meta = pool_data.get('poolMeta')
            if pool_meta and isinstance(pool_meta, str) and pool_meta.startswith('0x') and len(pool_meta) == 42:
                return pool_meta.lower()
            
            # Look in pool ID components
            if '-' in pool_id:
                parts = pool_id.split('-')
                for part in parts:
                    if part.startswith('0x') and len(part) == 42:
                        return part.lower()
        
        # For non-EVM chains, return pool_id as-is
        return pool_id
    
    def calculate_universal_id(self, pool_data: Dict, contract_address: str) -> str:
        """Calculate universal pool ID."""
        chain = pool_data.get('chain', 'unknown').lower()
        return f"{chain}:{contract_address}"
    
    def categorize_pool_type(self, pool_data: Dict) -> str:
        """Categorize pool type based on available data."""
        project = pool_data.get('project', '').lower()
        pool_meta = pool_data.get('poolMeta', '')
        
        pool_meta_lower = pool_meta.lower() if pool_meta else ''
        if 'uniswap-v3' in project or 'aerodrome-slipstream' in project or 'concentrated' in pool_meta_lower:
            return 'concentrated_liquidity'
        elif 'curve' in project or 'stable' in pool_meta_lower:
            return 'stable_swap'
        elif 'balancer' in project:
            return 'weighted_pool'
        elif any(x in project for x in ['aave', 'compound', 'morpho']):
            return 'lending_pool'
        elif 'v2' in project:
            return 'constant_product'
        else:
            return 'other'
    
    def assess_clm_suitability(self, pool_data: Dict) -> Dict:
        """Assess suitability for CLM strategies."""
        tvl = pool_data.get('tvlUsd', 0)
        apy = pool_data.get('apy', 0)
        pool_type = self.categorize_pool_type(pool_data)
        
        # Base score calculation
        score = 0
        factors = []
        
        # TVL factor (higher TVL = better for CLM)
        if tvl >= 100000000:  # $100M+
            score += 40
            factors.append("High TVL (>$100M)")
        elif tvl >= 10000000:  # $10M+
            score += 30
            factors.append("Medium TVL (>$10M)")
        elif tvl >= 1000000:  # $1M+
            score += 20
            factors.append("Sufficient TVL (>$1M)")
        
        # APY factor
        if apy >= 50:
            score += 30
            factors.append("High APY (>50%)")
        elif apy >= 20:
            score += 20
            factors.append("Good APY (>20%)")
        elif apy >= 5:
            score += 10
            factors.append("Moderate APY (>5%)")
        
        # Pool type factor
        if pool_type == 'concentrated_liquidity':
            score += 20
            factors.append("Concentrated liquidity native")
        elif pool_type == 'constant_product':
            score += 10
            factors.append("Compatible with CLM strategies")
        
        # Protocol reputation (based on common knowledge)
        project = pool_data.get('project', '').lower()
        if any(protocol in project for protocol in ['uniswap', 'curve', 'balancer', 'aerodrome']):
            score += 10
            factors.append("Established protocol")
        
        # Determine suitability level
        if score >= 80:
            suitability = "excellent"
        elif score >= 60:
            suitability = "good"
        elif score >= 40:
            suitability = "moderate"
        else:
            suitability = "low"
        
        return {
            "score": score,
            "level": suitability,
            "factors": factors,
            "recommended_capital": self.suggest_min_capital(tvl, apy),
            "risk_level": self.assess_risk_level(pool_data)
        }
    
    def suggest_min_capital(self, tvl: float, apy: float) -> str:
        """Suggest minimum capital based on pool characteristics."""
        if tvl >= 100000000 and apy >= 20:
            return "$10,000+"
        elif tvl >= 10000000 and apy >= 10:
            return "$5,000+"
        elif tvl >= 1000000:
            return "$1,000+"
        else:
            return "$500+"
    
    def assess_risk_level(self, pool_data: Dict) -> str:
        """Assess risk level based on token composition."""
        tokens = pool_data.get('underlyingTokens', [])
        if not tokens:
            return "unknown"
        
        # Simple heuristic based on common stablecoin addresses/symbols
        stablecoin_indicators = [
            'usdc', 'usdt', 'dai', 'busd', 'frax', 'lusd', 'susd', 
            'usdbc', 'usds', 'gusd', 'tusd', 'usdp', 'ust'
        ]
        
        # Get token symbols from pool name as fallback
        pool_name = pool_data.get('symbol', '').lower()
        
        # Count potential stablecoins
        stable_count = 0
        for token in tokens:
            token_lower = str(token).lower()
            if any(stable in token_lower for stable in stablecoin_indicators):
                stable_count += 1
        
        # Also check pool name for stablecoin pairs
        if any(stable in pool_name for stable in stablecoin_indicators):
            stable_count = max(stable_count, 1)
            if pool_name.count('usd') >= 2 or any(stable in pool_name for stable in ['usdc-usdt', 'usdt-usdc', 'dai-usdc']):
                stable_count = 2
        
        if len(tokens) >= 2 and stable_count >= 2:
            return "low"  # Stable-stable pairs
        elif stable_count >= 1:
            return "medium"  # Stable-volatile pairs
        else:
            return "high"  # Volatile-volatile pairs
    
    def process_pool_batch(self, pools_batch: List[Dict], batch_num: int):
        """Process a batch of pools."""
        print(f"📦 Processing batch {batch_num} ({len(pools_batch)} pools)...")
        
        processed_count = 0
        for i, pool_data in enumerate(pools_batch, 1):
            try:
                pool_id = pool_data.get('pool')
                pool_name = pool_data.get('symbol', 'Unknown')
                
                # Extract contract address
                contract_address = self.extract_pool_contract_address(pool_data)
                universal_id = self.calculate_universal_id(pool_data, contract_address)
                
                # Build comprehensive pool entry
                pool_entry = {
                    "universal_id": universal_id,
                    "defillama_pool_id": pool_id,
                    "name": pool_name,
                    "protocol": pool_data.get('project'),
                    "chain": pool_data.get('chain'),
                    "contract_address": contract_address,
                    "pool_type": self.categorize_pool_type(pool_data),
                    
                    # Financial metrics
                    "metrics": {
                        "tvl_usd": pool_data.get('tvlUsd', 0),
                        "apy_total": pool_data.get('apy', 0),
                        "apy_base": pool_data.get('apyBase', 0),
                        "apy_reward": pool_data.get('apyReward', 0),
                        "apy_mean_30d": pool_data.get('apyMean30d'),
                        "volume_usd_1d": pool_data.get('volumeUsd1d', 0),
                        "volume_usd_7d": pool_data.get('volumeUsd7d', 0),
                        "il_risk": pool_data.get('ilRisk'),
                        "exposure": pool_data.get('exposure'),
                        "count": pool_data.get('count', 1)
                    },
                    
                    # Token information
                    "tokens": {
                        "underlying_tokens": pool_data.get('underlyingTokens', []),
                        "reward_tokens": pool_data.get('rewardTokens', []),
                        "token_symbols": pool_data.get('symbol', '').replace('-', '/').split('/') if pool_data.get('symbol') else []
                    },
                    
                    # Pool configuration
                    "config": {
                        "pool_meta": pool_data.get('poolMeta'),
                        "mu": pool_data.get('mu'),
                        "sigma": pool_data.get('sigma'),
                        "outlier": pool_data.get('outlier', False),
                        "stable": pool_data.get('stablecoin', False)
                    },
                    
                    # CLM Strategy Assessment
                    "clm_analysis": self.assess_clm_suitability(pool_data),
                    
                    # Data sources and integration
                    "integration": {
                        "defillama": {
                            "pool_id": pool_id,
                            "chart_endpoint": f"/yields/chart/{pool_id}",
                            "enabled": True
                        },
                        "blockchain": {
                            "chain": pool_data.get('chain'),
                            "contract_address": contract_address,
                            "universal_id": universal_id
                        }
                    },
                    
                    # Metadata
                    "metadata": {
                        "added_at": datetime.utcnow().isoformat(),
                        "data_quality": "high" if pool_data.get('tvlUsd', 0) > 10000000 else "medium",
                        "last_updated": datetime.utcnow().isoformat(),
                        "rank_by_tvl": None  # Will be set later
                    }
                }
                
                # Add to directory
                self.directory["pools"][universal_id] = pool_entry
                processed_count += 1
                
                # Rate limiting
                if i % 10 == 0:
                    print(f"  ✓ Processed {i}/{len(pools_batch)} pools in batch {batch_num}")
                    time.sleep(self.rate_limit_delay)
                
            except Exception as e:
                print(f"  ❌ Error processing pool {pool_name}: {e}")
                continue
        
        print(f"✅ Completed batch {batch_num}: {processed_count}/{len(pools_batch)} pools processed")
        return processed_count
    
    def calculate_metadata_stats(self):
        """Calculate metadata statistics."""
        print("📊 Calculating metadata statistics...")
        
        # Count by protocol
        protocol_counts = {}
        protocol_tvl = {}
        
        # Count by chain
        chain_counts = {}
        chain_tvl = {}
        
        # TVL and APY ranges
        tvl_ranges = {"1M-10M": 0, "10M-100M": 0, "100M-1B": 0, "1B+": 0}
        apy_ranges = {"0-5%": 0, "5-20%": 0, "20-50%": 0, "50%+": 0}
        
        # CLM suitability
        clm_suitability = {"excellent": 0, "good": 0, "moderate": 0, "low": 0}
        
        total_tvl = 0
        
        for pool_id, pool in self.directory["pools"].items():
            protocol = pool["protocol"]
            chain = pool["chain"]
            tvl = pool["metrics"]["tvl_usd"]
            apy = pool["metrics"]["apy_total"]
            clm_level = pool["clm_analysis"]["level"]
            
            # Protocol stats
            protocol_counts[protocol] = protocol_counts.get(protocol, 0) + 1
            protocol_tvl[protocol] = protocol_tvl.get(protocol, 0) + tvl
            
            # Chain stats
            chain_counts[chain] = chain_counts.get(chain, 0) + 1
            chain_tvl[chain] = chain_tvl.get(chain, 0) + tvl
            
            # TVL ranges
            if tvl >= 1000000000:
                tvl_ranges["1B+"] += 1
            elif tvl >= 100000000:
                tvl_ranges["100M-1B"] += 1
            elif tvl >= 10000000:
                tvl_ranges["10M-100M"] += 1
            else:
                tvl_ranges["1M-10M"] += 1
            
            # APY ranges
            if apy >= 50:
                apy_ranges["50%+"] += 1
            elif apy >= 20:
                apy_ranges["20-50%"] += 1
            elif apy >= 5:
                apy_ranges["5-20%"] += 1
            else:
                apy_ranges["0-5%"] += 1
            
            # CLM suitability
            clm_suitability[clm_level] += 1
            
            total_tvl += tvl
        
        # Update directory metadata
        self.directory["metadata"] = {
            "by_protocol": {
                "counts": protocol_counts,
                "tvl": protocol_tvl
            },
            "by_chain": {
                "counts": chain_counts,
                "tvl": chain_tvl
            },
            "tvl_ranges": tvl_ranges,
            "apy_ranges": apy_ranges,
            "clm_suitability": clm_suitability,
            "total_tvl": total_tvl
        }
        
        self.directory["total_pools"] = len(self.directory["pools"])
        self.directory["pools_over_1m_tvl"] = len(self.directory["pools"])
    
    def add_tvl_rankings(self):
        """Add TVL rankings to each pool."""
        print("🏆 Adding TVL rankings...")
        
        # Sort pools by TVL
        sorted_pools = sorted(
            self.directory["pools"].items(),
            key=lambda x: x[1]["metrics"]["tvl_usd"],
            reverse=True
        )
        
        # Add rankings
        for rank, (pool_id, pool_data) in enumerate(sorted_pools, 1):
            self.directory["pools"][pool_id]["metadata"]["rank_by_tvl"] = rank
    
    def collect_all_pools(self, resume=True):
        """Main function to collect all pools over $1M TVL."""
        print("=" * 80)
        print("🏗️  BUILDING COMPREHENSIVE POOL DIRECTORY")
        print("=" * 80)
        print(f"📋 Target: All pools over $1M TVL")
        print(f"⚙️  Batch size: {self.batch_size}")
        print(f"🕐 Rate limit: {1/self.rate_limit_delay:.1f} req/sec")
        
        # Load previous progress
        progress = self.load_progress() if resume else {"processed_pools": 0, "last_batch": 0}
        
        # Fetch all pools
        all_pools = self.fetch_all_pools()
        if not all_pools:
            print("❌ Failed to fetch pools")
            return
        
        print(f"🎯 Target pools to process: {len(all_pools):,}")
        
        # Skip already processed pools if resuming
        if resume and progress["processed_pools"] > 0:
            all_pools = all_pools[progress["processed_pools"]:]
            print(f"📂 Resuming from pool {progress['processed_pools']:,}")
        
        # Process in batches
        total_processed = progress["processed_pools"]
        batch_num = progress["last_batch"]
        
        try:
            for i in range(0, len(all_pools), self.batch_size):
                batch_num += 1
                batch = all_pools[i:i + self.batch_size]
                
                processed_in_batch = self.process_pool_batch(batch, batch_num)
                total_processed += processed_in_batch
                
                # Save progress
                progress.update({
                    "processed_pools": total_processed,
                    "last_batch": batch_num,
                    "last_updated": datetime.utcnow().isoformat()
                })
                self.save_progress(progress)
                
                # Save intermediate results every 5 batches
                if batch_num % 5 == 0:
                    self.directory["last_updated"] = datetime.utcnow().isoformat()
                    self.calculate_metadata_stats()
                    
                    self.output_file.parent.mkdir(exist_ok=True)
                    with open(self.output_file, 'w') as f:
                        json.dump(self.directory, f, indent=2)
                    
                    print(f"💾 Intermediate save: {total_processed:,} pools processed")
                
                # Respect rate limits
                time.sleep(self.rate_limit_delay)
            
            print(f"\n✅ Collection complete: {total_processed:,} pools processed")
            
            # Final processing
            self.directory["last_updated"] = datetime.utcnow().isoformat()
            self.calculate_metadata_stats()
            self.add_tvl_rankings()
            
            # Save final result
            self.output_file.parent.mkdir(exist_ok=True)
            with open(self.output_file, 'w') as f:
                json.dump(self.directory, f, indent=2)
            
            print(f"💾 Final directory saved: {self.output_file}")
            
            # Clean up progress file
            if self.progress_file.exists():
                self.progress_file.unlink()
                print("🗑️  Cleaned up progress file")
            
            # Print summary
            self.print_summary()
            
        except KeyboardInterrupt:
            print(f"\n⏸️  Collection interrupted. Progress saved. Resume with same command.")
            # Save current state
            self.directory["last_updated"] = datetime.utcnow().isoformat()
            self.calculate_metadata_stats()
            
            self.output_file.parent.mkdir(exist_ok=True)
            with open(self.output_file, 'w') as f:
                json.dump(self.directory, f, indent=2)
            print(f"💾 Partial results saved: {self.output_file}")
    
    def print_summary(self):
        """Print collection summary."""
        print("\n" + "=" * 80)
        print("📊 COLLECTION SUMMARY")
        print("=" * 80)
        
        metadata = self.directory["metadata"]
        
        print(f"Total Pools: {self.directory['total_pools']:,}")
        print(f"Total TVL: ${metadata['total_tvl']:,.0f}")
        
        print(f"\n🏆 Top Protocols:")
        sorted_protocols = sorted(
            metadata["by_protocol"]["tvl"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for protocol, tvl in sorted_protocols[:10]:
            count = metadata["by_protocol"]["counts"][protocol]
            print(f"  {protocol:25} {count:4} pools (${tvl:,.0f})")
        
        print(f"\n⛓️  Top Chains:")
        sorted_chains = sorted(
            metadata["by_chain"]["tvl"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for chain, tvl in sorted_chains[:10]:
            count = metadata["by_chain"]["counts"][chain]
            print(f"  {chain:15} {count:4} pools (${tvl:,.0f})")
        
        print(f"\n🎯 CLM Suitability:")
        for level, count in metadata["clm_suitability"].items():
            percentage = count / self.directory["total_pools"] * 100 if self.directory["total_pools"] > 0 else 0
            print(f"  {level:10} {count:4} pools ({percentage:5.1f}%)")

def main():
    parser = argparse.ArgumentParser(description='Build comprehensive pool directory')
    parser.add_argument('--batch-size', type=int, default=25, help='Batch size for processing')
    parser.add_argument('--rate-limit', type=float, default=0.15, help='Delay between requests in seconds')
    parser.add_argument('--no-resume', action='store_true', help='Start fresh without resuming')
    
    args = parser.parse_args()
    
    collector = ComprehensivePoolCollector(
        batch_size=args.batch_size,
        rate_limit_delay=args.rate_limit
    )
    
    collector.collect_all_pools(resume=not args.no_resume)

if __name__ == "__main__":
    main()