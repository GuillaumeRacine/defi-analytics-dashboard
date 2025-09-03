'use client'

import { useState, useMemo } from 'react'
import PoolCharts from '../components/PoolCharts'
import TimeWindowFilter, { TimeWindow } from '../components/TimeWindowFilter'
import Link from 'next/link'
import { Search, ExternalLink, Copy, Filter } from 'lucide-react'

interface PoolsClientProps {
  poolRegistry: {
    pools: Record<string, any>
    last_updated: string | null
  }
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

export default function PoolsClient({ poolRegistry, poolData }: PoolsClientProps) {
  const [timeWindow, setTimeWindow] = useState<TimeWindow>('ALL')
  const [isChangingTimeWindow, setIsChangingTimeWindow] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedProtocol, setSelectedProtocol] = useState<string>('all')
  const [selectedChain, setSelectedChain] = useState<string>('all')
  const [copiedAddress, setCopiedAddress] = useState<string | null>(null)

  // Memoize pool registry data processing
  const { pools, protocols, chains, poolCount } = useMemo(() => {
    if (!poolRegistry.pools) return { pools: [], protocols: [], chains: [], poolCount: 0 }
    
    const poolEntries = Object.entries(poolRegistry.pools)
    const protocolSet = new Set<string>()
    const chainSet = new Set<string>()
    
    poolEntries.forEach(([_, pool]) => {
      protocolSet.add(pool.protocol)
      chainSet.add(pool.chain)
    })
    
    return {
      pools: poolEntries,
      protocols: Array.from(protocolSet).sort(),
      chains: Array.from(chainSet).sort(),
      poolCount: poolEntries.length
    }
  }, [poolRegistry])

  // Filter pools based on search and filters
  const filteredPools = useMemo(() => {
    return pools.filter(([poolId, pool]) => {
      const matchesSearch = searchTerm === '' || 
        pool.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        poolId.toLowerCase().includes(searchTerm.toLowerCase()) ||
        pool.contract_address.toLowerCase().includes(searchTerm.toLowerCase())
      
      const matchesProtocol = selectedProtocol === 'all' || pool.protocol === selectedProtocol
      const matchesChain = selectedChain === 'all' || pool.chain === selectedChain
      
      return matchesSearch && matchesProtocol && matchesChain
    })
  }, [pools, searchTerm, selectedProtocol, selectedChain])

