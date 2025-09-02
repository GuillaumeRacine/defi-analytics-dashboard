# DeFillama PRO API Documentation

## Overview

Complete API documentation for DeFillama, the leading DeFi analytics platform. This includes both free and Pro endpoints (🔒), covering TVL data, token prices, yields, and more.

## Base URLs

- **Main Pro API**: `https://pro-api.llama.fi` (Most endpoints)
- **Bridge API**: `https://bridges.llama.fi` (Cross-chain bridge data)

## Authentication

### Pro Endpoints (🔒)
API key is inserted between base URL and endpoint:
```
https://pro-api.llama.fi/<YOUR_API_KEY>/<ENDPOINT>
```

### Free Endpoints
No authentication required:
```
https://bridges.llama.fi/<ENDPOINT>
```

## API Categories

### 1. TVL & Protocol Data

#### Core TVL Endpoints

**GET /api/protocols** - List all protocols with current TVL
```json
Response: [{
  "id": "2269",
  "name": "Aave",
  "symbol": "AAVE",
  "category": "Lending",
  "chains": ["Ethereum", "Polygon"],
  "tvl": 5200000000,
  "change_1d": 2.3
}]
```

**GET /api/protocol/{protocol}** - Detailed protocol data including historical TVL
- Parameters: protocol (e.g., "aave", "uniswap")
- Returns: Complete protocol info with historical TVL arrays

**GET /api/tvl/{protocol}** - Simple current TVL number
- Returns: Single float value

🔒 **GET /api/tokenProtocols/{symbol}** - Shows which protocols hold a specific token
- Parameters: symbol (e.g., "usdt", "dai")

🔒 **GET /api/inflows/{protocol}/{timestamp}** - Daily capital flows
- Parameters: protocol slug, Unix timestamp at 00:00 UTC

#### Chain TVL Data

**GET /api/v2/chains** - Current TVL of all chains

**GET /api/v2/historicalChainTvl** - Historical TVL for all chains

**GET /api/v2/historicalChainTvl/{chain}** - Historical TVL for specific chain

🔒 **GET /api/chainAssets** - Asset breakdown across all chains

### 2. Price & Coin Data

**GET /coins/prices/current/{coins}** - Current prices for specified coins
- Format: "chain:address" (e.g., "ethereum:0x...")
- Optional: searchWidth parameter ("4h", "24h")

**GET /coins/prices/historical/{timestamp}/{coins}** - Historical prices at specific timestamp

**POST /coins/batchHistorical** - Batch historical price queries
```json
Request: {
  "coins": {
    "ethereum:0x...": [1640995200, 1641081600],
    "bsc:0x...": [1640995200]
  }
}
```

**GET /coins/chart/{coins}** - Price chart data with configurable intervals
- Parameters: period ("1d", "7d", "30d", "90d", "180d", "365d")
- Optional: span (data point interval in hours)

**GET /coins/percentage/{coins}** - Price change percentages

**GET /coins/prices/first/{coins}** - First recorded price for coins

**GET /coins/block/{chain}/{timestamp}** - Get block number at timestamp

### 3. Yields & Farming

🔒 **GET /yields/pools** - All yield pools with current APY
```json
Response: {
  "status": "success",
  "data": [{
    "pool": "747c1d2a-c668-4682-b9f9-296708a3dd90",
    "chain": "Ethereum",
    "project": "aave-v3",
    "symbol": "USDC",
    "tvlUsd": 1500000000,
    "apy": 3.5,
    "apyBase": 2.5,
    "apyReward": 1.0
  }]
}
```

🔒 **GET /yields/chart/{pool}** - Historical APY/TVL for a pool

🔒 **GET /yields/poolsBorrow** - Borrowing rates across protocols

🔒 **GET /yields/chartLendBorrow/{pool}** - Historical lend/borrow rates

🔒 **GET /yields/perps** - Perpetual futures funding rates

🔒 **GET /yields/lsdRates** - Liquid staking derivative rates

### 4. User & Activity Metrics

🔒 **GET /api/activeUsers** - Active users for all protocols

🔒 **GET /api/userData/{type}/{protocolId}** - Historical user metrics
- Types: "activeUsers", "uniqueActiveUsers", "dailyTxs", "gasUsd"

