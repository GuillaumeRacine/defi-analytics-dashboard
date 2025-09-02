"""
Multi-source data integration module.
Handles mapping between different data source identifiers and our contract-based UUIDs.
"""

from typing import Dict, List, Optional, Any, Protocol
from dataclasses import dataclass
from enum import Enum
import json
from abc import ABC, abstractmethod


class DataSource(Enum):
    """Supported data sources"""
    DEFILLAMA = "defillama"
    COINGECKO = "coingecko"
    GRAPH = "graph"
    ETHERSCAN = "etherscan"
    DUNE = "dune"
    CHAINLINK = "chainlink"
    ALCHEMY = "alchemy"
    INFURA = "infura"


@dataclass
class TokenIdentifier:
    """Universal token identifier across all data sources"""
    chain: str
    contract_address: str
    
    @property
    def uuid(self) -> str:
        """Returns universal identifier: chain:address"""
        return f"{self.chain}:{self.contract_address.lower()}"
    
    @property
    def defillama_id(self) -> str:
        """Format for DeFillama API"""
        return self.uuid  # DeFillama uses same format
    
    @property
    def graph_id(self) -> str:
        """Format for The Graph Protocol"""
        return self.contract_address.lower()
    
    def get_etherscan_url(self) -> str:
        """Get Etherscan URL for this token"""
        chain_explorers = {
            "ethereum": "etherscan.io",
            "polygon": "polygonscan.com",
            "arbitrum": "arbiscan.io",
            "optimism": "optimistic.etherscan.io",
            "bsc": "bscscan.com",
        }
        explorer = chain_explorers.get(self.chain, "etherscan.io")
        return f"https://{explorer}/token/{self.contract_address}"


@dataclass 
class PoolIdentifier:
    """Universal LP pool identifier"""
    chain: str
    pool_address: str
    protocol: str  # uniswap-v3, curve, balancer
    token_addresses: List[str]  # Component tokens
    
    @property
    def uuid(self) -> str:
        """Returns universal identifier: chain:address"""
        return f"{self.chain}:{self.pool_address.lower()}"
    
    @property
    def defillama_pool_id(self) -> Optional[str]:
        """DeFillama's internal pool UUID (needs lookup)"""
        # This would be populated from API response
        return None
    
    def get_token_pair_id(self) -> str:
        """Returns a token pair identifier for 2-token pools"""
        if len(self.token_addresses) == 2:
            tokens = sorted(self.token_addresses)
            return f"{tokens[0]}-{tokens[1]}"
        return "-".join(sorted(self.token_addresses))


