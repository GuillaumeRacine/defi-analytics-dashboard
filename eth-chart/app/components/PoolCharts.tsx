'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { TimeWindow, filterDataByTimeWindow } from './TimeWindowFilter'
import LazyChart from './LazyChart'

interface PoolData {
  metadata: {
    pool_id: string
    symbol: string
    chain: string
    protocol: string
    record_count: number
    date_range: {
      start: string
      end: string
    }
    tvl_stats: {
      current?: number
      min: number
      max: number
      avg: number
    }
    apy_stats: {
      min: number
      max: number
      avg: number
    }
    validation?: {
      valid: boolean
      total_days?: number
      date_range?: string
      error?: string
    }
  }
  timeseries: Array<{
    date: string
    tvlUsd?: number
    tvl?: number
    apy: number
    apyBase: number
    apyReward: number
    il7d?: number
    apyBase7d?: number
    interpolated?: boolean
  }>
}

interface Props {
  data: {
    'uniswap-v3'?: PoolData
    'orca'?: PoolData
    'cetus'?: PoolData
    [key: string]: PoolData | undefined
  }
}

const protocolConfig = {
  'uniswap-v3': { color: '#ff007a', name: 'Uniswap V3', chain: 'Ethereum' },
  'orca': { color: '#14f195', name: 'Orca', chain: 'Solana' },
  'cetus': { color: '#4da6ff', name: 'Cetus', chain: 'Sui' },
  'orca-dex': { color: '#14f195', name: 'Orca', chain: 'Solana' },
  'cetus-amm': { color: '#4da6ff', name: 'Cetus', chain: 'Sui' }
}

function PoolChart({ protocol, data, timeWindow }: { protocol: string, data: PoolData, timeWindow: TimeWindow }) {
  const config = protocolConfig[protocol as keyof typeof protocolConfig] || { color: '#666', name: protocol, chain: 'Unknown' }
  
  // Map the data structure to match what the chart expects
  const mappedTimeseries = data.timeseries.map(item => ({
    ...item,
    tvl: item.tvlUsd || item.tvl || 0,  // Handle both tvlUsd and tvl fields
  }))
  
  const chartData = filterDataByTimeWindow(mappedTimeseries, timeWindow)
  const stats = data.metadata
  
  const currentTVL = chartData[chartData.length - 1]?.tvl || 0
  const currentAPY = chartData[chartData.length - 1]?.apy || 0
  
  return (
    <div className="bg-gray-950 border border-gray-800 rounded p-3">
      <div className="flex justify-between items-center mb-2">
        <div>
          <h3 className="text-sm font-bold" style={{ color: config.color }}>
            {stats.symbol} Pool ({config.name})
          </h3>
          <div className="text-xs text-gray-500">
            {stats.chain} • {stats.record_count} daily points
          </div>
        </div>
        <div className="text-right">
          <div className="text-sm font-bold" style={{ color: config.color }}>
            ${currentTVL.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </div>
          <div className="text-xs text-gray-400">
            {currentAPY.toFixed(1)}% APY
          </div>
        </div>
      </div>
      
      <div className="space-y-3 mb-3">
        <LazyChart>
          <div className="bg-gray-900 rounded p-2">
            <div className="text-xs text-gray-500 mb-1">TVL Chart</div>
            <div className="h-40">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="2 2" stroke="#1f2937" strokeWidth={0.5} />
                  <XAxis 
                    dataKey="date"
                    tick={{ fontSize: 7, fill: '#6b7280' }}
                    tickLine={{ stroke: '#374151' }}
                    axisLine={{ stroke: '#374151' }}
                    type="category"
                    tickFormatter={(value, index) => {
                      const date = new Date(value)
                      const totalTicks = chartData.length
                      const interval = Math.max(1, Math.floor(totalTicks / 4))
                      
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
                    tick={{ fontSize: 7, fill: '#6b7280' }}
                    tickLine={{ stroke: '#374151' }}
                    axisLine={{ stroke: '#374151' }}
                    tickFormatter={(value) => {
                      if (value >= 1000000) return `$${(value/1000000).toFixed(0)}M`
                      if (value >= 1000) return `$${(value/1000).toFixed(0)}K`
                      return `$${value.toFixed(0)}`
                    }}
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: '#030712',
                      border: '1px solid #1f2937',
                      borderRadius: '4px',
                      fontSize: '9px',
                      padding: '4px'
                    }}
                    labelStyle={{ color: '#e5e7eb', fontSize: '8px' }}
                    formatter={(value: number) => [`$${value.toLocaleString()}`, 'TVL']}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="tvl" 
                    stroke={config.color}
                    strokeWidth={1}
                    dot={false}
                    activeDot={{ r: 2, fill: config.color }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </LazyChart>
        
        <LazyChart>
          <div className="bg-gray-900 rounded p-2">
            <div className="text-xs text-gray-500 mb-1">APY Chart</div>
            <div className="h-40">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="2 2" stroke="#1f2937" strokeWidth={0.5} />
                  <XAxis 
                    dataKey="date"
                    tick={{ fontSize: 7, fill: '#6b7280' }}
                    tickLine={{ stroke: '#374151' }}
                    axisLine={{ stroke: '#374151' }}
                    type="category"
                    tickFormatter={(value, index) => {
                      const date = new Date(value)
                      const totalTicks = chartData.length
                      const interval = Math.max(1, Math.floor(totalTicks / 4))
                      
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
                    tick={{ fontSize: 7, fill: '#6b7280' }}
                    tickLine={{ stroke: '#374151' }}
                    axisLine={{ stroke: '#374151' }}
                    tickFormatter={(value) => `${value.toFixed(0)}%`}
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: '#030712',
                      border: '1px solid #1f2937',
                      borderRadius: '4px',
                      fontSize: '9px',
                      padding: '4px'
                    }}
                    labelStyle={{ color: '#e5e7eb', fontSize: '8px' }}
                    formatter={(value: number) => [`${value.toFixed(1)}%`, 'APY']}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="apy" 
                    stroke="#10b981"
                    strokeWidth={1}
                    dot={false}
                    activeDot={{ r: 2, fill: "#10b981" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </LazyChart>
      </div>
      
      <div className="grid grid-cols-4 gap-2">
        <div className="text-center">
          <div className="text-xs text-gray-500">Avg TVL</div>
          <div className="text-xs font-mono">${stats.tvl_stats.avg.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500">Avg APY</div>
          <div className="text-xs font-mono">{stats.apy_stats.avg.toFixed(1)}%</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500">Max APY</div>
          <div className="text-xs font-mono">{stats.apy_stats.max.toFixed(1)}%</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500">Days</div>
          <div className="text-xs font-mono">{stats.record_count}</div>
        </div>
      </div>
    </div>
  )
}

export default function PoolCharts({ data, timeWindow }: Props & { timeWindow: TimeWindow }) {
  const availablePools = Object.entries(data).filter(([_, poolData]) => poolData && poolData.timeseries?.length > 0)
  
  if (availablePools.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        No pool data available
      </div>
    )
  }
  
  return (
    <div className="space-y-4">
      <div className="mb-3">
        <h2 className="text-lg font-bold text-white">CLM Pool Analysis</h2>
        <div className="text-xs text-gray-500">
          Historical TVL & APY data • {availablePools.length} pools • DeFillama PRO API
        </div>
      </div>
      
      <div className="grid grid-cols-1 gap-4">
        {availablePools.map(([protocol, poolData]) => (
          <PoolChart key={protocol} protocol={protocol} data={poolData} timeWindow={timeWindow} />
        ))}
      </div>
    </div>
  )
}