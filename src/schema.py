"""
Database schema definitions using contract addresses as primary identifiers.
This enables seamless integration with other data sources (Graph, Etherscan, etc.)
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class Chain(Enum):
    """Blockchain networks with their chain IDs"""
    ETHEREUM = (1, "ethereum")
    POLYGON = (137, "polygon") 
    ARBITRUM = (42161, "arbitrum")
    OPTIMISM = (10, "optimism")
    BSC = (56, "bsc")
    AVALANCHE = (43114, "avalanche")
    BASE = (8453, "base")
    
    def __init__(self, chain_id: int, name: str):
        self.chain_id = chain_id
        self.chain_name = name


@dataclass
class ContractIdentifier:
    """
    Universal identifier for any on-chain entity.
    Format: {chain}:{contract_address}
    Example: ethereum:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48 (USDC)
    """
    chain: Chain
    address: str  # Lowercase, checksummed address
    
    @property
    def uuid(self) -> str:
        """Returns the universal identifier string"""
        return f"{self.chain.chain_name}:{self.address.lower()}"
    
    @classmethod
    def from_string(cls, identifier: str) -> 'ContractIdentifier':
        """Parse a string identifier like 'ethereum:0x...'"""
        chain_name, address = identifier.split(':')
        chain = next(c for c in Chain if c.chain_name == chain_name)
        return cls(chain=chain, address=address.lower())


# DuckDB Schema Definitions

TOKEN_SCHEMA = """
CREATE TABLE IF NOT EXISTS tokens (
    -- Primary identifier
    contract_id VARCHAR PRIMARY KEY,  -- Format: chain:address
    chain VARCHAR NOT NULL,
    contract_address VARCHAR NOT NULL,
    
    -- Token metadata
    symbol VARCHAR,
    name VARCHAR,
    decimals INTEGER,
    total_supply DECIMAL(38, 0),
    
    -- DeFillama specific
    defillama_id VARCHAR,  -- Their internal ID if different
    coingecko_id VARCHAR,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tokens_chain_address ON tokens (chain, contract_address);
CREATE INDEX IF NOT EXISTS idx_tokens_symbol ON tokens (symbol);
"""

PRICE_HISTORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS price_history (
    -- Composite primary key for efficient queries
    contract_id VARCHAR NOT NULL,  -- Format: chain:address
    timestamp BIGINT NOT NULL,      -- Unix timestamp
    
    -- Price data
    price DECIMAL(38, 18) NOT NULL,
    volume_24h DECIMAL(38, 2),
    market_cap DECIMAL(38, 2),
    
    -- Data quality
    confidence DECIMAL(3, 2),  -- 0.00 to 1.00
    source VARCHAR,  -- 'defillama', 'coingecko', 'chainlink', etc.
    
    -- Additional metrics
    price_change_24h DECIMAL(10, 4),
    high_24h DECIMAL(38, 18),
    low_24h DECIMAL(38, 18),
    
    PRIMARY KEY (contract_id, timestamp, source)
);

CREATE INDEX IF NOT EXISTS idx_price_contract_time ON price_history (contract_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_price_timestamp ON price_history (timestamp);
"""

LP_POOL_SCHEMA = """
CREATE TABLE IF NOT EXISTS lp_pools (
    -- Primary identifier
    pool_contract_id VARCHAR PRIMARY KEY,  -- Format: chain:pool_address
    chain VARCHAR NOT NULL,
    pool_address VARCHAR NOT NULL,
    
    -- Pool configuration
    protocol VARCHAR NOT NULL,  -- 'uniswap-v3', 'curve', 'balancer'
    pool_type VARCHAR,  -- 'constant-product', 'stable', 'concentrated'
    
    -- Token pair/set (stored as JSON array of contract_ids)
    token_addresses JSON NOT NULL,  -- ["ethereum:0x...", "ethereum:0x..."]
    token_symbols JSON,  -- ["USDC", "ETH"]
    token_weights JSON,  -- [50, 50] for Balancer, null for others
    
    -- Uniswap V3 specific
    fee_tier INTEGER,  -- 500, 3000, 10000 (0.05%, 0.3%, 1%)
    tick_spacing INTEGER,
    
    -- DeFillama specific
    defillama_pool_id VARCHAR,  -- Their UUID
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pools_protocol ON lp_pools (protocol);
CREATE INDEX IF NOT EXISTS idx_pools_chain ON lp_pools (chain);
"""

LP_POOL_HISTORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS lp_pool_history (
    -- Composite key
    pool_contract_id VARCHAR NOT NULL,
    timestamp BIGINT NOT NULL,
    
    -- Liquidity metrics
    tvl_usd DECIMAL(38, 2) NOT NULL,
    volume_24h_usd DECIMAL(38, 2),
    fees_24h_usd DECIMAL(38, 2),
    
    -- Token reserves (stored as JSON for flexibility)
    reserves JSON,  -- {"ethereum:0x...": "1000000", ...}
    reserves_usd JSON,  -- {"ethereum:0x...": 1000000.00, ...}
    
    -- Yield metrics
    apy_base DECIMAL(10, 4),  -- Base APY from fees
    apy_reward DECIMAL(10, 4),  -- Additional rewards APY
    apy_total DECIMAL(10, 4),  -- Total APY
    
    -- Impermanent loss
    il_7d DECIMAL(10, 4),  -- 7-day IL percentage
    il_30d DECIMAL(10, 4),  -- 30-day IL percentage
    
    -- Data source
    source VARCHAR DEFAULT 'defillama',
    
    PRIMARY KEY (pool_contract_id, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_pool_history_time ON lp_pool_history (timestamp);
"""

LP_POSITION_SCHEMA = """
CREATE TABLE IF NOT EXISTS lp_positions (
    -- Position identifier
    position_id VARCHAR PRIMARY KEY,  -- Can be NFT ID for Uni V3
    pool_contract_id VARCHAR NOT NULL,
    wallet_address VARCHAR NOT NULL,  -- Owner wallet
    
    -- Position details
    liquidity_amount DECIMAL(38, 18),  -- LP token amount or liquidity
    
    -- Uniswap V3 concentrated liquidity
    tick_lower INTEGER,
    tick_upper INTEGER,
    
    -- Entry tracking
    entry_timestamp BIGINT,
    entry_price_token0 DECIMAL(38, 18),
    entry_price_token1 DECIMAL(38, 18),
    
    -- Current state
    is_active BOOLEAN DEFAULT TRUE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_positions_wallet ON lp_positions (wallet_address);
CREATE INDEX IF NOT EXISTS idx_positions_pool_wallet ON lp_positions (pool_contract_id, wallet_address);
"""

WALLET_SCHEMA = """
CREATE TABLE IF NOT EXISTS wallets (
    -- Using address as primary key (addresses are unique across chains)
    wallet_address VARCHAR PRIMARY KEY,
    
    -- Wallet metadata
    label VARCHAR,  -- Optional label/name
    wallet_type VARCHAR,  -- 'eoa', 'contract', 'multisig'
    
    -- Tracking
    first_seen_timestamp BIGINT,
    last_active_timestamp BIGINT,
    
    -- Stats (can be updated periodically)
    total_transactions INTEGER DEFAULT 0,
    unique_tokens_held INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_wallets_type ON wallets (wallet_type);
CREATE INDEX IF NOT EXISTS idx_wallets_last_active ON wallets (last_active_timestamp);
"""

WALLET_BALANCE_SCHEMA = """
CREATE TABLE IF NOT EXISTS wallet_balances (
    -- Composite key
    wallet_address VARCHAR NOT NULL,
    contract_id VARCHAR NOT NULL,  -- Token contract
    timestamp BIGINT NOT NULL,
    
    -- Balance data
    balance DECIMAL(38, 18) NOT NULL,
    balance_usd DECIMAL(38, 2),
    
    -- Data source
    source VARCHAR DEFAULT 'defillama',
    
    PRIMARY KEY (wallet_address, contract_id, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_balances_wallet_time ON wallet_balances (wallet_address, timestamp);
"""

PROTOCOL_TVL_SCHEMA = """
CREATE TABLE IF NOT EXISTS protocol_tvl (
    -- Protocol identification
    protocol_id VARCHAR NOT NULL,  -- DeFillama protocol ID
    timestamp BIGINT NOT NULL,
    
    -- TVL breakdown
    total_tvl_usd DECIMAL(38, 2) NOT NULL,
    chain_tvls JSON,  -- {"ethereum": 1000000, "polygon": 500000}
    
    -- Token breakdown (optional)
    token_tvls JSON,  -- {"ethereum:0x...": 1000000}
    
    -- Metadata
    mcap DECIMAL(38, 2),
    token_price DECIMAL(38, 18),
    
    PRIMARY KEY (protocol_id, timestamp)
);
"""

# Multi-source data reconciliation table
DATA_SOURCE_MAPPING_SCHEMA = """
CREATE TABLE IF NOT EXISTS data_source_mappings (
    -- Our universal ID
    contract_id VARCHAR NOT NULL,
    
    -- External source IDs
    source_name VARCHAR NOT NULL,  -- 'defillama', 'coingecko', 'graph', etc.
    source_id VARCHAR NOT NULL,     -- Their internal ID
    
    -- Metadata
    is_verified BOOLEAN DEFAULT FALSE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (contract_id, source_name)
);

CREATE INDEX IF NOT EXISTS idx_mapping_source_id ON data_source_mappings (source_name, source_id);
"""


def create_all_tables(connection):
    """Create all tables in the database"""
    schemas = [
        TOKEN_SCHEMA,
        PRICE_HISTORY_SCHEMA,
        LP_POOL_SCHEMA,
        LP_POOL_HISTORY_SCHEMA,
        LP_POSITION_SCHEMA,
        WALLET_SCHEMA,
        WALLET_BALANCE_SCHEMA,
        PROTOCOL_TVL_SCHEMA,
        DATA_SOURCE_MAPPING_SCHEMA
    ]
    
    for schema in schemas:
        connection.execute(schema)
    
    print("✅ All tables created successfully")


def example_queries():
    """Example queries showing how to use contract addresses as identifiers"""
    
    return {
        "get_token_price": """
            SELECT price, timestamp, confidence
            FROM price_history
            WHERE contract_id = 'ethereum:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'  -- USDC
              AND timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT 1
        """,
        
        "get_lp_pool_tvl": """
            SELECT ph.timestamp, ph.tvl_usd, ph.apy_total, p.token_symbols
            FROM lp_pool_history ph
            JOIN lp_pools p ON ph.pool_contract_id = p.pool_contract_id
            WHERE p.pool_contract_id = 'ethereum:0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8'  -- USDC/ETH 0.3%
              AND ph.timestamp BETWEEN ? AND ?
            ORDER BY ph.timestamp
        """,
        
        "cross_source_price_check": """
            -- Compare prices from multiple sources
            SELECT 
                contract_id,
                timestamp,
                source,
                price,
                AVG(price) OVER (PARTITION BY contract_id, timestamp) as avg_price,
                ABS(price - AVG(price) OVER (PARTITION BY contract_id, timestamp)) / price as deviation
            FROM price_history
            WHERE contract_id = ?
              AND timestamp = ?
            ORDER BY source
        """,
        
        "wallet_portfolio": """
            SELECT 
                wb.contract_id,
                t.symbol,
                wb.balance,
                wb.balance_usd,
                ph.price as current_price
            FROM wallet_balances wb
            JOIN tokens t ON wb.contract_id = t.contract_id
            LEFT JOIN price_history ph ON wb.contract_id = ph.contract_id 
                AND ph.timestamp = (SELECT MAX(timestamp) FROM price_history WHERE contract_id = wb.contract_id)
            WHERE wb.wallet_address = ?
              AND wb.timestamp = (SELECT MAX(timestamp) FROM wallet_balances WHERE wallet_address = ?)
        """
    }