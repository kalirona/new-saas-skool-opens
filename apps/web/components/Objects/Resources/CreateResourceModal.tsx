'use client'

import { Loader2, AlertCircle, Check, FileText, Video, Link, Download } from 'lucide-react'

import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'

import { useLHSession } from '@components/Contexts/LHSessionContext'
import {
  createResource,
  ResourceCreate,
  ResourceType,
} from '@services/resources/resources'
import Modal from '@components/Objects/StyledElements/Modal/Modal'

interface CreateResourceModalProps {
  isOpen: boolean
  onClose: () => void
  orgId: number
  onCreated?: () => void
}

const RESOURCE_TYPE_OPTIONS: { value: ResourceType; icon: React.ReactNode; label: string }[] = [
  { value: 'pdf', icon: <FileText size={16} className="text-red-500" />, label: 'PDF' },
  { value: 'video', icon: <Video size={16} className="text-blue-500" />, label: 'Video' },
  { value: 'link', icon: <Link size={16} className="text-indigo-500" />, label: 'Link' },
  { value: 'download', icon: <Download size={16} className="text-green-500" />, label: 'Download' },
  { value: 'template', icon: <FileText size={16} className="text-amber-500" />, label: 'Template' },
]

export function CreateResourceModal({ isOpen, onClose, orgId, onCreated }: CreateResourceModalProps) {
  const { t } = useTranslation()
  const session = useLHSession() as any
  const accessToken = session?.data?.tokens?.access_token
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [resourceType, setResourceType] = useState<ResourceType>('link')
  const [url, setUrl] = useState('')
  const [visibility, setVisibility] = useState('private')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) {
      setError('Title is required')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      const data: ResourceCreate = {
        title: title.trim(),
        description: description.trim() || null,
        resource_type: resourceType,
        url: url.trim() || null,
        visibility,
      }

      await createResource(orgId, data, accessToken)
      toast.success('Resource created')
      setTitle('')
      setDescription('')
      setUrl('')
      setResourceType('link')
      setVisibility('private')
      onCreated?.()
      onClose()
    } catch (err: any) {
      const message = err?.message || 'Failed to create resource'
      setError(message)
      toast.error(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Modal
      isDialogOpen={isOpen}
      onOpenChange={(open) => {
        if (!open) {
          setTitle('')
          setDescription('')
          setUrl('')
          setResourceType('link')
          setVisibility('private')
          setError(null)
          onClose()
        }
      }}
      dialogTitle="Create Resource"
      dialogDescription="Add a new resource to your library"
      minWidth="md"
      dialogContent={
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Resource Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
              {RESOURCE_TYPE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setResourceType(opt.value)}
                  className={`flex flex-col items-center gap-1 p-3 rounded-lg border transition-all ${
                    resourceType === opt.value
                      ? 'border-gray-900 bg-gray-50'
                      : 'border-gray-200 hover:border-gray-300 bg-white'
                  }`}
                >
                  {opt.icon}
                  <span className={`text-[10px] font-medium ${
                    resourceType === opt.value ? 'text-gray-900' : 'text-gray-500'
                  }`}>
                    {opt.label}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Title */}
          <div>
            <label htmlFor="res-title" className="block text-sm font-medium text-gray-700 mb-1">
              Title *
            </label>
            <input
              id="res-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter resource title"
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-sm"
            />
          </div>

          {/* URL (for links and videos) */}
          {(resourceType === 'link' || resourceType === 'video') && (
            <div>
              <label htmlFor="res-url" className="block text-sm font-medium text-gray-700 mb-1">
                {resourceType === 'link' ? 'URL' : 'Video URL'}
              </label>
              <input
                id="res-url"
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder={resourceType === 'link' ? 'https://example.com/doc' : 'https://youtube.com/watch?v=...'}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-sm"
              />
            </div>
          )}

          {/* Description */}
          <div>
            <label htmlFor="res-desc" className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              id="res-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description"
              rows={3}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-sm resize-none"
            />
          </div>

          {/* Visibility */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Visibility</label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setVisibility('private')}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-all text-sm ${
                  visibility === 'private'
                    ? 'border-gray-900 bg-gray-50 font-medium'
                    : 'border-gray-200 hover:border-gray-300 bg-white'
                }`}
              >
                Private
                {visibility === 'private' && <Check size={14} className="text-gray-900" />}
              </button>
              <button
                type="button"
                onClick={() => setVisibility('public')}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-all text-sm ${
                  visibility === 'public'
                    ? 'border-gray-900 bg-gray-50 font-medium'
                    : 'border-gray-200 hover:border-gray-300 bg-white'
                }`}
              >
                Public
                {visibility === 'public' && <Check size={14} className="text-gray-900" />}
              </button>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-100 rounded-lg text-red-700 text-sm">
              <AlertCircle size={16} className="flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !title.trim()}
              className="px-4 py-2 text-sm font-medium text-white bg-neutral-900 hover:bg-neutral-800 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isSubmitting && <Loader2 size={16} className="animate-spin" />}
              Create
            </button>
          </div>
        </form>
      }
    />
  )
}

export default CreateResourceModal
