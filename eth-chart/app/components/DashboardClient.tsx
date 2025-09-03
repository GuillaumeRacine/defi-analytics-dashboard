'use client'

import { useState, useMemo } from 'react'
import Link from 'next/link'
import FourTokenCharts from './FourTokenCharts'
import TimeWindowFilter, { TimeWindow } from './TimeWindowFilter'

interface DashboardClientProps {
  tokensData: any
  poolData: any
}

// Loading skeleton component
function LoadingSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-8 bg-gray-800 rounded mb-4"></div>
      <div className="space-y-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="border border-gray-800 rounded p-4">
            <div className="h-6 bg-gray-800 rounded mb-2"></div>
            <div className="h-32 bg-gray-900 rounded mb-2"></div>
            <div className="h-32 bg-gray-900 rounded"></div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function DashboardClient({ tokensData, poolData }: DashboardClientProps) {
  const [timeWindow, setTimeWindow] = useState<TimeWindow>('ALL')
  const [isChangingTimeWindow, setIsChangingTimeWindow] = useState(false)

  // Memoize expensive computations
  const tokenCount = useMemo(() => {
    return tokensData ? Object.keys(tokensData).length : 0
  }, [tokensData])

  const handleTimeWindowChange = async (newTimeWindow: TimeWindow) => {
    setIsChangingTimeWindow(true)
    
    // Add a small delay to show loading state
    await new Promise(resolve => setTimeout(resolve, 100))
    
    setTimeWindow(newTimeWindow)
    setIsChangingTimeWindow(false)
  }

  // Show loading if no data
  if (!tokensData) {
    return (
      <div className="min-h-screen bg-black text-white p-4">
        <LoadingSkeleton />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <div className="sticky top-0 bg-black/95 backdrop-blur-sm z-10 pt-4 pb-2 border-b border-gray-800/50">
        <div className="max-w-7xl mx-auto px-4">
          {/* Navigation */}
          <div className="flex items-center justify-between mb-4">
            <nav className="flex items-center space-x-6">
              <h1 className="text-lg font-bold text-white">Token Analytics</h1>
              <Link href="/pools" className="text-gray-400 hover:text-white text-sm transition-colors">
                Pools →
              </Link>
            </nav>
            
            <Link href="/table" className="text-blue-400 hover:text-blue-300 text-sm transition-colors">
              View Table →
            </Link>
          </div>
          
          {/* Time Window Filter */}
          <div className="flex flex-col items-center space-y-2">
            <TimeWindowFilter selected={timeWindow} onChange={handleTimeWindowChange} />
            
            {/* Token summary */}
            <div className="text-xs text-gray-500 flex items-center space-x-4">
              <span>{tokenCount} tokens</span>
              <span>•</span>
              <span>Price Analytics</span>
              <span>•</span>
              <span className="text-green-500">Cached & Optimized</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Token Content */}
      <div className={`transition-opacity duration-200 ${isChangingTimeWindow ? 'opacity-50' : 'opacity-100'}`}>
        {tokensData && <FourTokenCharts data={tokensData} timeWindow={timeWindow} />}
      </div>
      
      {/* Footer */}
      <footer className="border-t border-gray-800 mt-8 pt-4 pb-8 text-center">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-center space-x-8 text-sm">
            <Link href="/pools" className="text-blue-400 hover:text-blue-300 transition-colors">
              Explore Pools
            </Link>
            <Link href="/table" className="text-blue-400 hover:text-blue-300 transition-colors">
              Data Tables
            </Link>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            DeFi Token Analytics • Historical Price Data
          </p>
        </div>
      </footer>
    </div>
  )
}