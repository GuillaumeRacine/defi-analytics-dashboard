# Development Workflow & Guidelines

## Project Goal
Build a historical dataset for backtesting trading algorithms using DeFillama PRO API data, focusing on token prices, LP token prices, and related DeFi metrics.

## Core Development Principles

### 1. Speed Over Complexity
- **Prioritize rapid prototyping** - Get working code quickly, optimize later
- **Use simple solutions first** - SQLite/DuckDB over complex databases
- **Minimal dependencies** - Avoid unnecessary libraries
- **Iterate fast** - Test ideas quickly, fail fast, learn faster

### 2. Development Workflow

#### Step 1: Research & Design
- Research best practices but choose simplest viable option
- Consider maintenance burden vs performance gains
- Document decisions and trade-offs
- Challenge assumptions and propose alternatives

#### Step 2: Write Code
- Start with minimal viable implementation
- Use type hints for clarity
- Keep functions small and focused
- Comment only complex logic

#### Step 3: Test from User Perspective
- Run actual API calls with real data
- Test UI/visualization if applicable
- Verify data accuracy against DeFillama website
- Check for edge cases and errors

#### Step 4: QA & Data Validation
- Implement scripts to detect:
  - Stale data (timestamps too old)
  - Outliers (price spikes/drops > 50%)
  - Missing data points
  - API errors or rate limits
- Log all anomalies for review

#### Step 5: Documentation Updates
- Keep docs.md current with API changes
- Update this CLAUDE.md with learnings
- Document data schema changes
- Maintain clear README for users

## Technology Stack Decisions

### Data Storage: DuckDB + Parquet
**Why:**
- DuckDB excels at analytical queries (OLAP)
- Parquet files provide excellent compression
- Can query files directly without loading to memory
- Supports SQL for familiar querying
- Easy backup (just copy files)

**Structure:**
```
data/
├── raw/              # Raw API responses (JSON)
├── parquet/          # Processed data in Parquet format
│   ├── prices/       # Token price history
│   ├── pools/        # LP pool data
│   ├── tvl/          # Protocol TVL data
│   └── yields/       # Yield/APY data
└── duckdb/           # DuckDB database files
```

### Universal Identifier Strategy: Contract Addresses

**Key Design Decision**: Use contract addresses as universal identifiers (UUIDs) across all data sources.

**Format**: `{chain}:{contract_address}`
- Example: `ethereum:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48` (USDC on Ethereum)

**Benefits**:
1. **Cross-source compatibility**: Same ID works with DeFillama, The Graph, Etherscan, etc.
2. **No translation needed**: Direct blockchain queries possible
3. **Immutable**: Contract addresses don't change
4. **Verifiable**: Can verify on-chain

**Implementation**:
```python
# All entities use contract-based IDs
token_id = "ethereum:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"  # USDC
pool_id = "ethereum:0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"   # Uniswap V3 USDC/ETH
wallet_id = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"          # vitalik.eth

# Data source mapping table tracks external IDs
mappings = {
    "ethereum:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {
        "defillama": "coingecko:usd-coin",
        "coingecko": "usd-coin",
        "graph": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    }
}
```

### Programming Language: Python
**Libraries:**
- `httpx` - Async HTTP client for API calls
- `duckdb` - Database and query engine
- `pandas` - Data manipulation (use sparingly)
- `pyarrow` - Parquet file handling
- `plotly` - Interactive charts
- `streamlit` - Quick data exploration UI

## Data Collection Strategy

### 1. Initial Historical Backfill
- Start with most recent data and work backwards
- Collect 1 year of history initially
- Focus on top 100 tokens by volume
- Include major LP pools (Uniswap V3, Curve)

### 2. Incremental Updates
- Daily updates for active trading pairs
- Hourly updates during high volatility
- Weekly full refresh to catch corrections

### 3. Data Priority
1. **Critical**: Token prices (ETH, BTC, stables)
2. **Important**: LP pool TVL and APY
3. **Useful**: Protocol TVL, volumes
4. **Nice-to-have**: User metrics, fees

## API Rate Limit Management

```python
class RateLimiter:
    def __init__(self, calls_per_second=10):
        self.calls_per_second = calls_per_second
        self.last_call = 0
    
    async def wait(self):
        elapsed = time.time() - self.last_call
        if elapsed < 1/self.calls_per_second:
            await asyncio.sleep(1/self.calls_per_second - elapsed)
        self.last_call = time.time()
```

## Critical Data Quality Standards

### Timeseries Completeness Requirements
**MANDATORY**: All timeseries data MUST have consecutive days with ZERO gaps between start and end dates.

### Standardized Data Quality Pipeline
For ALL new token or pool data ingestion, use the standardized pipeline:

```bash
# Validate only (check for gaps)
python3 scripts/data_quality_pipeline.py --validate-only

# Process specific token
python3 scripts/data_quality_pipeline.py --token BTC

# Process specific pool  
python3 scripts/data_quality_pipeline.py --pool uniswap-v3

# Process everything
python3 scripts/data_quality_pipeline.py --all
```

### Data Ingestion Workflow
1. **Initial Data Collection**: Collect raw data from DeFillama API
2. **Validation**: Run pipeline validation to detect gaps
3. **Gap Filling**: Use pipeline to systematically fill ALL missing dates
4. **Re-validation**: Confirm zero gaps before deployment
5. **Deployment**: Update production data files only after validation passes

