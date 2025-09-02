# 📊 How to View Your DeFillama Dataset

## Quick Start
```bash
# Interactive explorer (best for beginners)
python3 query_data.py

# Quick overview
python3 view_data_simple.py
```

## 🔍 CLI Commands

### View Database Structure
```bash
# List all tables with row counts
python3 query_data.py tables

# Inspect specific table (shows schema + data)
python3 query_data.py table tokens
python3 query_data.py table price_history 20
python3 query_data.py table lp_pools
```

### View Token Data
```bash
# All tokens with metadata
python3 query_data.py tokens

# Price history for specific token
python3 query_data.py history WETH
python3 query_data.py history USDC

# Recent prices (last N records)
python3 query_data.py prices 30
```

### Quick Analysis
```bash
# Price summary with statistics
python3 query_data.py summary

# Custom SQL query
python3 query_data.py query "SELECT symbol, COUNT(*) FROM price_history ph JOIN tokens t ON ph.contract_id = t.contract_id GROUP BY symbol"
```

## 📄 CSV Files (Open in Excel/Sheets)

```bash
# View available exports
ls exports/

# Main files:
open exports/price_history_with_symbols.csv  # Complete price data with token names
open exports/tokens.csv                      # Token metadata
```

**CSV Contents:**
- `price_history_with_symbols.csv`: All price data with symbol, timestamp, price, confidence
- `tokens.csv`: Token metadata with contract addresses
- `price_summary.csv`: Statistical summaries

## 💻 Direct Database Access

### Simple Queries
```python
import duckdb
conn = duckdb.connect('data/duckdb/defillama.db')

# Get latest prices
latest = conn.sql("""
    SELECT t.symbol, ph.price, ph.timestamp
    FROM price_history ph
    JOIN tokens t ON ph.contract_id = t.contract_id
    WHERE ph.timestamp = (SELECT MAX(timestamp) FROM price_history)
""")
print(latest)

# Price statistics
stats = conn.sql("""
    SELECT 
        t.symbol,
        COUNT(*) as records,
        MIN(ph.price) as min_price,
        MAX(ph.price) as max_price,
        AVG(ph.price) as avg_price
    FROM price_history ph
    JOIN tokens t ON ph.contract_id = t.contract_id
    GROUP BY t.symbol
""")
print(stats)
```

### Export to CSV
```python
# Export any query to CSV
conn.sql("""
    COPY (
        SELECT t.symbol, ph.price, ph.timestamp
        FROM price_history ph
        JOIN tokens t ON ph.contract_id = t.contract_id
        ORDER BY ph.timestamp
    ) TO 'my_custom_export.csv' (FORMAT CSV, HEADER)
""")
```

## 🏗️ Database Schema Overview

Your data uses **contract addresses as universal identifiers**:

### Key Tables
1. **`tokens`** - Token metadata
   - Primary key: `contract_id` (format: `ethereum:0x...`)
   - Contains: symbol, name, decimals, contract address

2. **`price_history`** - Historical price data
   - Primary key: `(contract_id, timestamp, source)`
   - Contains: price, confidence, source, timestamp

3. **`lp_pools`** - LP pool information
   - Primary key: `pool_contract_id` (format: `ethereum:0x...`)
   - Contains: protocol, token pairs, fee tiers

4. **`data_source_mappings`** - Cross-source ID mapping (for future use)

### Contract ID Format
```
Format: {chain}:{contract_address}
Examples:
- USDC: ethereum:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48
- WETH: ethereum:0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2
- Uni V3 Pool: ethereum:0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8
```

## 🎯 Example Use Cases

### 1. Find Most Volatile Token
```bash
python3 query_data.py query "
SELECT 
    t.symbol,
    (MAX(ph.price) - MIN(ph.price)) / MIN(ph.price) * 100 as volatility_pct
FROM price_history ph
JOIN tokens t ON ph.contract_id = t.contract_id
GROUP BY t.symbol
ORDER BY volatility_pct DESC
"
```

### 2. Price Changes by Day
```bash
python3 query_data.py query "
SELECT 
    t.symbol,
    ph.timestamp,
    ph.price,
    LAG(ph.price) OVER (PARTITION BY t.symbol ORDER BY ph.timestamp) as prev_price
FROM price_history ph
JOIN tokens t ON ph.contract_id = t.contract_id
ORDER BY ph.timestamp DESC
LIMIT 20
"
```

### 3. Cross-Reference with External Data
Since you use contract addresses as IDs, you can easily join with:
- Etherscan data
- The Graph Protocol data
- Dune Analytics exports
- Any blockchain data source

## 🚀 Quick Tips

### View Everything Quickly
```bash
# See all your data in one command
python3 -c "
import duckdb
conn = duckdb.connect('data/duckdb/defillama.db')
print('=== TOKENS ===')
print(conn.sql('SELECT symbol, contract_id FROM tokens'))
print('\n=== LATEST PRICES ===')
print(conn.sql('SELECT t.symbol, ph.price FROM price_history ph JOIN tokens t ON ph.contract_id = t.contract_id WHERE ph.timestamp = (SELECT MAX(timestamp) FROM price_history)'))
print('\n=== PRICE RANGES ===')
print(conn.sql('SELECT t.symbol, MIN(ph.price) as min_p, MAX(ph.price) as max_p FROM price_history ph JOIN tokens t ON ph.contract_id = t.contract_id GROUP BY t.symbol'))
"
```

### Monitor Data Quality
```bash
# Check for any missing confidence scores
python3 query_data.py query "SELECT COUNT(*) as missing_confidence FROM price_history WHERE confidence IS NULL"

# Check data freshness
python3 query_data.py query "SELECT MAX(timestamp) as last_update, (strftime('%s', 'now') - MAX(timestamp)) / 3600 as hours_old FROM price_history"
```

## 🎨 Visualization Options

1. **Excel/Google Sheets**: Open CSV files directly
2. **Python Plotting**: Load CSV into pandas + matplotlib/plotly
3. **Streamlit Dashboard**: `streamlit run dashboard.py` (when fixed)
4. **Custom Scripts**: Use DuckDB connection for real-time charts

---

**Your dataset is working perfectly!** The contract-address approach makes it incredibly easy to expand with additional data sources while maintaining data integrity and cross-compatibility.