import fs from 'fs'
import path from 'path'
import DashboardClient from './components/DashboardClient'

async function getAllTokensData() {
  const dataPath = path.join(process.cwd(), 'data', 'all_tokens_data.json')
  const fileContent = fs.readFileSync(dataPath, 'utf8')
  const jsonData = JSON.parse(fileContent)
  return jsonData
}

async function getPoolData() {
  try {
    const dataPath = path.join(process.cwd(), 'data', 'pool_data.json')
    const fileContent = fs.readFileSync(dataPath, 'utf8')
    const jsonData = JSON.parse(fileContent)
    return jsonData
  } catch (e) {
    return {}
  }
}

export default async function TokenCharts() {
  const tokensData = await getAllTokensData()
  const poolData = await getPoolData()
  
  return <DashboardClient tokensData={tokensData} poolData={poolData} />
}