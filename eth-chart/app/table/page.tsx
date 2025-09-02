'use client'

import { useState, useEffect } from 'react'
import { filterDataByTimeWindow, TimeWindow } from '../components/TimeWindowFilter'

interface TokenData {
  metadata: {
    symbol: string
    record_count: number
    date_range: {
      start: string
      end: string
    }
  }
  timeseries: Array<{
    date: string
    price: number
    confidence: number
  }>
}

interface PoolData {
  pool_info: {
    symbol: string
    chain: string
    tvl: number
  }
  metadata: {
    record_count: number
    date_range: {
      start: string
      end: string
    }
  }
  timeseries: Array<{
    date: string
    tvl: number
    apy: number
    volume_1d: number
  }>
}

interface TableRow {
  date: string
  BTC_price?: number
  ETH_price?: number
  SOL_price?: number
  SUI_price?: number
  uniswap_v3_tvl?: number
  uniswap_v3_apy?: number
  orca_dex_tvl?: number
  orca_dex_apy?: number
  cetus_amm_tvl?: number
  cetus_amm_apy?: number
}

export default function TableView() {
  const [tokenData, setTokenData] = useState<Record<string, TokenData>>({})
  const [poolData, setPoolData] = useState<Record<string, PoolData>>({})
  const [timeWindow, setTimeWindow] = useState<TimeWindow>('ALL')
  const [tableData, setTableData] = useState<TableRow[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      try {
        const [tokenResponse, poolResponse] = await Promise.all([
          fetch('/data/all_tokens_data.json'),
          fetch('/data/pool_data.json').catch(() => null)
        ])

        const tokens = await tokenResponse.json()
        const pools = poolResponse ? await poolResponse.json() : {}

        setTokenData(tokens)
        setPoolData(pools)
      } catch (error) {
        console.error('Error loading data:', error)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  useEffect(() => {
    if (Object.keys(tokenData).length === 0) return

    const allDates = new Set<string>()
    
    Object.values(tokenData).forEach(token => {
      if (token?.timeseries) {
        const filtered = filterDataByTimeWindow(token.timeseries, timeWindow)
        filtered.forEach(item => allDates.add(item.date))
      }
    })

    Object.values(poolData).forEach(pool => {
      if (pool?.timeseries) {
        const filtered = filterDataByTimeWindow(pool.timeseries, timeWindow)
        filtered.forEach(item => allDates.add(item.date))
      }
    })

    const sortedDates = Array.from(allDates).sort()
    
    const rows: TableRow[] = sortedDates.map(date => {
      const row: TableRow = { date }

      if (tokenData.BTC?.timeseries) {
        const filtered = filterDataByTimeWindow(tokenData.BTC.timeseries, timeWindow)
        const btcData = filtered.find(item => item.date === date)
        if (btcData) row.BTC_price = btcData.price
      }

      if (tokenData.ETH?.timeseries) {
        const filtered = filterDataByTimeWindow(tokenData.ETH.timeseries, timeWindow)
        const ethData = filtered.find(item => item.date === date)
        if (ethData) row.ETH_price = ethData.price
      }

      if (tokenData.SOL?.timeseries) {
        const filtered = filterDataByTimeWindow(tokenData.SOL.timeseries, timeWindow)
        const solData = filtered.find(item => item.date === date)
        if (solData) row.SOL_price = solData.price
      }

      if (tokenData.SUI?.timeseries) {
        const filtered = filterDataByTimeWindow(tokenData.SUI.timeseries, timeWindow)
        const suiData = filtered.find(item => item.date === date)
        if (suiData) row.SUI_price = suiData.price
      }

      if (poolData['uniswap-v3']?.timeseries) {
        const filtered = filterDataByTimeWindow(poolData['uniswap-v3'].timeseries, timeWindow)
        const uniData = filtered.find(item => item.date === date)
        if (uniData) {
          row.uniswap_v3_tvl = uniData.tvl
          row.uniswap_v3_apy = uniData.apy
        }
      }

      if (poolData['orca-dex']?.timeseries) {
        const filtered = filterDataByTimeWindow(poolData['orca-dex'].timeseries, timeWindow)
        const orcaData = filtered.find(item => item.date === date)
        if (orcaData) {
          row.orca_dex_tvl = orcaData.tvl
          row.orca_dex_apy = orcaData.apy
        }
      }

      if (poolData['cetus-amm']?.timeseries) {
        const filtered = filterDataByTimeWindow(poolData['cetus-amm'].timeseries, timeWindow)
        const cetusData = filtered.find(item => item.date === date)
        if (cetusData) {
          row.cetus_amm_tvl = cetusData.tvl
          row.cetus_amm_apy = cetusData.apy
        }
      }

      return row
    })

    setTableData(rows)
  }, [tokenData, poolData, timeWindow])

  if (loading) {
    return (
      <div className="bg-black text-white min-h-screen flex items-center justify-center">
        <div className="text-sm text-gray-500">Loading data...</div>
      </div>
    )
  }

  return (
    <div className="bg-black text-white min-h-screen p-4 font-mono">
      <div className="max-w-7xl mx-auto">
        <div className="mb-4">
          <h1 className="text-lg font-bold mb-2">Data Table View</h1>
          <div className="text-xs text-gray-500 mb-4">
            Daily data for all tokens and pools • {tableData.length} rows
          </div>
          
          <div className="flex gap-2 mb-4">
            {(['ALL', '3Y', '1Y', '6M', '3M', '1M', '1W'] as TimeWindow[]).map((window) => (
              <button
                key={window}
                onClick={() => setTimeWindow(window)}
                className={`px-2 py-1 text-xs rounded border ${
                  timeWindow === window
                    ? 'bg-blue-600 border-blue-500 text-white'
                    : 'bg-gray-800 border-gray-700 text-gray-300 hover:bg-gray-700'
                }`}
              >
                {window}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="border-b border-gray-800">
                <th className="text-left p-2 text-gray-400">Date</th>
                <th className="text-right p-2 text-orange-400">BTC Price</th>
                <th className="text-right p-2 text-blue-400">ETH Price</th>
                <th className="text-right p-2 text-green-400">SOL Price</th>
                <th className="text-right p-2 text-cyan-400">SUI Price</th>
                <th className="text-right p-2 text-pink-400">Uni TVL</th>
                <th className="text-right p-2 text-pink-300">Uni APY</th>
                <th className="text-right p-2 text-emerald-400">Orca TVL</th>
                <th className="text-right p-2 text-emerald-300">Orca APY</th>
                <th className="text-right p-2 text-sky-400">Cetus TVL</th>
                <th className="text-right p-2 text-sky-300">Cetus APY</th>
              </tr>
            </thead>
            <tbody>
              {tableData.map((row, index) => (
                <tr key={row.date} className={`border-b border-gray-900 ${index % 2 === 0 ? 'bg-gray-950' : 'bg-black'} hover:bg-gray-900`}>
                  <td className="p-2 text-gray-300 font-mono">{row.date}</td>
                  <td className="p-2 text-right text-orange-300">
                    {row.BTC_price ? `$${row.BTC_price.toLocaleString(undefined, { maximumFractionDigits: 0 })}` : '-'}
                  </td>
                  <td className="p-2 text-right text-blue-300">
                    {row.ETH_price ? `$${row.ETH_price.toLocaleString(undefined, { maximumFractionDigits: 0 })}` : '-'}
                  </td>
                  <td className="p-2 text-right text-green-300">
                    {row.SOL_price ? `$${row.SOL_price.toFixed(2)}` : '-'}
                  </td>
                  <td className="p-2 text-right text-cyan-300">
                    {row.SUI_price ? `$${row.SUI_price.toFixed(3)}` : '-'}
                  </td>
                  <td className="p-2 text-right text-pink-300">
                    {row.uniswap_v3_tvl ? `$${(row.uniswap_v3_tvl / 1000000).toFixed(1)}M` : '-'}
                  </td>
                  <td className="p-2 text-right text-pink-200">
                    {row.uniswap_v3_apy ? `${row.uniswap_v3_apy.toFixed(1)}%` : '-'}
                  </td>
                  <td className="p-2 text-right text-emerald-300">
                    {row.orca_dex_tvl ? `$${(row.orca_dex_tvl / 1000000).toFixed(1)}M` : '-'}
                  </td>
                  <td className="p-2 text-right text-emerald-200">
                    {row.orca_dex_apy ? `${row.orca_dex_apy.toFixed(1)}%` : '-'}
                  </td>
                  <td className="p-2 text-right text-sky-300">
                    {row.cetus_amm_tvl ? `$${(row.cetus_amm_tvl / 1000000).toFixed(1)}M` : '-'}
                  </td>
                  <td className="p-2 text-right text-sky-200">
                    {row.cetus_amm_apy ? `${row.cetus_amm_apy.toFixed(1)}%` : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-4 text-center">
          <a href="/" className="text-blue-400 hover:text-blue-300 text-xs">
            ← Back to Charts
          </a>
        </div>
      </div>
    </div>
  )
}