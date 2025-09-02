'use client'

import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

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
    BTC: TokenData
    ETH: TokenData
    SOL: TokenData
    SUI: TokenData
  }
}

const tokenColors = {
  BTC: '#f7931a',
  ETH: '#627eea',
  SOL: '#14f195',
  SUI: '#4da6ff'
}

export default function MultiTokenChart({ data }: Props) {
  const [mounted, setMounted] = useState(false)
  const [selectedTokens, setSelectedTokens] = useState<string[]>(['BTC', 'ETH'])
  
  useEffect(() => {
    setMounted(true)
  }, [])

  // Normalize data to overlapping date range
  const allDates = new Set<string>()
  Object.values(data).forEach(token => {
    token.timeseries.forEach(point => allDates.add(point.date))
  })
  
  const sortedDates = Array.from(allDates).sort()
  
  // Create unified chart data
  const chartData = sortedDates.map(date => {
    const dataPoint: any = { date }
    
    Object.entries(data).forEach(([symbol, tokenData]) => {
      const point = tokenData.timeseries.find(p => p.date === date)
      dataPoint[symbol] = point?.price || null
    })
    
    return dataPoint
  }).filter(point => selectedTokens.some(token => point[token] !== null))

  const toggleToken = (token: string) => {
    setSelectedTokens(prev => 
      prev.includes(token) 
        ? prev.filter(t => t !== token)
        : [...prev, token]
    )
  }

  return (
    <div className="min-h-screen bg-black text-white p-2 font-mono">
      <div className="max-w-6xl mx-auto">
        <div className="mb-3">
          <h1 className="text-sm font-bold">Multi-Token Price Charts - DeFillama PRO API</h1>
          <div className="text-xs text-gray-500">
            {Object.values(data).reduce((sum, token) => sum + token.timeseries.length, 0).toLocaleString()} total data points
          </div>
        </div>

        {/* Token toggles */}
        <div className="grid grid-cols-4 gap-2 mb-3">
          {Object.entries(data).map(([symbol, tokenData]) => (
            <button
              key={symbol}
              onClick={() => toggleToken(symbol)}
              className={`bg-gray-950 border rounded p-2 text-left transition-all ${
                selectedTokens.includes(symbol) 
                  ? 'border-gray-600 shadow-lg' 
                  : 'border-gray-800 opacity-60 hover:opacity-80'
              }`}
            >
              <div className="text-xs text-gray-500">{symbol}</div>
              <div className="text-sm font-bold" style={{ color: selectedTokens.includes(symbol) ? tokenColors[symbol as keyof typeof tokenColors] : '#9ca3af' }}>
                ${tokenData.metadata.price_stats.avg.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </div>
              <div className="text-xs text-gray-600">
                {tokenData.metadata.record_count} pts
              </div>
            </button>
          ))}
        </div>

        {/* Price stats for selected tokens */}
        <div className="grid grid-cols-2 gap-2 mb-3">
          {selectedTokens.map(symbol => {
            const token = data[symbol as keyof typeof data]
            const currentPrice = token.timeseries[token.timeseries.length - 1]?.price || 0
            return (
              <div key={symbol} className="bg-gray-950 border border-gray-800 rounded p-2">
                <div className="flex justify-between items-center">
                  <div>
                    <div className="text-xs text-gray-500">{symbol} Current</div>
                    <div className="text-sm font-bold" style={{ color: tokenColors[symbol as keyof typeof tokenColors] }}>
                      ${currentPrice.toLocaleString()}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-gray-500">Range</div>
                    <div className="text-xs text-gray-400">
                      ${token.metadata.price_stats.min.toLocaleString(undefined, { maximumFractionDigits: 0 })} - ${token.metadata.price_stats.max.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Chart */}
        <div className="bg-gray-950 border border-gray-800 rounded p-3">
          {mounted ? (
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="2 2" stroke="#1f2937" strokeWidth={0.5} />
                  <XAxis 
                    dataKey="date"
                    tick={{ fontSize: 9, fill: '#6b7280' }}
                    tickLine={{ stroke: '#374151' }}
                    axisLine={{ stroke: '#374151' }}
                    interval="preserveStartEnd"
                  />
                  <YAxis 
                    tick={{ fontSize: 9, fill: '#6b7280' }}
                    tickLine={{ stroke: '#374151' }}
                    axisLine={{ stroke: '#374151' }}
                    tickFormatter={(value) => `$${value.toLocaleString()}`}
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
                    formatter={(value: number, name: string) => [
                      value ? `$${value.toLocaleString()}` : 'No data', 
                      name
                    ]}
                  />
                  <Legend 
                    wrapperStyle={{ fontSize: '10px' }}
                  />
                  {selectedTokens.map(symbol => (
                    <Line 
                      key={symbol}
                      type="monotone" 
                      dataKey={symbol} 
                      stroke={tokenColors[symbol as keyof typeof tokenColors]}
                      strokeWidth={1.5}
                      dot={false}
                      activeDot={{ r: 3, fill: tokenColors[symbol as keyof typeof tokenColors] }}
                      connectNulls={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-96 flex items-center justify-center">
              <div className="text-xs text-gray-500">Chart loading...</div>
            </div>
          )}
        </div>

        <div className="text-center text-xs text-gray-600 mt-3">
          Updated {new Date().toLocaleDateString()} • {selectedTokens.join(', ')} selected
        </div>
      </div>
    </div>
  )
}