class DataSourceMapper:
    """Maps between different data source identifier formats"""
    
    def __init__(self):
        self.mappings: Dict[str, Dict[str, str]] = {}
        self.reverse_mappings: Dict[str, Dict[str, str]] = {}
        self._load_known_mappings()
    
    def _load_known_mappings(self):
        """Load known token mappings"""
        # Common token mappings
        known_tokens = {
            "ethereum:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {
                DataSource.DEFILLAMA: "ethereum:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                DataSource.COINGECKO: "usd-coin",
                DataSource.GRAPH: "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            },
            "ethereum:0xdac17f958d2ee523a2206206994597c13d831ec7": {
                DataSource.DEFILLAMA: "ethereum:0xdac17f958d2ee523a2206206994597c13d831ec7",
                DataSource.COINGECKO: "tether",
                DataSource.GRAPH: "0xdac17f958d2ee523a2206206994597c13d831ec7",
            },
            "ethereum:0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": {
                DataSource.DEFILLAMA: "ethereum:0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                DataSource.COINGECKO: "weth",
                DataSource.GRAPH: "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            },
        }
        
        for uuid, source_ids in known_tokens.items():
            self.mappings[uuid] = source_ids
            for source, source_id in source_ids.items():
                if source not in self.reverse_mappings:
                    self.reverse_mappings[source] = {}
                self.reverse_mappings[source][source_id] = uuid
    
    def add_mapping(self, uuid: str, source: DataSource, source_id: str):
        """Add a new mapping"""
        if uuid not in self.mappings:
            self.mappings[uuid] = {}
        self.mappings[uuid][source] = source_id
        
        if source not in self.reverse_mappings:
            self.reverse_mappings[source] = {}
        self.reverse_mappings[source][source_id] = uuid
    
    def get_source_id(self, uuid: str, source: DataSource) -> Optional[str]:
        """Get the source-specific ID for a UUID"""
        return self.mappings.get(uuid, {}).get(source)
    
    def get_uuid(self, source: DataSource, source_id: str) -> Optional[str]:
        """Get the UUID for a source-specific ID"""
        return self.reverse_mappings.get(source, {}).get(source_id)
    
    def save_mappings(self, filepath: str):
        """Save mappings to JSON file"""
        data = {
            "mappings": {
                uuid: {source.value: sid for source, sid in source_map.items()}
                for uuid, source_map in self.mappings.items()
            }
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_mappings(self, filepath: str):
        """Load mappings from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.mappings = {}
        self.reverse_mappings = {}
        
        for uuid, source_map in data["mappings"].items():
            self.mappings[uuid] = {
                DataSource(source_name): source_id 
                for source_name, source_id in source_map.items()
            }
            for source_name, source_id in source_map.items():
                source = DataSource(source_name)
                if source not in self.reverse_mappings:
                    self.reverse_mappings[source] = {}
                self.reverse_mappings[source][source_id] = uuid


class DataAggregator:
    """Aggregates data from multiple sources using contract addresses as keys"""
    
    def __init__(self, mapper: DataSourceMapper):
        self.mapper = mapper
        self.data_cache: Dict[str, Dict[str, Any]] = {}
    
    def add_price_data(self, uuid: str, source: DataSource, timestamp: int, price: float, **kwargs):
        """Add price data from a source"""
        if uuid not in self.data_cache:
            self.data_cache[uuid] = {"prices": {}}
        
        if timestamp not in self.data_cache[uuid]["prices"]:
            self.data_cache[uuid]["prices"][timestamp] = {}
        
        self.data_cache[uuid]["prices"][timestamp][source.value] = {
            "price": price,
            "source": source.value,
            **kwargs
        }
    
    def get_consensus_price(self, uuid: str, timestamp: int) -> Optional[Dict[str, Any]]:
        """Get consensus price from multiple sources"""
        if uuid not in self.data_cache or timestamp not in self.data_cache[uuid].get("prices", {}):
            return None
        
        prices_data = self.data_cache[uuid]["prices"][timestamp]
        prices = [data["price"] for data in prices_data.values()]
        
        if not prices:
            return None
        
        # Calculate consensus metrics
        avg_price = sum(prices) / len(prices)
        median_price = sorted(prices)[len(prices) // 2]
        
        # Calculate confidence based on agreement
        deviations = [abs(p - median_price) / median_price for p in prices]
        max_deviation = max(deviations) if deviations else 0
        confidence = max(0, 1 - max_deviation)
        
        return {
            "uuid": uuid,
            "timestamp": timestamp,
            "price": median_price,  # Use median as consensus
            "avg_price": avg_price,
            "confidence": confidence,
            "sources": list(prices_data.keys()),
            "source_prices": {source: data["price"] for source, data in prices_data.items()}
        }
    
    def validate_cross_source(self, uuid: str, timestamp: int, threshold: float = 0.05) -> bool:
        """Validate price across sources with deviation threshold"""
        consensus = self.get_consensus_price(uuid, timestamp)
        if not consensus or len(consensus["sources"]) < 2:
            return False
        
        # Check if all prices are within threshold of median
        median = consensus["price"]
        for price in consensus["source_prices"].values():
            if abs(price - median) / median > threshold:
                return False
        
        return True


class IDataFetcher(Protocol):
    """Protocol for data fetchers from different sources"""
    
    async def fetch_token_price(self, uuid: str, timestamp: Optional[int] = None) -> Dict[str, Any]:
        """Fetch token price"""
        ...
    
    async def fetch_pool_data(self, uuid: str, timestamp: Optional[int] = None) -> Dict[str, Any]:
        """Fetch LP pool data"""
        ...


class MultiSourceClient:
    """Client that fetches and reconciles data from multiple sources"""
    
    def __init__(self):
        self.mapper = DataSourceMapper()
        self.aggregator = DataAggregator(self.mapper)
        self.fetchers: Dict[DataSource, IDataFetcher] = {}
    
    def register_fetcher(self, source: DataSource, fetcher: IDataFetcher):
        """Register a data fetcher for a source"""
        self.fetchers[source] = fetcher
    
    async def fetch_token_data(self, uuid: str, timestamp: Optional[int] = None, 
                               sources: Optional[List[DataSource]] = None) -> Dict[str, Any]:
        """Fetch token data from multiple sources and reconcile"""
        if sources is None:
            sources = list(self.fetchers.keys())
        
        results = {}
        for source in sources:
            if source not in self.fetchers:
                continue
            
            try:
                data = await self.fetchers[source].fetch_token_price(uuid, timestamp)
                results[source.value] = data
                
                # Add to aggregator
                if "price" in data:
                    self.aggregator.add_price_data(
                        uuid, source, timestamp or data.get("timestamp"), 
                        data["price"], **data
                    )
            except Exception as e:
                print(f"Error fetching from {source.value}: {e}")
                continue
        
        # Get consensus data
        if timestamp:
            consensus = self.aggregator.get_consensus_price(uuid, timestamp)
            if consensus:
                results["consensus"] = consensus
        
        return results
    
    def get_unified_token_data(self, uuid: str) -> Dict[str, Any]:
        """Get all available data for a token across sources"""
        return {
            "uuid": uuid,
            "mappings": self.mapper.mappings.get(uuid, {}),
            "cached_data": self.data_cache.get(uuid, {})
        }