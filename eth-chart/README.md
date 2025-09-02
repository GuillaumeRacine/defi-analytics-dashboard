# ETH Price Chart - 5-Year Daily Timeseries

Interactive React chart displaying 1,855 daily ETH price snapshots from Sept 2020 to Sept 2025.

## Features

- **5-Year Dataset**: 1,855 daily price points from DeFillama PRO API
- **Interactive Timeframes**: 1M, 3M, 6M, 1Y, All
- **Minimal UI**: Compact design with small fonts for maximum data density
- **Real-time Stats**: Current price, ATH, ATL, volatility metrics
- **99% Data Confidence**: Professional-grade financial data

## Dataset Stats

- **Date Range**: 2020-09-02 → 2025-09-01
- **Price Range**: $338.19 → $4,844.02 
- **Volatility**: 1,332% over 5 years
- **Data Points**: 1,855 daily snapshots (100% coverage)

## Development

```bash
npm run dev     # Start development server
npm run build   # Build for production
npm run start   # Start production server
```

## Deployment

### Vercel (Recommended)
```bash
vercel --prod
```

### Manual Deploy
1. Run `npm run build`
2. Deploy `.next` folder to any static host
3. Ensure `public/data/eth-timeseries.json` is included

## Data Source

- **API**: DeFillama PRO (1000 req/min, 1M monthly)
- **Contract**: `ethereum:0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2`
- **Collection**: 1,855 API calls at noon UTC daily
- **Storage**: DuckDB with contract-based architecture