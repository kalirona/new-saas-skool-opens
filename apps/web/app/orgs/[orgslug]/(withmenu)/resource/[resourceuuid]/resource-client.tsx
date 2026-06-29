'use client'
import Link from 'next/link'
import React from 'react'
import { getUriWithOrg } from '@services/config/config'
import { getResource, getResources, ResourceDetail } from '@services/resources/resources'
import GeneralWrapperStyled from '@components/Objects/StyledElements/Wrappers/GeneralWrapper'
import { getResourceThumbnailMediaDirectory } from '@services/media/media'
import { FileText, Video, Link as LinkIcon, Download, File, Music, BookCopy, Calendar, User, ArrowLeft, ExternalLink, Lock, Globe, ChevronRight, Crown } from 'lucide-react'
import { useOrg } from '@components/Contexts/OrgContext'
import { Breadcrumbs } from '@components/Objects/Breadcrumbs/Breadcrumbs'
import { useLHSession } from '@components/Contexts/LHSessionContext'
import { useQuery } from '@tanstack/react-query'
import { queryKeys } from '@/lib/query/keys'
import { useTranslation } from 'react-i18next'

function ResourceTypeIcon({ type, size = 24 }: { type: string; size?: number }) {
  switch (type) {
    case 'pdf': return <FileText size={size} className="text-red-500" />
    case 'video': return <Video size={size} className="text-blue-500" />
    case 'audio': return <Music size={size} className="text-purple-500" />
    case 'link': return <LinkIcon size={size} className="text-indigo-500" />
    case 'file':
    case 'zip': return <File size={size} className="text-green-500" />
    case 'download': return <Download size={size} className="text-green-500" />
    case 'markdown':
    case 'rich_text':
    case 'ai_prompt':
    case 'template': return <FileText size={size} className="text-amber-500" />
    case 'external_embed': return <ExternalLink size={size} className="text-cyan-500" />
    default: return <File size={size} className="text-gray-500" />
  }
}

function ResourceTypeBadge({ type }: { type: string }) {
  const labels: Record<string, string> = {
    pdf: 'PDF', video: 'Video', audio: 'Audio', link: 'Link',
    file: 'File', zip: 'Archive', download: 'Download',
    markdown: 'Markdown', rich_text: 'Rich Text', ai_prompt: 'AI Prompt',
    template: 'Template', external_embed: 'Embed',
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gray-100 text-gray-700 text-xs font-medium">
      <ResourceTypeIcon type={type} size={14} />
      {labels[type] || type}
    </span>
  )
}

