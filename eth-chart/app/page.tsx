import fs from 'fs'
import path from 'path'
import { cache } from 'react'
import DashboardClient from './components/DashboardClient'
import { precomputeChartData } from '../lib/cache'

// Cache data loading functions for better performance
const getAllTokensData = cache(async () => {
  const dataPath = path.join(process.cwd(), 'data', 'all_tokens_data.json')
  const fileContent = fs.readFileSync(dataPath, 'utf8')
  const jsonData = JSON.parse(fileContent)
  
  // Precompute chart data for all tokens
  const processedData = Object.entries(jsonData).reduce((acc, [token, data]: [string, any]) => {
    if (data.timeseries && Array.isArray(data.timeseries)) {
      acc[token] = {
        ...data,
        timeseries: precomputeChartData(data.timeseries)
      }
    } else {
      acc[token] = data
    }
    return acc
  }, {} as any)
  
  return processedData
})

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

export default async function TokenCharts() {
  const tokensData = await getAllTokensData()
  
  console.log('Token data loaded and cached')
  console.log('Data cached and optimized for fast loading')
  
  return <DashboardClient tokensData={tokensData} poolData={null} />
}

export const metadata = {
  title: 'Token Analytics - DeFi Dashboard',
  description: 'Historical price analytics for DeFi tokens and cryptocurrencies'
}