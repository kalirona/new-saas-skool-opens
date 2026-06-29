import { getOrganizationContextInfo } from '@services/organizations/orgs'
import { Metadata } from 'next'
import React from 'react'
import ResourcesHome from '@components/Dashboard/Home/ResourcesHome'

type MetadataProps = {
  params: Promise<{ orgslug: string }>
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}

export async function generateMetadata(props: MetadataProps): Promise<Metadata> {
  const params = await props.params
  const org = await getOrganizationContextInfo(params.orgslug, {
    revalidate: 120,
    tags: ['organizations'],
  })

  return {
    title: 'Resources — ' + org.name,
    description: `Manage resources for ${org.name}`,
    robots: {
      index: false,
      follow: false,
    },
  }
}

async function ResourcesPage(props: { params: Promise<{ orgslug: string }> }) {
  return <ResourcesHome />
}

export default ResourcesPage