const ResourceClient = (props: { resourceuuid: string; orgslug: string }) => {
  const { t } = useTranslation()
  const { resourceuuid, orgslug } = props
  const org = useOrg() as any
  const session = useLHSession() as any
  const access_token = session?.data?.tokens?.access_token

  const { data: resource, error, isLoading } = useQuery({
    queryKey: queryKeys.resources.detail(resourceuuid),
    queryFn: () => getResource(resourceuuid, access_token),
    enabled: !!resourceuuid,
    staleTime: 60_000,
  })

  const { data: relatedResources } = useQuery({
    queryKey: [...queryKeys.resources.list(org?.id), 'related', resource?.community_id],
    queryFn: () => getResources(org?.id, { community_id: resource?.community_id, limit: 6 }, access_token),
    enabled: !!org?.id && !!resource?.community_id,
    staleTime: 60_000,
  })

  if (isLoading) {
    return (
      <GeneralWrapperStyled>
        <div className="animate-pulse space-y-6">
          <div className="h-4 bg-gray-200 rounded w-1/3" />
          <div className="h-[300px] bg-gray-200 rounded-lg" />
          <div className="space-y-3">
            <div className="h-8 bg-gray-200 rounded w-2/3" />
            <div className="h-4 bg-gray-200 rounded w-full" />
            <div className="h-4 bg-gray-200 rounded w-5/6" />
          </div>
        </div>
      </GeneralWrapperStyled>
    )
  }

  if (error || !resource) {
    return (
      <GeneralWrapperStyled>
        <div className="flex flex-col items-center justify-center min-h-[50vh] text-center px-4">
          <h2 className="text-xl font-semibold text-gray-700 mb-2">
            {t('resource.notFound', 'Resource not found')}
          </h2>
          <p className="text-gray-500 mb-4">
            {t('resource.loadError', 'This resource could not be found or you do not have access.')}
          </p>
          <Link href={getUriWithOrg(orgslug, '/library')} className="text-blue-600 hover:underline">
            {t('resource.backToLibrary', 'Back to Library')}
          </Link>
        </div>
      </GeneralWrapperStyled>
    )
  }

  const coverUrl = resource.thumbnail_image && resource.org_uuid
    ? getResourceThumbnailMediaDirectory(resource.org_uuid, resource.resource_uuid, resource.thumbnail_image)
    : null

  const formatDate = (dateStr: string) => {
    if (!dateStr) return ''
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric', month: 'long', day: 'numeric',
      })
    } catch {
      return dateStr
    }
  }

  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return null
    const units = ['B', 'KB', 'MB', 'GB']
    let size = bytes
    let unitIdx = 0
    while (size >= 1024 && unitIdx < units.length - 1) { size /= 1024; unitIdx++ }
    return `${size.toFixed(1)} ${units[unitIdx]}`
  }

  const relatedList = relatedResources?.resources?.filter(r => r.resource_uuid !== resourceuuid) || []

  return (
    <GeneralWrapperStyled>
      <div className="pb-4">
        <Breadcrumbs items={[
          { label: t('library.library', 'Library'), href: getUriWithOrg(orgslug, '/library'), icon: <BookCopy size={14} /> },
          { label: resource.title },
        ]} />
      </div>

      <div className="flex flex-col md:flex-row gap-8">
        <div className="w-full md:w-2/3 space-y-6">
          {coverUrl ? (
            <div className="rounded-xl overflow-hidden ring-1 ring-inset ring-black/10 shadow-xl">
              <img
                src={coverUrl}
                alt={resource.title}
                className="w-full h-[200px] md:h-[400px] object-cover"
                fetchPriority="high"
              />
            </div>
          ) : (
            <div className="rounded-xl ring-1 ring-inset ring-black/10 shadow-xl bg-gradient-to-br from-gray-50 to-gray-100 w-full h-[200px] md:h-[400px] flex items-center justify-center">
              <ResourceTypeIcon type={resource.resource_type} size={64} />
            </div>
          )}

          <div>
            <div className="flex items-center gap-3 mb-3">
              <ResourceTypeBadge type={resource.resource_type} />
              {resource.visibility === 'public' ? (
                <span className="inline-flex items-center gap-1 text-xs text-green-600 bg-green-50 px-2 py-1 rounded-full">
                  <Globe size={12} /> Public
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded-full">
                  <Lock size={12} /> Private
                </span>
              )}
            </div>
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">{resource.title}</h1>
            {resource.description && (
              <p className="text-gray-600 leading-relaxed whitespace-pre-line">{resource.description}</p>
            )}
          </div>

          {resource.content && (
            <div className="prose max-w-none">
              <div className="bg-white rounded-xl ring-1 ring-inset ring-gray-200 p-6">
                <h3 className="text-lg font-semibold mb-3">{t('resource.preview', 'Preview')}</h3>
                <div className="text-gray-700 leading-relaxed whitespace-pre-line">{resource.content}</div>
              </div>
            </div>
          )}

          {resource.embed_url && (
            <div className="rounded-xl overflow-hidden ring-1 ring-inset ring-black/10 shadow-xl aspect-video">
              <iframe
                src={resource.embed_url}
                className="w-full h-full"
                allowFullScreen
                title={resource.title}
              />
            </div>
          )}

          {resource.resource_type === 'video' && resource.url && (
            <div className="rounded-xl overflow-hidden ring-1 ring-inset ring-black/10 shadow-xl">
              <video src={resource.url} controls className="w-full" preload="metadata">
                <track kind="captions" />
              </video>
            </div>
          )}
        </div>

        <div className="w-full md:w-1/3 space-y-4">
          <div className="bg-white rounded-xl ring-1 ring-inset ring-gray-200 p-5 space-y-4">
            {resource.url && resource.resource_type !== 'video' && (
              <a
                href={resource.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 w-full py-2.5 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
              >
                <ExternalLink size={16} />
                {t('resource.openLink', 'Open Link')}
              </a>
            )}

            {resource.file_id && (
              <a
                href={resource.url || '#'}
                download
                className="flex items-center justify-center gap-2 w-full py-2.5 px-4 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
              >
                <Download size={16} />
                {t('resource.download', 'Download')}
                {resource.file_size && ` (${formatFileSize(resource.file_size)})`}
              </a>
            )}

            <div className="border-t border-gray-100 pt-4 space-y-3">
              {resource.file_format && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">{t('resource.format', 'Format')}</span>
                  <span className="font-medium text-gray-900 uppercase">{resource.file_format}</span>
                </div>
              )}
              {resource.file_size && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">{t('resource.fileSize', 'File size')}</span>
                  <span className="font-medium text-gray-900">{formatFileSize(resource.file_size)}</span>
                </div>
              )}
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">{t('resource.lastUpdated', 'Last updated')}</span>
                <span className="font-medium text-gray-900">{formatDate(resource.update_date) || formatDate(resource.creation_date)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">{t('resource.created', 'Created')}</span>
                <span className="font-medium text-gray-900">{formatDate(resource.creation_date)}</span>
              </div>
            </div>
          </div>

          {resource.author_username && (
            <div className="bg-white rounded-xl ring-1 ring-inset ring-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                {t('resource.author', 'Author')}
              </h3>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center overflow-hidden flex-shrink-0">
                  {resource.author_avatar ? (
                    <img src={resource.author_avatar} alt="" className="w-full h-full object-cover" />
                  ) : (
                    <User size={20} className="text-gray-500" />
                  )}
                </div>
                <div>
                  <p className="font-medium text-gray-900">
                    {resource.author_first_name && resource.author_last_name
                      ? `${resource.author_first_name} ${resource.author_last_name}`
                      : resource.author_username}
                  </p>
                  <p className="text-sm text-gray-500">@{resource.author_username}</p>
                </div>
              </div>
            </div>
          )}

          {resource.community_name && (
            <div className="bg-white rounded-xl ring-1 ring-inset ring-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                {t('resource.community', 'Community')}
              </h3>
              <Link
                href={getUriWithOrg(orgslug, `/community/${resource.community_uuid}`)}
                className="flex items-center gap-3 group"
              >
                <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center overflow-hidden flex-shrink-0">
                  {resource.community_thumbnail ? (
                    <img src={resource.community_thumbnail} alt="" className="w-full h-full object-cover" />
                  ) : (
                    <BookCopy size={20} className="text-gray-500" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 group-hover:text-blue-600 transition-colors truncate">
                    {resource.community_name}
                  </p>
                  <p className="text-sm text-gray-500">{t('resource.viewCommunity', 'View Community')}</p>
                </div>
                <ChevronRight size={16} className="text-gray-400 group-hover:text-blue-600 flex-shrink-0" />
              </Link>
            </div>
          )}
        </div>
      </div>

      {resource.community_name && !resource.user_has_access && (
        <div className="mt-8 p-6 bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl ring-1 ring-inset ring-amber-200">
          <div className="flex items-start gap-4">
            <div className="p-2 bg-amber-100 rounded-lg">
              <Crown size={24} className="text-amber-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-amber-900 mb-1">
                {resource.required_plan_name
                  ? `This resource requires the ${resource.required_plan_name} plan`
                  : 'This resource requires a membership'}
              </h3>
              <p className="text-amber-700 mb-4">
                Join the <strong>{resource.community_name}</strong> community and choose a plan to access this resource.
              </p>
              <div className="flex gap-3">
                <Link
                  href={getUriWithOrg(orgslug, `/community/${resource.community_uuid}`)}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors text-sm font-medium"
                >
                  <BookCopy size={16} />
                  View Community & Plans
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}

      {relatedList.length > 0 && (
        <div className="mt-12 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">
            {t('resource.relatedResources', 'Related Resources')}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {relatedList.slice(0, 6).map((r: any) => (
              <Link
                key={r.resource_uuid}
                href={getUriWithOrg(orgslug, `/resource/${r.resource_uuid}`)}
                className="group block bg-white rounded-xl ring-1 ring-inset ring-gray-200 hover:ring-blue-300 transition-all p-4"
              >
                <div className="flex items-start gap-3">
                  <ResourceTypeIcon type={r.resource_type} size={20} />
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-gray-900 group-hover:text-blue-600 transition-colors truncate">
                      {r.title}
                    </p>
                    {r.description && (
                      <p className="text-sm text-gray-500 mt-1 line-clamp-2">{r.description}</p>
                    )}
                    <p className="text-xs text-gray-400 mt-2">{formatDate(r.update_date || r.creation_date)}</p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </GeneralWrapperStyled>
  )
}

export default ResourceClient