### Quality Assurance Checklist
- [ ] No missing days between start and end dates
- [ ] No duplicate dates in timeseries
- [ ] Proper metadata updates (record counts, date ranges, price stats)
- [ ] Rate limiting applied (0.15s between API calls)
- [ ] Sequential processing to avoid database locks
- [ ] Batch processing for large datasets (50 items per batch)

### Current Data Coverage (As of 2025-09-02)
- **BTC**: 1,825 days (2020-09-02 to 2025-08-31) ✓ Complete, Zero Gaps
- **ETH**: 1,826 days (2020-09-02 to 2025-09-01) ✓ Complete, Zero Gaps  
- **SOL**: 1,825 days (2020-09-02 to 2025-08-31) ✓ Complete, Zero Gaps
- **SUI**: 854 days (2023-05-03 to 2025-09-01) ✓ Complete, Zero Gaps
- **Uniswap V3 Pool**: 365+ days ✓ Complete
- **Orca Pool**: 180+ days ✓ Complete
- **Cetus Pool**: 120+ days ✓ Complete

### Error Recovery Procedures
1. **API Timeout Errors**: Retry with exponential backoff
2. **Missing Data Points**: Use gap filling pipeline with rate limiting
3. **Duplicate Dates**: Remove duplicates keeping chronologically last occurrence
4. **Data Validation Failures**: Do not deploy until all issues resolved

## Data Quality Checks

### Price Data Validation
```python
def validate_price(token, price, timestamp):
    # Check for zero/negative prices
    if price <= 0:
        return False, "Invalid price"
    
    # Check for extreme changes (>50% in 1 hour)
    last_price = get_last_price(token, timestamp - 3600)
    if last_price:
        change = abs(price - last_price) / last_price
        if change > 0.5:
            return False, f"Extreme price change: {change:.2%}"
    
    # Check timestamp is reasonable
    if timestamp > time.time() or timestamp < 1420070400:  # Before 2015
        return False, "Invalid timestamp"
    
    return True, "Valid"
```

### LP Pool Validation
```python
def validate_lp_pool(pool_data):
    # Check TVL is positive
    if pool_data['tvlUsd'] <= 0:
        return False, "Invalid TVL"
    
    # Check APY is reasonable (0-1000%)
    if not 0 <= pool_data['apy'] <= 1000:
        return False, f"Unrealistic APY: {pool_data['apy']}"
    
    # Check underlying tokens exist
    if not pool_data.get('underlyingTokens'):
        return False, "Missing underlying tokens"
    
    return True, "Valid"
```

## Query Patterns for Backtesting

### Get Price at Timestamp
```sql
SELECT price, confidence 
FROM prices 
WHERE token = ? 
  AND timestamp <= ? 
ORDER BY timestamp DESC 
LIMIT 1
```

### Get LP Pool Performance
```sql
SELECT 
    date,
    tvlUsd,
    apy,
    volume_24h,
    fees_24h
FROM lp_pools 
WHERE pool_id = ?
  AND date BETWEEN ? AND ?
ORDER BY date
```

### Calculate Returns
```sql
WITH price_data AS (
    SELECT 
        token,
        timestamp,
        price,
        LAG(price) OVER (PARTITION BY token ORDER BY timestamp) as prev_price
    FROM prices
    WHERE token IN (?)
      AND timestamp BETWEEN ? AND ?
)
SELECT 
    token,
    timestamp,
    price,
    (price - prev_price) / prev_price as return_pct
FROM price_data
WHERE prev_price IS NOT NULL
```

## Error Handling Strategy

1. **API Errors**: Exponential backoff with max retries
2. **Data Errors**: Log and skip, continue processing
3. **Critical Errors**: Alert and stop processing
4. **Rate Limits**: Automatic throttling

## Performance Optimization Tips

1. **Batch API Calls**: Use batch endpoints when available
2. **Parallel Processing**: Use asyncio for concurrent requests
3. **Cache Frequently Used Data**: Redis or in-memory cache
4. **Partition Data**: By date/chain for faster queries
5. **Index Strategically**: On timestamp, token, pool_id

## Monitoring & Alerts

- Track API credit usage
- Monitor data freshness
- Alert on validation failures > threshold
- Log query performance metrics

## Next Steps Checklist

- [ ] Set up DuckDB database schema
- [ ] Implement data collection scripts
- [ ] Build data validation pipeline
- [ ] Create backtesting framework
- [ ] Develop visualization dashboard
- [ ] Write comprehensive tests
- [ ] Deploy monitoring system

## Critical Thinking Notes

### Challenges to Address
1. **API Key Management**: Secure storage, rotation
2. **Data Gaps**: Handle missing historical data
3. **Chain Differences**: Normalize cross-chain data
4. **Decimal Precision**: Maintain accuracy for small values
5. **Timestamp Alignment**: Standardize to UTC

### Alternative Approaches to Consider
1. **Graph Protocol**: For on-chain data
2. **Direct RPC Calls**: For real-time data
3. **Multiple Data Sources**: Cross-validation
4. **Event-Driven Updates**: WebSocket subscriptions

Remember: **Simple and working beats complex and perfect**. Start simple, measure, then optimize only what matters for your trading strategy.