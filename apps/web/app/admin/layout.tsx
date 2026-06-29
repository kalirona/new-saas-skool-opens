import type { Metadata } from 'next'
import AdminProviders from './providers'
import React from 'react'
import { BRAND_SEO, BRAND_NAME } from '@/lib/brand'

export const metadata: Metadata = {
  title: {
    template: `%s | ${BRAND_NAME} ${BRAND_SEO.adminTitle}`,
    default: `${BRAND_NAME} ${BRAND_SEO.adminTitle}`,
  },
}

export default function AdminRootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <AdminProviders>{children}</AdminProviders>
}
