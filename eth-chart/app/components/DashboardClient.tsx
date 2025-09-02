'use client'

import { useState } from 'react'
import FourTokenCharts from './FourTokenCharts'
import PoolCharts from './PoolCharts'
import TimeWindowFilter, { TimeWindow } from './TimeWindowFilter'

interface DashboardClientProps {
  tokensData: any
  poolData: any
}

export default function DashboardClient({ tokensData, poolData }: DashboardClientProps) {
  const [timeWindow, setTimeWindow] = useState<TimeWindow>('ALL')

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="sticky top-0 bg-black z-10 pt-4 pb-2">
        <TimeWindowFilter selected={timeWindow} onChange={setTimeWindow} />
      </div>
      
      <FourTokenCharts data={tokensData} timeWindow={timeWindow} />
      
      <div className="max-w-7xl mx-auto p-2">
        <div className="mt-8 border-t border-gray-800 pt-6">
          <PoolCharts data={poolData} timeWindow={timeWindow} />
        </div>
        
        <footer className="mt-8 border-t border-gray-800 pt-4 text-center">
          <a href="/table" className="text-blue-400 hover:text-blue-300 text-xs">
            View Table Data →
          </a>
        </footer>
      </div>
    </div>
  )
}