### 5. Volume Metrics

**GET /api/overview/dexs** - Aggregated DEX volumes
- Optional: excludeTotalDataChart, dataType parameters

**GET /api/overview/dexs/{chain}** - DEX volumes for specific chain

**GET /api/summary/dexs/{protocol}** - Specific DEX protocol volumes

**GET /api/overview/options** - Options trading volumes

**GET /api/summary/options/{protocol}** - Specific options protocol data

🔒 **GET /api/overview/derivatives** - Aggregated derivatives data

🔒 **GET /api/summary/derivatives/{protocol}** - Specific derivatives protocol

### 6. Fees & Revenue

**GET /api/overview/fees** - Protocol fees overview
- Optional: dataType ("dailyFees", "dailyRevenue", "dailyHoldersRevenue")

**GET /api/overview/fees/{chain}** - Fees for specific chain

**GET /api/summary/fees/{protocol}** - Specific protocol fees

### 7. Unlocks & Emissions

🔒 **GET /api/emissions** - All tokens with unlock schedules

🔒 **GET /api/emission/{protocol}** - Detailed vesting schedule

### 8. Ecosystem Data

🔒 **GET /api/categories** - TVL by category

🔒 **GET /api/forks** - Protocol fork relationships

🔒 **GET /api/oracles** - Oracle protocol data

🔒 **GET /api/entities** - Company/entity information

🔒 **GET /api/treasuries** - Protocol treasury balances

### 9. ETF Data

🔒 **GET /etfs** - All ETF products and holdings

🔒 **GET /etf/{etf}** - Specific ETF data

🔒 **GET /etfHoldings/{etf}** - Historical holdings for ETF

🔒 **GET /etfInflows** - Aggregated ETF flows

🔒 **GET /etfInflows/{etf}** - Specific ETF inflows

### 10. Bridges

**GET /bridges** (Base: bridges.llama.fi) - All bridge volumes and transactions

**GET /bridge/{id}** - Specific bridge data

**GET /bridgevolume/{chain}** - Chain-specific bridge volumes

**GET /bridgedaystats/{timestamp}/{chain}** - Daily bridge statistics

**GET /transactions/{id}** - Large bridge transactions

### 11. Account Management

🔒 **GET /api/getApiKey** - Verify API key validity

🔒 **GET /api/getApiCredits** - Check remaining API credits

## Important Notes for Backtesting

### Key Endpoints for Historical Data

1. **Token Prices**: Use `/coins/prices/historical/{timestamp}/{coins}` or `/coins/batchHistorical` for bulk queries
2. **LP Tokens**: Track via `/yields/chart/{pool}` for historical APY/TVL
3. **Protocol TVL**: Use `/api/protocol/{protocol}` for complete historical data
4. **Yields**: Access `/yields/pools` for current and `/yields/chart/{pool}` for historical

### Rate Limits & Best Practices

- Pro API provides higher rate limits
- Batch requests when possible (e.g., batchHistorical for prices)
- Cache frequently accessed data locally
- Use appropriate searchWidth parameters for price queries

### Data Freshness

- Current prices updated every 10 minutes
- TVL data updated hourly
- Yield rates updated every 6 hours
- User metrics updated daily

## Example Usage

### Get Historical Token Price
```python
# Get ETH price on Jan 1, 2024
GET https://pro-api.llama.fi/YOUR_KEY/coins/prices/historical/1704067200/ethereum:0x0000000000000000000000000000000000000000
```

### Get LP Pool Historical Data
```python
# Get Uniswap V3 USDC/ETH pool history
GET https://pro-api.llama.fi/YOUR_KEY/yields/chart/747c1d2a-c668-4682-b9f9-296708a3dd90
```

### Batch Historical Prices
```python
POST https://pro-api.llama.fi/YOUR_KEY/coins/batchHistorical
Body: {
  "coins": {
    "ethereum:0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": [1704067200, 1704153600],
    "ethereum:0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": [1704067200]
  }
}
```

## Data Structure Notes

- Timestamps are Unix timestamps (seconds since epoch)
- Prices include confidence scores
- TVL values are in USD
- APY values are percentages (3.5 = 3.5%)
- All monetary values in USD unless specified