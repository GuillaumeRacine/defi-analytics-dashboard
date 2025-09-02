'use client'

import { useState } from 'react'

export type TimeWindow = 'ALL' | '3Y' | '1Y' | '6M' | '3M' | '1M' | '1W'

interface TimeWindowFilterProps {
  selected: TimeWindow
  onChange: (window: TimeWindow) => void
}

const windows: { value: TimeWindow; label: string }[] = [
  { value: 'ALL', label: 'All' },
  { value: '3Y', label: '3Y' },
  { value: '1Y', label: '1Y' },
  { value: '6M', label: '6M' },
  { value: '3M', label: '3M' },
  { value: '1M', label: '1M' },
  { value: '1W', label: '1W' },
]

export default function TimeWindowFilter({ selected, onChange }: TimeWindowFilterProps) {
  return (
    <div className="flex justify-center mb-4">
      <div className="inline-flex bg-gray-900 rounded-lg p-1">
        {windows.map((window) => (
          <button
            key={window.value}
            onClick={() => onChange(window.value)}
            className={`
              px-3 py-1 rounded-md text-xs font-medium transition-all
              ${selected === window.value 
                ? 'bg-blue-600 text-white' 
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }
            `}
          >
            {window.label}
          </button>
        ))}
      </div>
    </div>
  )
}

export function filterDataByTimeWindow(data: any[], timeWindow: TimeWindow): any[] {
  if (timeWindow === 'ALL' || !data || data.length === 0) {
    return data
  }

  const now = new Date()
  let cutoffDate = new Date()

  switch (timeWindow) {
    case '3Y':
      cutoffDate.setFullYear(now.getFullYear() - 3)
      break
    case '1Y':
      cutoffDate.setFullYear(now.getFullYear() - 1)
      break
    case '6M':
      cutoffDate.setMonth(now.getMonth() - 6)
      break
    case '3M':
      cutoffDate.setMonth(now.getMonth() - 3)
      break
    case '1M':
      cutoffDate.setMonth(now.getMonth() - 1)
      break
    case '1W':
      cutoffDate.setDate(now.getDate() - 7)
      break
  }

  return data.filter(item => {
    const itemDate = new Date(item.date)
    return itemDate >= cutoffDate
  })
}