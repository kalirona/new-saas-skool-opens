import { getOrganizationContextInfo } from '@services/organizations/orgs'
import { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { getServerSession } from '@/lib/auth/server'
import { getCommunity } from '@services/communities/communities'
import { getSpace } from '@services/communities/spaces'
import { getDiscussions, DiscussionWithAuthor } from '@services/communities/discussions'
import { getOrgThumbnailMediaDirectory, getOrgOgImageMediaDirectory } from '@services/media/media'
import { getOrgSeoConfig, buildPageTitle, buildBreadcrumbJsonLd } from '@/lib/seo/utils'
import { getServerCanonicalUrl } from '@/lib/seo/utils.server'
import { JsonLd } from '@components/SEO/JsonLd'
import SpaceClient from './space-client'

type MetadataProps = {
  params: Promise<{ orgslug: string; communityuuid: string; spaceuuid: string }>
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}

export async function generateMetadata(props: MetadataProps): Promise<Metadata> {
  const params = await props.params
  const org = await getOrganizationContextInfo(params.orgslug, {
    revalidate: 120,
    tags: ['organizations'],
  })

  const communityUuid = `community_${params.communityuuid}`
  const spaceUuid = params.spaceuuid.startsWith('space_') ? params.spaceuuid : `space_${params.spaceuuid}`
  let community = null
  let space = null
  try {
    community = await getCommunity(communityUuid, { revalidate: 120, tags: ['communities'] })
    space = await getSpace(spaceUuid)
  } catch {
    // not found or no access
  }

  const seoConfig = getOrgSeoConfig(org)
  const title = buildPageTitle(space ? space.name : 'Space', org.name, seoConfig)
  const description = space?.description || community?.description || seoConfig.default_meta_description || `Space discussions from ${org.name}`

  const ogImageUrl = seoConfig.default_og_image
    ? getOrgOgImageMediaDirectory(org?.org_uuid, seoConfig.default_og_image)
    : null
  const imageUrl = ogImageUrl || getOrgThumbnailMediaDirectory(org?.org_uuid, org?.thumbnail_image)
  const canonical = await getServerCanonicalUrl(params.orgslug, `/community/${params.communityuuid}`)

  return {
    title,
    description,
    robots: {
      index: !seoConfig.noindex_communities,
      follow: true,
      nocache: true,
    },
    openGraph: {
      title: `${title} — ${org.name}`,
      description,
      type: 'article',
      url: canonical,
      images: imageUrl ? [{ url: imageUrl, width: 800, height: 600 }] : [],
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
      images: imageUrl ? [imageUrl] : [],
    },
    alternates: { canonical },
  }
}

export default async function SpacePage(props: { params: Promise<{ orgslug: string; communityuuid: string; spaceuuid: string }> }) {
  const session = await getServerSession()
  const access_token = session?.tokens?.access_token
  const params = await props.params
  const org = await getOrganizationContextInfo(params.orgslug, { revalidate: 120, tags: ['organizations'] })
  if (!org) notFound()

  const communityUuid = `community_${params.communityuuid}`
  const spaceUuid = params.spaceuuid.startsWith('space_') ? params.spaceuuid : `space_${params.spaceuuid}`

  let community = null
  let space = null
  let communityError: { status?: number } | null = null
  let initialDiscussions: DiscussionWithAuthor[] = []
  try {
    community = await getCommunity(communityUuid, { revalidate: 120, tags: ['communities'] }, access_token ? access_token : undefined)
  } catch (error: any) {
    communityError = { status: error?.status }
  }

  if (community) {
    try {
      space = await getSpace(spaceUuid, access_token ? access_token : undefined)
    } catch {
      space = null
    }
    if (space) {
      try {
        initialDiscussions = await getDiscussions(
          communityUuid, 'recent', 1, 50, { revalidate: 30, tags: ['discussions'] },
          access_token ? access_token : undefined, undefined, space.id
        )
      } catch {
        initialDiscussions = []
      }
    }
  }

  if (!community && (!communityError || !access_token)) {
    notFound()
  }
  if (!community || !space) {
    notFound()
  }

  const breadcrumbJsonLd = buildBreadcrumbJsonLd([
    { name: 'Home', url: await getServerCanonicalUrl(params.orgslug, '/') },
    { name: 'Communities', url: await getServerCanonicalUrl(params.orgslug, '/communities') },
    { name: community.name, url: await getServerCanonicalUrl(params.orgslug, `/community/${params.communityuuid}`) },
    { name: space.name },
  ])

  return (
    <>
      <JsonLd data={breadcrumbJsonLd} />
      <SpaceClient
        community={community}
        space={space}
        initialDiscussions={initialDiscussions}
        orgslug={params.orgslug}
        org_id={org.id}
      />
    </>
  )
}
