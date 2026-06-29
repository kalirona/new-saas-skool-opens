'use client'

import React from 'react'
import { Inbox } from 'lucide-react'

interface EmptyStateProps {
  icon?: React.ReactNode
  title: string
  description?: string
  action?: React.ReactNode
  className?: string
}

export default function EmptyState({
  icon,
  title,
  description,
  action,
  className = '',
}: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center py-16 px-6 ${className}`}>
      <div className="w-16 h-16 rounded-2xl bg-gray-100 flex items-center justify-center mb-5">
        {icon || <Inbox size={32} className="text-gray-400" />}
      </div>
      <h3 className="text-lg font-semibold text-gray-600 mb-1.5 text-center">
        {title}
      </h3>
      {description && (
        <p className="text-sm text-gray-400 text-center max-w-sm mb-5">
          {description}
        </p>
      )}
      {action && (
        <div>
          {action}
        </div>
      )}
    </div>
  )
}
