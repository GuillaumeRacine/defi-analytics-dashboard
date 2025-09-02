import fs from 'fs'
import path from 'path'
import { cache } from 'react'
import PoolsClient from './PoolsClient'
import { precomputeChartData } from '../../lib/cache'

// Cache pool data loading for better performance
const getPoolData = cache(async () => {
  try {
    const dataPath = path.join(process.cwd(), 'data', 'pool_data.json')
    const fileContent = fs.readFileSync(dataPath, 'utf8')
    const jsonData = JSON.parse(fileContent)
    
    // Precompute chart data for all pools
    const processedData = Object.entries(jsonData).reduce((acc, [pool, data]: [string, any]) => {
      if (data.timeseries && Array.isArray(data.timeseries)) {
        acc[pool] = {
          ...data,
          timeseries: precomputeChartData(data.timeseries)
        }
      } else {
        acc[pool] = data
      }
      return acc
    }, {} as any)
    
    return processedData
  } catch (e) {
    console.error('Error loading pool data:', e)
    return {}
  }
})

// Enable static generation with revalidation
export const revalidate = 3600 // Revalidate every hour

export default async function PoolsPage() {
  const poolData = await getPoolData()
  
  console.log('Pool page - Pool data keys:', Object.keys(poolData))
  console.log('Pool data cached and optimized for fast loading')
  
  return <PoolsClient poolData={poolData} />
}

export const metadata = {
  title: 'Pool Analytics - DeFi Dashboard',
  description: 'Historical TVL and APY analytics for DeFi liquidity pools'
}