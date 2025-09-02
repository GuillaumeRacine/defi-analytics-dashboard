'use client'

import { useState, useEffect, useRef } from 'react'

interface LazyChartProps {
  children: React.ReactNode
  fallback?: React.ReactNode
  rootMargin?: string
}

export default function LazyChart({ 
  children, 
  fallback = <div className="h-40 bg-gray-900 rounded animate-pulse" />,
  rootMargin = '50px'
}: LazyChartProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [hasLoaded, setHasLoaded] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasLoaded) {
          setIsVisible(true)
          // Add a small delay to ensure smooth loading
          setTimeout(() => setHasLoaded(true), 100)
          observer.disconnect()
        }
      },
      { rootMargin }
    )

    if (ref.current) {
      observer.observe(ref.current)
    }

    return () => observer.disconnect()
  }, [hasLoaded, rootMargin])

  return (
    <div ref={ref}>
      {hasLoaded ? children : fallback}
    </div>
  )
}