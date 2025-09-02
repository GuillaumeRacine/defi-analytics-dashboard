// Data caching utilities for faster app performance

interface CacheEntry<T> {
  data: T
  timestamp: number
  ttl: number
}

class DataCache {
  private cache = new Map<string, CacheEntry<any>>()
  
  set<T>(key: string, data: T, ttlMinutes: number = 60) {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: ttlMinutes * 60 * 1000 // Convert to milliseconds
    })
  }
  
  get<T>(key: string): T | null {
    const entry = this.cache.get(key)
    if (!entry) return null
    
    const now = Date.now()
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key)
      return null
    }
    
    return entry.data
  }
  
  has(key: string): boolean {
    const entry = this.cache.get(key)
    if (!entry) return false
    
    const now = Date.now()
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key)
      return false
    }
    
    return true
  }
  
  clear() {
    this.cache.clear()
  }
  
  size() {
    return this.cache.size
  }
}

// Global cache instance
export const dataCache = new DataCache()

// Precompute aggregations for faster chart rendering
export function precomputeChartData(timeseries: any[]) {
  if (!timeseries || timeseries.length === 0) return timeseries
  
  // Add computed fields for better performance
  return timeseries.map((item, index) => {
    const tvl = item.tvlUsd || item.tvl || 0
    const prevItem = index > 0 ? timeseries[index - 1] : null
    const prevTvl = prevItem ? (prevItem.tvlUsd || prevItem.tvl || 0) : tvl
    
    return {
      ...item,
      tvl,
      tvlChange: prevTvl > 0 ? ((tvl - prevTvl) / prevTvl) * 100 : 0,
      formattedTvl: formatCurrency(tvl),
      formattedApy: `${item.apy?.toFixed(1) || '0.0'}%`
    }
  })
}

function formatCurrency(value: number): string {
  if (value >= 1000000000) return `$${(value / 1000000000).toFixed(1)}B`
  if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`
  if (value >= 1000) return `$${(value / 1000).toFixed(1)}K`
  return `$${value.toFixed(0)}`
}

// Time window data optimization
export function optimizeDataForTimeWindow(data: any[], timeWindow: string): any[] {
  if (timeWindow === 'ALL' || !data || data.length === 0) {
    return data || []
  }
  
  const cacheKey = `optimized_${timeWindow}_${data.length}`
  const cached = dataCache.get<any[]>(cacheKey)
  if (cached && Array.isArray(cached)) return cached
  
  // For shorter time windows, we can reduce data points for better performance
  let optimizedData = data
  
  if (timeWindow === '1W' && data.length > 7) {
    // For 1 week, show every data point
    optimizedData = data.slice(-7)
  } else if (timeWindow === '1M' && data.length > 60) {
    // For 1 month, show every other day if we have too many points
    optimizedData = data.slice(-30)
  } else if (timeWindow === '3M' && data.length > 180) {
    // For 3 months, sample every few days
    optimizedData = data.filter((_, index) => index % 2 === 0 || index >= data.length - 90)
  } else if (timeWindow === '1Y' && data.length > 365) {
    // For 1 year, sample weekly
    optimizedData = data.filter((_, index) => index % 7 === 0 || index >= data.length - 365)
  }
  
  dataCache.set(cacheKey, optimizedData, 30) // Cache for 30 minutes
  return optimizedData
}