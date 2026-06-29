import React from 'react'
import { cn } from '@/lib/utils'

interface ResponsiveGridProps {
  children: React.ReactNode
  className?: string
  cols?: {
    sm?: number
    md?: number
    lg?: number
    xl?: number
  }
}

export function ResponsiveGrid({ children, className, cols }: ResponsiveGridProps) {
  const {
    sm = 1,
    md = 2,
    lg = 3,
    xl = 4,
  } = cols || {}

  return (
    <div
      className={cn(
        `grid gap-4`,
        `grid-cols-${sm}`,
        `sm:grid-cols-${Math.min(sm + 1, 2)}`,
        `md:grid-cols-${md}`,
        `lg:grid-cols-${lg}`,
        `xl:grid-cols-${xl}`,
        className
      )}
    >
      {children}
    </div>
  )
}
