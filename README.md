# DeFi Backtesting Dataset

A comprehensive historical dataset system for backtesting DeFi trading strategies, built on DeFillama PRO API with multi-source data integration capabilities.

## 🎯 Project Goal

Build a robust, scalable dataset for backtesting trading algorithms with:
- Historical token prices
- LP pool metrics (TVL, APY, impermanent loss)
- Cross-chain data
- Multi-source validation

## 🏗️ Architecture

### Universal Identifier System
All entities use **contract addresses as UUIDs** for seamless multi-source integration:
- Format: `{chain}:{contract_address}`
- Example: `ethereum:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48` (USDC)

This enables direct integration with:
- DeFillama API
- The Graph Protocol
- Etherscan/Block explorers
- On-chain RPC calls
- Dune Analytics
- Any blockchain data source

### Storage Architecture
```
DuckDB (OLAP) + Parquet Files
├── Tokens (contract_id as primary key)
├── Price History (multi-source with consensus)
├── LP Pools (pool contract addresses)
├── LP Positions (with NFT IDs for Uni V3)
├── Wallets (address-based tracking)
└── Cross-source mappings
```

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Clone repository
git clone <repo>
cd DN_Dataset

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DeFillama API key
```

### 2. Initialize Database
```python
import duckdb
from src.schema import create_all_tables

conn = duckdb.connect('data/duckdb/defillama.db')
create_all_tables(conn)
```

### 3. Fetch Your First Data
```python
from src.collectors import TokenPriceCollector

collector = TokenPriceCollector(api_key="YOUR_KEY")
prices = await collector.fetch_token_price(
    "ethereum:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
    start_date="2024-01-01"
)
```

## 📁 Project Structure

```
DN_Dataset/
├── data/
│   ├── raw/           # Raw API responses
│   ├── parquet/       # Processed Parquet files
│   └── duckdb/        # DuckDB database
├── src/
│   ├── collectors/    # API data collectors
│   ├── validators/    # Data validation
│   ├── backtest/      # Backtesting engine
│   ├── integration/   # Multi-source integration
│   └── utils/         # Utilities
├── docs.md            # API documentation
├── CLAUDE.md          # Development workflow
├── ROADMAP.md         # Project roadmap
└── schema.py          # Database schema
```

## 📊 Key Features

### Multi-Source Data Integration
- Automatic cross-source validation
- Consensus pricing from multiple sources
- Outlier detection and filtering
- Source reliability scoring

### Backtesting Capabilities
- Historical price data (1+ year)
- LP pool performance metrics
- Impermanent loss calculations
- Slippage and fee modeling
- Multi-asset strategies

### Data Quality
- Automatic validation checks
- Stale data detection
- Outlier filtering (>50% changes)
- Missing data interpolation
- Cross-source verification

## 🗺️ Roadmap

### Phase 1: Foundation ✅
- [x] API integration setup
- [x] Database schema design
- [x] Contract-based UUID system
- [x] Multi-source architecture

### Phase 2: Data Collection (Current)
- [ ] Historical data backfill
- [ ] Top 100 tokens coverage
- [ ] Major LP pools (Uniswap, Curve)
- [ ] Validation pipeline

### Phase 3: Backtesting Engine
- [ ] Position tracking
- [ ] Strategy evaluation
- [ ] Performance analytics
- [ ] Risk metrics

### Phase 4: Visualization
- [ ] Streamlit dashboard
- [ ] Interactive charts
- [ ] Strategy comparison

### Phase 5: Production
- [ ] Automated updates
- [ ] Monitoring & alerts
- [ ] Live trading prep

## 🔧 Development Workflow

1. **Research** best practices but choose simplicity
2. **Write** minimal viable code
3. **Test** with real data from user perspective
4. **Validate** data accuracy and completeness
5. **Document** changes and learnings

See [CLAUDE.md](CLAUDE.md) for detailed workflow.

## 🚨 Key Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| API Rate Limits | Smart throttling, caching, batch requests |
| Data Gaps | Multiple sources, interpolation, fallbacks |
| Cross-chain Complexity | Universal contract ID system |
| Storage Scale | DuckDB + Parquet for efficient queries |
| Source Discrepancies | Consensus algorithms, validation |

## 📈 Example Queries

### Get Token Price
```sql
SELECT price, timestamp, confidence
FROM price_history
WHERE contract_id = 'ethereum:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'
ORDER BY timestamp DESC
LIMIT 1;
```

### LP Pool Performance
```sql
SELECT timestamp, tvl_usd, apy_total, il_7d
FROM lp_pool_history
WHERE pool_contract_id = 'ethereum:0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8'
  AND timestamp BETWEEN ? AND ?;
```

### Cross-Source Validation
```sql
SELECT source, price, 
       ABS(price - AVG(price) OVER()) / price as deviation
FROM price_history
WHERE contract_id = ? AND timestamp = ?;
```

## 🤝 Contributing

This is a living project designed for rapid iteration. Key principles:
- **Speed over perfection** - Ship fast, iterate
- **Simple over complex** - Start simple, optimize later
- **Working over ideal** - Get it working first

## 📝 Documentation

- [docs.md](docs.md) - Complete API documentation
- [CLAUDE.md](CLAUDE.md) - Development guidelines
- [ROADMAP.md](ROADMAP.md) - Project roadmap & risks
- [schema.py](src/schema.py) - Database schema

## ⚠️ Important Notes

1. **API Key Required**: Get your DeFillama PRO key first
2. **Contract Addresses**: All IDs use `chain:address` format
3. **Multi-source Ready**: Designed for data source expansion
4. **Validation Critical**: Always validate cross-source data

## 🎯 Next Steps

1. Get DeFillama PRO API key
2. Run initial data collection test
3. Validate data quality
4. Start building strategies
5. Iterate and improve

---

**Philosophy**: Simple and working beats complex and perfect. Build fast, measure, optimize what matters.

**Remember**: This system uses contract addresses as universal identifiers, enabling seamless integration with any blockchain data source.