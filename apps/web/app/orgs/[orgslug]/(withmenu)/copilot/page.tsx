import React from 'react'
import { Metadata } from 'next'
import { getOrganizationContextInfo } from '@services/organizations/orgs'
import Copilot from './copilot'
import { getServerSession } from '@/lib/auth/server'
import { buildPageTitle, BRAND_NAME } from '@/lib/brand'

type MetadataProps = {
  params: Promise<{ orgslug: string }>
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}

export async function generateMetadata(props: MetadataProps): Promise<Metadata> {
  const params = await props.params
  const session = await getServerSession()
  const access_token = session?.tokens?.access_token
  const org = await getOrganizationContextInfo(params.orgslug, {
    revalidate: 120,
    tags: ['organizations'],
  }, access_token)
  return {
    title: buildPageTitle('Copilot', org.name),
    description: `MessageSquare with AI about your courses using ${BRAND_NAME} Copilot.`,
  }
}

const CopilotPage = async (params: any) => {
  const orgslug = (await params.params).orgslug

  return (
    <div>
      <Copilot orgslug={orgslug} />
    </div>
  )
}

export default CopilotPage