  const handleTimeWindowChange = async (newTimeWindow: TimeWindow) => {
    setIsChangingTimeWindow(true)
    await new Promise(resolve => setTimeout(resolve, 100))
    setTimeWindow(newTimeWindow)
    setIsChangingTimeWindow(false)
  }

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedAddress(text)
      setTimeout(() => setCopiedAddress(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const formatTVL = (tvl: number | undefined | null) => {
    if (!tvl || typeof tvl !== 'number' || isNaN(tvl)) return '$0'
    if (tvl >= 1000000000) return `$${(tvl / 1000000000).toFixed(1)}B`
    if (tvl >= 1000000) return `$${(tvl / 1000000).toFixed(1)}M`
    if (tvl >= 1000) return `$${(tvl / 1000).toFixed(1)}K`
    return `$${tvl.toFixed(0)}`
  }

  // Show loading if no data
  if (!poolRegistry.pools) {
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
              <Link href="/" className="text-gray-400 hover:text-white text-sm transition-colors">
                ← Tokens
              </Link>
              <h1 className="text-lg font-bold text-white">Explore Pools</h1>
            </nav>
            
            <Link href="/table" className="text-blue-400 hover:text-blue-300 text-sm transition-colors">
              View Table →
            </Link>
          </div>
          
          {/* Search and Filters */}
          <div className="space-y-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search pools, addresses, or tokens..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg pl-10 pr-4 py-2 text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none"
              />
            </div>
            
            {/* Filters */}
            <div className="flex flex-wrap gap-4">
              <div className="flex items-center space-x-2">
                <Filter className="w-4 h-4 text-gray-400" />
                <select
                  value={selectedProtocol}
                  onChange={(e) => setSelectedProtocol(e.target.value)}
                  className="bg-gray-900 border border-gray-700 rounded px-3 py-1 text-sm text-white focus:border-blue-500 focus:outline-none"
                >
                  <option value="all">All Protocols</option>
                  {protocols.map(protocol => (
                    <option key={protocol} value={protocol}>{protocol}</option>
                  ))}
                </select>
              </div>
              
              <select
                value={selectedChain}
                onChange={(e) => setSelectedChain(e.target.value)}
                className="bg-gray-900 border border-gray-700 rounded px-3 py-1 text-sm text-white focus:border-blue-500 focus:outline-none"
              >
                <option value="all">All Chains</option>
                {chains.map(chain => (
                  <option key={chain} value={chain}>{chain}</option>
                ))}
              </select>
            </div>
            
            {/* Stats */}
            <div className="text-xs text-gray-500 flex items-center space-x-4">
              <span>{filteredPools.length} of {poolCount} pools</span>
              <span>•</span>
              <span>{protocols.length} Protocols</span>
              <span>•</span>
              <span>{chains.length} Chains</span>
              <span>•</span>
              <span className="text-green-500">Over $1M TVL</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Pool Registry Content */}
      <div className="max-w-7xl mx-auto p-4">
        <div className="space-y-3">
          {filteredPools.map(([poolId, pool]) => (
            <div key={poolId} className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:bg-gray-800 transition-colors">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <h3 className="font-semibold text-white">{pool.name}</h3>
                    <span className="px-2 py-1 text-xs bg-blue-900 text-blue-200 rounded">
                      {pool.protocol}
                    </span>
                    <span className="px-2 py-1 text-xs bg-purple-900 text-purple-200 rounded">
                      {pool.chain}
                    </span>
                    {pool.clm_analysis && (
                      <span className={`px-2 py-1 text-xs rounded ${
                        pool.clm_analysis.level === 'excellent' ? 'bg-green-900 text-green-200' :
                        pool.clm_analysis.level === 'good' ? 'bg-blue-900 text-blue-200' :
                        pool.clm_analysis.level === 'moderate' ? 'bg-yellow-900 text-yellow-200' :
                        'bg-gray-700 text-gray-300'
                      }`}>
                        CLM: {pool.clm_analysis.level}
                      </span>
                    )}
                  </div>
                  
                  <div className="mt-2 space-y-1">
                    <div className="flex items-center space-x-4 text-sm text-gray-400">
                      <span>Universal ID: <span className="text-gray-300 font-mono text-xs">{poolId}</span></span>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-gray-400">Contract:</span>
                      <span className="font-mono text-xs text-gray-300">{pool.contract_address}</span>
                      <button
                        onClick={() => copyToClipboard(pool.contract_address)}
                        className="text-gray-400 hover:text-white transition-colors"
                        title="Copy address"
                      >
                        <Copy className="w-3 h-3" />
                      </button>
                      {copiedAddress === pool.contract_address && (
                        <span className="text-xs text-green-400">Copied!</span>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="text-lg font-bold text-white">
                    {formatTVL(pool.metrics?.tvl_usd)}
                  </div>
                  <div className="text-xs text-gray-400">TVL</div>
                  {pool.metrics?.apy_total && (
                    <div className="text-sm text-green-400">
                      {pool.metrics.apy_total.toFixed(2)}% APY
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          
          {filteredPools.length === 0 && (
            <div className="text-center py-8">
              <div className="text-gray-400">No pools found matching your filters.</div>
              <button
                onClick={() => {
                  setSearchTerm('')
                  setSelectedProtocol('all')
                  setSelectedChain('all')
                }}
                className="mt-2 text-blue-400 hover:text-blue-300 text-sm transition-colors"
              >
                Clear filters
              </button>
            </div>
          )}
        </div>
      </div>
      
      {/* Footer */}
      <footer className="border-t border-gray-800 mt-8 pt-4 pb-8 text-center">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-center space-x-8 text-sm">
            <Link href="/" className="text-blue-400 hover:text-blue-300 transition-colors">
              Token Charts
            </Link>
            <Link href="/table" className="text-blue-400 hover:text-blue-300 transition-colors">
              Data Tables
            </Link>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            DeFi Pool Registry • {poolCount} Pools across Orca, Aerodrome & Cetus
          </p>
        </div>
      </footer>
    </div>
  )
}