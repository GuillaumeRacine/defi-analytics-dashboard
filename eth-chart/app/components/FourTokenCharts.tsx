'use client'

import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import TimeWindowFilter, { TimeWindow, filterDataByTimeWindow } from './TimeWindowFilter'

interface TokenData {
  metadata: {
    symbol: string
    record_count: number
    date_range: {
      start: string
      end: string
    }
    price_stats: {
      min: number
      max: number
      avg: number
      volatility: number
    }
  }
  timeseries: Array<{
    date: string
    price: number
    confidence: number
  }>
}

interface Props {
  data: {
    BTC?: TokenData
    ETH?: TokenData
    SOL?: TokenData
    SUI?: TokenData
  }
}

const tokenConfig = {
  BTC: { color: '#f7931a', name: 'Bitcoin' },
  ETH: { color: '#627eea', name: 'Ethereum' },
  SOL: { color: '#14f195', name: 'Solana' },
  SUI: { color: '#4da6ff', name: 'Sui' }
}

function TokenChart({ symbol, data, timeWindow }: { symbol: string, data: TokenData, timeWindow: TimeWindow }) {
  const config = tokenConfig[symbol as keyof typeof tokenConfig]
  const chartData = filterDataByTimeWindow(data.timeseries, timeWindow)
  const currentPrice = chartData[chartData.length - 1]?.price || 0
  const firstPrice = chartData[0]?.price || 0
  const priceChange = firstPrice > 0 ? ((currentPrice - firstPrice) / firstPrice) * 100 : 0
  
  return (
    <div className="bg-gray-950 border border-gray-800 rounded p-3">
      <div className="flex justify-between items-center mb-2">
        <div>
          <h3 className="text-sm font-bold" style={{ color: config.color }}>
            {config.name} ({symbol})
          </h3>
          <div className="text-xs text-gray-500">
            {data.metadata.record_count} daily points
          </div>
        </div>
        <div className="text-right">
          <div className="text-sm font-bold" style={{ color: config.color }}>
            ${currentPrice.toLocaleString(undefined, { maximumFractionDigits: 2 })}
          </div>
          <div className={`text-xs ${priceChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(1)}%
          </div>
        </div>
      </div>
      
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
            <CartesianGrid strokeDasharray="2 2" stroke="#1f2937" strokeWidth={0.5} />
            <XAxis 
              dataKey="date"
              tick={{ fontSize: 8, fill: '#6b7280' }}
              tickLine={{ stroke: '#374151' }}
              axisLine={{ stroke: '#374151' }}
              type="category"
              scale="point"
              tickFormatter={(value, index) => {
                const date = new Date(value)
                const totalTicks = chartData.length
                
                // Show fewer, more readable ticks
                const interval = Math.max(1, Math.floor(totalTicks / 5))
                
                if (index % interval === 0 || index === 0 || index === totalTicks - 1) {
                  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                  const month = months[date.getMonth()]
                  const year = date.getFullYear().toString().slice(-2)
                  return `${month} '${year}`
                }
                return ''
              }}
            />
            <YAxis 
              tick={{ fontSize: 8, fill: '#6b7280' }}
              tickLine={{ stroke: '#374151' }}
              axisLine={{ stroke: '#374151' }}
              tickFormatter={(value) => {
                if (value >= 1000) return `$${(value/1000).toFixed(0)}k`
                if (value >= 1) return `$${value.toFixed(0)}`
                return `$${value.toFixed(2)}`
              }}
              domain={['dataMin * 0.95', 'dataMax * 1.05']}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: '#030712',
                border: '1px solid #1f2937',
                borderRadius: '4px',
                fontSize: '10px',
                padding: '6px'
              }}
              labelStyle={{ color: '#e5e7eb', fontSize: '9px' }}
              formatter={(value: number) => [`$${value.toLocaleString()}`, symbol]}
            />
            <Line 
              type="monotone" 
              dataKey="price" 
              stroke={config.color}
              strokeWidth={1.5}
              dot={false}
              activeDot={{ r: 2, fill: config.color }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      <div className="grid grid-cols-3 gap-2 mt-2">
        <div className="text-center">
          <div className="text-xs text-gray-500">Low</div>
          <div className="text-xs font-mono">${data.metadata.price_stats.min.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500">Avg</div>
          <div className="text-xs font-mono">${data.metadata.price_stats.avg.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500">High</div>
          <div className="text-xs font-mono">${data.metadata.price_stats.max.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
        </div>
      </div>
    </div>
  )
}

export default function FourTokenCharts({ data, timeWindow }: Props & { timeWindow: TimeWindow }) {
  const [mounted, setMounted] = useState(false)
  
  useEffect(() => {
    setMounted(true)
  }, [])

  const availableTokens = Object.entries(data).filter(([_, tokenData]) => tokenData && tokenData.timeseries?.length > 0)

  return (
    <div className="bg-black text-white p-2 font-mono">
      <div className="max-w-7xl mx-auto">
        <div className="mb-3">
          <h1 className="text-sm font-bold">Crypto Price Charts - 5 Year Daily Series</h1>
          <div className="text-xs text-gray-500">
            DeFillama PRO API • {availableTokens.length} tokens • Daily snapshots at 12:00 UTC
          </div>
        </div>

        {!mounted ? (
          <div className="flex items-center justify-center h-96">
            <div className="text-xs text-gray-500">Loading charts...</div>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {availableTokens.map(([symbol, tokenData]) => (
              <TokenChart key={symbol} symbol={symbol} data={tokenData} timeWindow={timeWindow} />
            ))}
            
            {availableTokens.length === 0 && (
              <div className="col-span-2 text-center text-gray-500 py-8">
                No token data available
              </div>
            )}
          </div>
        )}

        <div className="text-center text-xs text-gray-600 mt-3">
          Data coverage: {availableTokens.map(([symbol, data]) => 
            `${symbol} (${data.metadata.record_count} days)`
          ).join(' • ')}
        </div>
      </div>
    </div>
  )
}