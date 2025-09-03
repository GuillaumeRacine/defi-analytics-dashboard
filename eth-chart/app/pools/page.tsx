import fs from 'fs'
import path from 'path'
import { cache } from 'react'
import PoolsClient from './PoolsClient'
import { precomputeChartData } from '../../lib/cache'

// Cache pool registry data loading for better performance
const getPoolRegistry = cache(async () => {
  try {
    const dataPath = path.join(process.cwd(), 'data', 'comprehensive_pool_directory.json')
    const fileContent = fs.readFileSync(dataPath, 'utf8')
    const registryData = JSON.parse(fileContent)
    
    return registryData
  } catch (error) {
    console.error('Error loading comprehensive pool directory:', error)
    console.error('Tried path:', path.join(process.cwd(), 'data', 'comprehensive_pool_directory.json'))
    // Fallback to simple registry
    try {
      const fallbackPath = path.join(process.cwd(), 'data', 'pool_registry_simple.json')
      const fallbackContent = fs.readFileSync(fallbackPath, 'utf8')
      const fallbackData = JSON.parse(fallbackContent)
      console.log('Using fallback simple registry')
      return fallbackData
    } catch (fallbackError) {
      console.error('Fallback also failed:', fallbackError)
      return { pools: {}, last_updated: null }
    }
  }
})

// Cache historical pool data loading
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
  const poolRegistry = await getPoolRegistry()
  const poolData = await getPoolData()
  
  console.log('Pool registry loaded:', Object.keys(poolRegistry.pools || {}).length, 'pools')
  console.log('Pool data cached and optimized for fast loading')
  
  return <PoolsClient poolRegistry={poolRegistry} poolData={poolData} />
}

export const metadata = {
  title: 'Explore Pools - DeFi Pool Directory',
  description: 'Comprehensive directory of 3,718+ pools over $1M TVL from DeFillama with complete metadata and CLM analysis'
}