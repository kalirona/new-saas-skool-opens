import React from 'react'
import ResourceClient from './resource-client'
import { getResource } from '@services/resources/resources'
import { getOrganizationContextInfo } from '@services/organizations/orgs'
import { Metadata } from 'next'
import { getResourceThumbnailMediaDirectory, getOrgOgImageMediaDirectory } from '@services/media/media'
import { getServerSession } from '@/lib/auth/server'
import { getOrgSeoConfig, buildPageTitle as buildSeoPageTitle } from '@/lib/seo/utils'
import { buildPageTitle } from '@/lib/brand'
import { getServerCanonicalUrl } from '@/lib/seo/utils.server'

type MetadataProps = {
  params: Promise<{ orgslug: string; resourceuuid: string }>
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}

export async function generateMetadata(props: MetadataProps): Promise<Metadata> {
  const params = await props.params
  const session = await getServerSession()
  const access_token = session?.tokens?.access_token

  const [org, resourceResult] = await Promise.all([
    getOrganizationContextInfo(params.orgslug, {
      revalidate: 120,
      tags: ['organizations'],
    }),
    getResource(params.resourceuuid, access_token ?? undefined).catch(() => null),
  ])

  if (!resourceResult) {
    return {
      title: buildPageTitle('Resource', org?.name),
      description: `View this resource on ${org?.name || ''}`,
    }
  }

  const seoConfig = getOrgSeoConfig(org)
  const defaultTitle = buildSeoPageTitle(resourceResult.title, org.name, seoConfig)
  const defaultDescription = resourceResult.description || seoConfig.default_meta_description || ''
  const orgOgImageUrl = seoConfig.default_og_image
    ? getOrgOgImageMediaDirectory(org?.org_uuid, seoConfig.default_og_image)
    : null
  const defaultImage = resourceResult?.thumbnail_image && resourceResult?.org_uuid
    ? getResourceThumbnailMediaDirectory(
        resourceResult.org_uuid,
        resourceResult?.resource_uuid,
        resourceResult?.thumbnail_image
      )
    : orgOgImageUrl || '/empty_thumbnail.png'

  return {
    title: defaultTitle,
    description: defaultDescription,
    robots: {
      index: true,
      follow: true,
      nocache: true,
      googleBot: {
        index: true,
        follow: true,
        'max-image-preview': 'large',
      },
    },
    alternates: {
      canonical: await getServerCanonicalUrl(params.orgslug, `/resource/${params.resourceuuid}`),
    },
    openGraph: {
      title: defaultTitle,
      description: defaultDescription,
      images: [{ url: defaultImage, width: 800, height: 600, alt: resourceResult.title }],
      type: 'article',
      publishedTime: resourceResult.creation_date || '',
    },
    twitter: {
      card: 'summary_large_image',
      title: defaultTitle,
      description: defaultDescription,
      images: [defaultImage],
    },
  }
}

const ResourcePage = async (props: any) => {
  const { resourceuuid, orgslug } = await props.params
  return <ResourceClient resourceuuid={resourceuuid} orgslug={orgslug} />
}

export default ResourcePage
