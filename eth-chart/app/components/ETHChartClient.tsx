'use client'

import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface PriceData {
  date: string
  price: number
}

interface Props {
  data: {
    timeseries: PriceData[]
    metadata: any
  }
}

export default function ETHChartClient({ data }: Props) {
  const [mounted, setMounted] = useState(false)
  
  useEffect(() => {
    setMounted(true)
  }, [])

  const chartData = data.timeseries
  const currentPrice = chartData[chartData.length - 1]?.price || 0
  const minPrice = Math.min(...chartData.map(d => d.price))
  const maxPrice = Math.max(...chartData.map(d => d.price))

  return (
    <div className="min-h-screen bg-black text-white p-2 font-mono">
      <div className="max-w-6xl mx-auto">
        <div className="mb-3">
          <h1 className="text-sm font-bold">ETH Price Chart - 5 Year Daily Timeseries</h1>
          <div className="text-xs text-gray-500">
            {chartData.length.toLocaleString()} daily snapshots • DeFillama PRO API
          </div>
        </div>

        <div className="grid grid-cols-4 gap-2 mb-3">
          <div className="bg-gray-950 border border-gray-800 rounded p-2">
            <div className="text-xs text-gray-500">Current</div>
            <div className="text-sm font-bold text-emerald-400">${currentPrice.toLocaleString()}</div>
          </div>
          <div className="bg-gray-950 border border-gray-800 rounded p-2">
            <div className="text-xs text-gray-500">All-Time High</div>
            <div className="text-sm font-bold text-cyan-400">${maxPrice.toLocaleString()}</div>
          </div>
          <div className="bg-gray-950 border border-gray-800 rounded p-2">
            <div className="text-xs text-gray-500">All-Time Low</div>
            <div className="text-sm font-bold text-amber-400">${minPrice.toLocaleString()}</div>
          </div>
          <div className="bg-gray-950 border border-gray-800 rounded p-2">
            <div className="text-xs text-gray-500">Data Points</div>
            <div className="text-sm font-bold text-violet-400">{chartData.length.toLocaleString()}</div>
          </div>
        </div>

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
                    formatter={(value: number) => [`$${value.toLocaleString()}`, 'ETH']}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="price" 
                    stroke="#00ffff" 
                    strokeWidth={1.5}
                    dot={false}
                    activeDot={{ r: 3, fill: '#00ffff' }}
                  />
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
          ethereum:0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2 • Updated {new Date().toLocaleDateString()}
        </div>
      </div>
    </div>
  )
}