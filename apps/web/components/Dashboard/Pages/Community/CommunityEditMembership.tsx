'use client'
import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useCommunity, useCommunityDispatch } from '@components/Contexts/CommunityContext'
import { useLHSession } from '@components/Contexts/LHSessionContext'
import { updateCommunity } from '@services/communities/communities'
import toast from 'react-hot-toast'
import { Loader2, Info, Lock, Globe, CreditCard, EyeOff, ShieldCheck } from 'lucide-react'

const COMMUNITY_TYPE_OPTIONS = [
  {
    value: 'open',
    icon: Globe,
    title: 'Open Community',
    description: 'Anyone can view and join. Discussions and content are publicly visible.',
  },
  {
    value: 'paid',
    icon: CreditCard,
    title: 'Paid Community',
    description: 'Community is visible but joining requires a paid membership plan.',
  },
  {
    value: 'invite_only',
    icon: Lock,
    title: 'Invite Only',
    description: 'Community is visible but only invited users can join.',
  },
  {
    value: 'hidden',
    icon: EyeOff,
    title: 'Hidden Community',
    description: 'Community is not listed publicly. Only members with a direct link can access.',
  },
]

export function CommunityEditMembership() {
  const { t } = useTranslation()
  const communityState = useCommunity()
  const communityDispatch = useCommunityDispatch()
  const community = communityState?.community
  const session = useLHSession() as any
  const accessToken = session?.data?.tokens?.access_token
  const [saving, setSaving] = useState(false)
  const [selectedType, setSelectedType] = useState(community?.community_type || 'open')
  const [locked, setLocked] = useState(community?.locked ?? false)

  const handleSave = async () => {
    if (!community || !accessToken) return
    setSaving(true)
    try {
      await updateCommunity(community.community_uuid, { community_type: selectedType, locked }, accessToken)
      communityDispatch?.({ type: 'setCommunity', payload: { ...community, community_type: selectedType, locked } })
      toast.success(t('dashboard.courses.communities.settings.membership.toasts.saved') || 'Community type updated')
    } catch (err: any) {
      toast.error(err.message || t('dashboard.courses.communities.settings.membership.toasts.error') || 'Failed to update')
    } finally {
      setSaving(false)
    }
  }

  if (!community) return null

  return (
    <div className="mx-4 sm:mx-10">
      <div className="h-6"></div>
      <div className="bg-white rounded-xl shadow-xs px-4 py-4">
        <div className="flex flex-col bg-gray-50 -space-y-1 px-3 sm:px-5 py-3 rounded-md mb-6">
          <h1 className="font-bold text-lg sm:text-xl text-gray-800">
            {t('dashboard.courses.communities.settings.membership.title') || 'Membership'}
          </h1>
          <h2 className="text-gray-500 text-xs sm:text-sm">
            {t('dashboard.courses.communities.settings.membership.subtitle') || 'Configure how users access your community'}
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
          {COMMUNITY_TYPE_OPTIONS.map((opt) => {
            const Icon = opt.icon
            const isSelected = selectedType === opt.value
            return (
              <button
                key={opt.value}
                onClick={() => setSelectedType(opt.value)}
                className={`flex items-start gap-3 p-4 rounded-lg border-2 text-left transition-all ${
                  isSelected
                    ? 'border-gray-900 bg-gray-50'
                    : 'border-gray-200 hover:border-gray-300 bg-white'
                }`}
              >
                <div className={`p-2 rounded-lg ${isSelected ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-500'}`}>
                  <Icon size={18} />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-gray-900">{opt.title}</h3>
                  <p className="text-xs text-gray-500 mt-0.5">{opt.description}</p>
                </div>
              </button>
            )
          })}
        </div>

        {selectedType === 'paid' && (
          <div className="flex items-start gap-2 p-3 bg-blue-50 border border-blue-100 rounded-lg text-sm text-blue-700 mb-6">
            <Info size={16} className="shrink-0 mt-0.5" />
            <span>
              {t('dashboard.courses.communities.settings.membership.paid_hint') ||
                'Paid communities require at least one active membership plan. Go to the Plans tab to create pricing tiers.'}
            </span>
          </div>
        )}

        {selectedType === 'invite_only' && (
          <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-100 rounded-lg text-sm text-amber-700 mb-6">
            <Info size={16} className="shrink-0 mt-0.5" />
            <span>
              {t('dashboard.courses.communities.settings.membership.invite_hint') ||
                'Invite-only communities require an admin to manually add members or provide an invite link.'}
            </span>
          </div>
        )}

        <div className="border-t border-gray-100 pt-4 mb-6">
          <div className="flex items-center justify-between px-1">
            <div className="flex items-start gap-3">
              <div className={`p-2 rounded-lg ${locked ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-500'}`}>
                <ShieldCheck size={18} />
              </div>
              <div>
                <h3 className="font-semibold text-sm text-gray-900">
                  {t('dashboard.courses.communities.settings.membership.lock_title') || 'Lock Community'}
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  {t('dashboard.courses.communities.settings.membership.lock_description') ||
                    'When locked, only members with an active plan can access this community and its resources.'}
                </p>
              </div>
            </div>
            <button
              onClick={() => setLocked(!locked)}
              className={`relative w-11 h-6 rounded-full transition-colors ${
                locked ? 'bg-amber-500' : 'bg-gray-300'
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                  locked ? 'translate-x-5' : ''
                }`}
              />
            </button>
          </div>
        </div>

        <div className="flex justify-end pt-2 border-t border-gray-100">
          <button
            onClick={handleSave}
            disabled={saving || (selectedType === community.community_type && locked === community.locked)}
            className="px-6 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {saving && <Loader2 size={14} className="animate-spin" />}
            {t('common.save') || 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default CommunityEditMembership
