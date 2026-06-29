import { Metadata } from 'next'
import React from 'react'
import ClientAdminLayout from './ClientAdminLayout'
import { BRAND_SEO } from '@/lib/brand'

export const metadata: Metadata = {
  title: BRAND_SEO.dashboardTitle,
}

async function DashboardLayout(
  props: {
    children: React.ReactNode
    params: Promise<any>
  }
) {
  const params = await props.params;

  const {
    children
  } = props;

  return (
    <>
      <ClientAdminLayout
        params={params}>
        {children}
      </ClientAdminLayout>
    </>
  )
}

export default DashboardLayout
