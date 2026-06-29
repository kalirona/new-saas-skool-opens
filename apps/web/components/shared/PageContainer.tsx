import React from 'react'
import { cn } from '@/lib/utils'

interface PageContainerProps {
  children: React.ReactNode
  className?: string
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full'
}

const maxWidthClasses = {
  sm: 'max-w-screen-sm',
  md: 'max-w-screen-md',
  lg: 'max-w-screen-lg',
  xl: 'max-w-screen-xl',
  '2xl': 'max-w-(--breakpoint-2xl)',
  full: 'max-w-full',
}

export function PageContainer({ children, className, maxWidth = '2xl' }: PageContainerProps) {
  return (
    <div className={cn("mx-auto px-4 sm:px-6 lg:px-8 py-5", maxWidthClasses[maxWidth], className)}>
      {children}
    </div>
  )
}
