'use client'

import { FileText, Filter, Folder, LinkIcon, Plus, Search, X, Video, Download } from 'lucide-react'

import React, { useState, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import EmptyState from '@components/shared/EmptyState'

import { useOrg } from '@components/Contexts/OrgContext'
import { useLHSession } from '@components/Contexts/LHSessionContext'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  getResources,
  deleteResource,
  Resource,
  ResourceType,
  ResourceSortBy,
} from '@services/resources/resources'
import { getTags, Tag } from '@services/resources/tags'
import { ResourceCard } from '@components/Objects/Resources/ResourceCard'
import { CreateResourceModal } from '@components/Objects/Resources/CreateResourceModal'
import toast from 'react-hot-toast'
import { searchMatchesAny } from '@/lib/search/normalize'

const TYPE_FILTERS: { value: ResourceType | 'all'; labelKey: string; icon: React.ReactNode }[] = [
  { value: 'all', labelKey: 'dashboard.resources.filter_all', icon: null },
  { value: 'pdf', labelKey: 'dashboard.resources.filter_pdf', icon: <FileText size={14} className="text-red-500" /> },
  { value: 'video', labelKey: 'dashboard.resources.filter_video', icon: <Video size={14} className="text-blue-500" /> },
  { value: 'link', labelKey: 'dashboard.resources.filter_link', icon: <LinkIcon size={14} className="text-indigo-500" /> },
  { value: 'download', labelKey: 'dashboard.resources.filter_download', icon: <Download size={14} className="text-green-500" /> },
  { value: 'template', labelKey: 'dashboard.resources.filter_template', icon: <FileText size={14} className="text-amber-500" /> },
]

export default function ResourcesHome() {
  const { t } = useTranslation()
  const org = useOrg() as any
  const session = useLHSession() as any
  const queryClient = useQueryClient()
  const accessToken = session?.data?.tokens?.access_token
  const orgId = org?.id

  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState<ResourceType | 'all'>('all')
  const [sortBy, setSortBy] = useState<ResourceSortBy>('newest')

  const { data: listData, isLoading } = useQuery({
    queryKey: ['resources', orgId, typeFilter, sortBy],
    queryFn: () => getResources(orgId, {
      resource_type: typeFilter === 'all' ? null : typeFilter,
      sort_by: sortBy,
      limit: 100,
    }, accessToken),
    enabled: !!orgId && !!accessToken,
    staleTime: 30_000,
  })

  const { data: tags = [] } = useQuery<Tag[]>({
    queryKey: ['resources', orgId, 'tags'],
    queryFn: () => getTags(orgId, accessToken),
    enabled: !!orgId && !!accessToken,
    staleTime: 60_000,
  })

  const resources = listData?.resources || []

  const filtered = useMemo(() => {
    if (!searchQuery.trim()) return resources
    return resources.filter((r) =>
      searchMatchesAny([r.title, r.description, r.url], searchQuery)
    )
  }, [resources, searchQuery])

  const confirmDelete = async (resource: Resource) => {
    if (!window.confirm(`Delete "${resource.title}"? This action cannot be undone.`)) return
    try {
      await deleteResource(resource.resource_uuid, accessToken)
      toast.success('Resource deleted')
      queryClient.invalidateQueries({ queryKey: ['resources', orgId] })
    } catch (err: any) {
      toast.error(err?.message || t('dashboard.resources.delete_error'))
    }
  }

  const refetch = () => {
    queryClient.invalidateQueries({ queryKey: ['resources', orgId] })
  }

  return (
    <div className="h-full w-full bg-background">
      <div className="px-4 sm:px-10 pt-8 pb-10">
        <div className="space-y-6 max-w-[1600px] mx-auto w-full">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {t('dashboard.resources.title') || 'Resources'}
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                {t('dashboard.resources.subtitle') || 'Manage your learning resources'}
              </p>
            </div>
            <button
              onClick={() => setIsCreateOpen(true)}
              className="flex items-center gap-2 px-4 py-2.5 bg-neutral-900 hover:bg-neutral-800 text-white rounded-lg transition-colors text-sm font-medium"
            >
              <Plus size={18} />
              {t('dashboard.resources.new_resource')}
            </button>
          </div>

          {/* Search + Filter Bar */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder={t('dashboard.resources.search_placeholder')}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-9 py-2.5 text-sm bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-300 transition-all nice-shadow"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <X size={14} />
                </button>
              )}
            </div>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as ResourceSortBy)}
              className="px-3 py-2.5 text-sm bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 nice-shadow"
            >
              <option value="newest">{t('dashboard.resources.sort_newest')}</option>
              <option value="oldest">{t('dashboard.resources.sort_oldest')}</option>
              <option value="title">{t('dashboard.resources.sort_title')}</option>
            </select>
          </div>

          {/* Type Filter Pills */}
          <div className="flex items-center gap-2 flex-wrap">
            {TYPE_FILTERS.map((f) => (
              <button
                key={f.value}
                onClick={() => setTypeFilter(f.value)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                  typeFilter === f.value
                    ? 'bg-neutral-900 text-white'
                    : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50 nice-shadow'
                }`}
              >
                {f.icon}
                {t(f.labelKey)}
              </button>
            ))}
          </div>

          {/* Tags Row */}
          {tags.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap">
              <Filter size={14} className="text-gray-400" />
              {tags.map((tag) => (
                <span
                  key={tag.id}
                  className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium"
                  style={{
                    backgroundColor: tag.color ? `${tag.color}20` : '#f3f4f6',
                    color: tag.color || '#374151',
                  }}
                >
                  {tag.name}
                </span>
              ))}
            </div>
          )}

          {/* Count */}
          <p className="text-xs text-gray-400">
            {t('dashboard.resources.count', { count: filtered.length })}
            {typeFilter !== 'all' && ` · ${t(TYPE_FILTERS.find((f) => f.value === typeFilter)?.labelKey || '')}`}
          </p>

          {/* Grid */}
          {isLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="bg-white rounded-xl nice-shadow overflow-hidden animate-pulse">
                  <div className="aspect-video bg-gray-100" />
                  <div className="p-3.5 space-y-2">
                    <div className="h-4 bg-gray-100 rounded w-3/4" />
                    <div className="h-3 bg-gray-100 rounded w-full" />
                  </div>
                </div>
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <EmptyState
              icon={<Folder size={32} className="text-gray-400" />}
              title={searchQuery ? t('dashboard.resources.no_search_results') : t('dashboard.resources.no_resources')}
              description={searchQuery ? t('dashboard.resources.no_search_results_description') : t('dashboard.resources.no_resources_description')}
              action={!searchQuery ? (
                <button
                  onClick={() => setIsCreateOpen(true)}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-neutral-900 hover:bg-neutral-800 text-white rounded-lg transition-colors text-sm font-medium"
                >
                  <Plus size={16} />
                  {t('dashboard.resources.new_resource')}
                </button>
              ) : undefined}
            />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {filtered.map((resource) => (
                <ResourceCard
                  key={resource.resource_uuid}
                  resource={resource}
                  onDelete={confirmDelete}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      <CreateResourceModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        orgId={orgId}
        onCreated={refetch}
      />
    </div>
  )
}
