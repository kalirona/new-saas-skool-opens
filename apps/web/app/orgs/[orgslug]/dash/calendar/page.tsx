import { getOrganizationContextInfo } from '@services/organizations/orgs'
import { Metadata } from 'next'
import React from 'react'
import CalendarClient from './CalendarClient'

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
    title: 'Calendar — ' + org.name,
    description: `View and manage events for ${org.name}`,
    robots: {
      index: false,
      follow: false,
    },
  }
}

async function CalendarPage() {
  return <CalendarClient />
}

export default CalendarPage
