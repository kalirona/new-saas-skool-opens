import React from 'react'
import type { Metadata } from 'next'
import OperationsDashboard from '@components/Admin/OperationsDashboard'

export const metadata: Metadata = {
  title: 'Operations',
}

export default function AdminOperationsPage() {
  return (
    <div className="p-8">
      <OperationsDashboard />
    </div>
  )
}
