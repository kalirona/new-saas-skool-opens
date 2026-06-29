'use client'

import { FileText, Video, Link, Download, Globe, Lock, Trash2, Pencil } from 'lucide-react'

import React from 'react'

import { Resource, ResourceType } from '@services/resources/resources'

interface ResourceCardProps {
  resource: Resource
  onEdit?: (resource: Resource) => void
  onDelete?: (resource: Resource) => void
}

function ResourceTypeIcon({ type, size = 20 }: { type: ResourceType; size?: number }) {
  switch (type) {
    case 'pdf':
      return <FileText size={size} className="text-red-500" />
    case 'video':
      return <Video size={size} className="text-blue-500" />
    case 'link':
      return <Link size={size} className="text-indigo-500" />
    case 'download':
      return <Download size={size} className="text-green-500" />
    case 'template':
      return <FileText size={size} className="text-amber-500" />
  }
}

function ResourceTypeBadge({ type }: { type: ResourceType }) {
  const labels: Record<ResourceType, string> = {
    pdf: 'PDF',
    video: 'Video',
    link: 'Link',
    download: 'Download',
    template: 'Template',
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-gray-100 text-gray-600 uppercase tracking-wide">
      <ResourceTypeIcon type={type} size={12} />
      {labels[type]}
    </span>
  )
}

export function ResourceCard({ resource, onEdit, onDelete }: ResourceCardProps) {
  return (
    <div className="group relative bg-white rounded-xl nice-shadow hover:shadow-md transition-all duration-200 border border-gray-100 hover:border-gray-200 overflow-hidden">
      {/* Thumbnail */}
      <div className="aspect-video bg-gray-50 relative overflow-hidden">
        <div className="w-full h-full flex items-center justify-center">
          <ResourceTypeIcon type={resource.resource_type} size={40} />
        </div>
        {/* Type badge overlay */}
        <div className="absolute top-2 left-2">
          <ResourceTypeBadge type={resource.resource_type} />
        </div>
      </div>

      {/* Content */}
      <div className="p-3.5">
        {/* Visibility + Actions row */}
        <div className="flex items-center justify-between mb-1.5">
          {resource.visibility === 'public' ? (
            <span className="inline-flex items-center gap-1 text-[10px] font-medium text-green-600">
              <Globe size={12} />
              Public
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-[10px] font-medium text-amber-600">
              <Lock size={12} />
              Private
            </span>
          )}
          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {onEdit && (
              <button
                onClick={(e) => { e.stopPropagation(); onEdit(resource) }}
                className="p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
                title="Edit"
              >
                <Pencil size={12} />
              </button>
            )}
            {onDelete && (
              <button
                onClick={(e) => { e.stopPropagation(); onDelete(resource) }}
                className="p-1 rounded hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors"
                title="Delete"
              >
                <Trash2 size={12} />
              </button>
            )}
          </div>
        </div>
        <h3 className="text-sm font-semibold text-gray-900 truncate group-hover:text-indigo-600 transition-colors">
          {resource.title}
        </h3>
        {resource.description && (
          <p className="text-xs text-gray-500 mt-1 line-clamp-2 leading-relaxed">
            {resource.description}
          </p>
        )}
        {resource.url && resource.resource_type === 'link' && (
          <p className="text-[10px] text-gray-400 mt-1.5 truncate">{resource.url}</p>
        )}
        {resource.file_size && (
          <p className="text-[10px] text-gray-400 mt-1.5">
            {(resource.file_size / 1024 / 1024).toFixed(1)} MB
          </p>
        )}
      </div>

    </div>
  )
}

export default ResourceCard
