import React from 'react'
import { Card, CardContent } from '../ui/card'
import { cn } from '@/lib/utils'

interface SectionCardProps {
  children: React.ReactNode
  className?: string
  padding?: boolean
}

export function SectionCard({ children, className, padding = true }: SectionCardProps) {
  return (
    <Card className={cn('bg-white nice-shadow', className)}>
      {padding ? <CardContent className="p-6">{children}</CardContent> : children}
    </Card>
  )
}
