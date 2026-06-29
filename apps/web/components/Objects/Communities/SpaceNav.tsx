'use client'
import React from 'react'
import { useTranslation } from 'react-i18next'
import { Hash, Loader2 } from 'lucide-react'
import { Space } from '@services/communities/spaces'

interface SpaceNavProps {
  spaces: Space[]
  selectedSpaceId: number | null
  onSelectSpace: (spaceId: number | null) => void
  isLoading?: boolean
}

export function SpaceNav({
  spaces,
  selectedSpaceId,
  onSelectSpace,
  isLoading = false,
}: SpaceNavProps) {
  const { t } = useTranslation()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-3">
        <Loader2 size={16} className="animate-spin text-gray-400" />
      </div>
    )
  }

  if (spaces.length === 0) {
    return null
  }

  return (
    <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none">
      <button
        onClick={() => onSelectSpace(null)}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors ${
          selectedSpaceId === null
            ? 'bg-neutral-900 text-white'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        }`}
      >
        <Hash size={12} />
        {t('communities.all_discussions')}
      </button>
      {spaces.map((space) => (
        <button
          key={space.id}
          onClick={() => onSelectSpace(space.id)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors ${
            selectedSpaceId === space.id
              ? 'bg-neutral-900 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          {space.icon || <Hash size={12} />}
          <span>{space.name}</span>
        </button>
      ))}
    </div>
  )
}

export default SpaceNav
