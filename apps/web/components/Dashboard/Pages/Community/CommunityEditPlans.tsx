'use client'
import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useLHSession } from '@components/Contexts/LHSessionContext'
import { useOrg } from '@components/Contexts/OrgContext'
import { useCommunity } from '@components/Contexts/CommunityContext'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/lib/query/keys'
import { getAPIUrl } from '@services/config/config'
import { RequestBodyWithAuthHeader } from '@services/utils/ts/requests'
import { DollarSign, Trash2, Pencil, Plus, Loader2, Copy, GripVertical } from 'lucide-react'
import toast from 'react-hot-toast'
import ConfirmationModal from '@components/Objects/StyledElements/ConfirmationModal/ConfirmationModal'
import Modal from '@components/Objects/StyledElements/Modal/Modal'
import {
  getAllMembershipPlansAdmin,
  createMembershipPlan,
  updateMembershipPlan,
  deleteMembershipPlan,
  duplicateMembershipPlan,
  reorderMembershipPlans,
  MembershipPlan,
  MembershipPlanCreate,
  MembershipPlanUpdate,
} from '@services/communities/membership'
import { getUserGroups } from '@services/usergroups/usergroups'
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd'

const CommunityEditPlans: React.FC = () => {
  const { t } = useTranslation()
  const session = useLHSession() as any
  const org = useOrg() as any
  const communityState = useCommunity()
  const community = communityState?.community
  const accessToken = session?.data?.tokens?.access_token
  const queryClient = useQueryClient()

  const { data: plans, isLoading } = useQuery({
    queryKey: queryKeys.community.plans(community?.community_uuid ?? ''),
    queryFn: () => getAllMembershipPlansAdmin(community!.community_uuid, accessToken),
    enabled: !!(community?.community_uuid && accessToken),
    staleTime: 30_000,
  })

  const { data: usergroups } = useQuery({
    queryKey: queryKeys.usergroups.list(org?.id),
    queryFn: () => getUserGroups(org.id, accessToken),
    enabled: !!(org?.id && accessToken),
    staleTime: 60_000,
  })

  const [planModal, setPlanModal] = useState(false)
  const [editingPlan, setEditingPlan] = useState<MembershipPlan | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (!community) return null

  const handleCreate = async (data: MembershipPlanCreate) => {
    setSubmitting(true)
    try {
      await createMembershipPlan(community.community_uuid, data, accessToken)
      toast.success(t('dashboard.courses.communities.settings.plans.toasts.create_success'))
      queryClient.invalidateQueries({ queryKey: queryKeys.community.plans(community.community_uuid) })
      setPlanModal(false)
    } catch (err: any) {
      toast.error(err.message || t('dashboard.courses.communities.settings.plans.toasts.create_error'))
    } finally {
      setSubmitting(false)
    }
  }

  const handleUpdate = async (planUuid: string, data: MembershipPlanUpdate) => {
    setSubmitting(true)
    try {
      await updateMembershipPlan(planUuid, data, accessToken)
      toast.success(t('dashboard.courses.communities.settings.plans.toasts.update_success'))
      queryClient.invalidateQueries({ queryKey: queryKeys.community.plans(community.community_uuid) })
      setPlanModal(false)
      setEditingPlan(null)
    } catch (err: any) {
      toast.error(err.message || t('dashboard.courses.communities.settings.plans.toasts.update_error'))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (planUuid: string) => {
    try {
      await deleteMembershipPlan(planUuid, accessToken)
      toast.success(t('dashboard.courses.communities.settings.plans.toasts.delete_success'))
      queryClient.invalidateQueries({ queryKey: queryKeys.community.plans(community.community_uuid) })
    } catch (err: any) {
      toast.error(err.message || t('dashboard.courses.communities.settings.plans.toasts.delete_error'))
    }
  }

  const handleDuplicate = async (planUuid: string) => {
    try {
      await duplicateMembershipPlan(planUuid, accessToken)
      toast.success(t('dashboard.courses.communities.settings.plans.toasts.duplicate_success') || 'Plan duplicated')
      queryClient.invalidateQueries({ queryKey: queryKeys.community.plans(community.community_uuid) })
    } catch (err: any) {
      toast.error(err.message || 'Failed to duplicate plan')
    }
  }

  const handleDragEnd = async (result: any) => {
    const { source, destination } = result
    if (!destination || source.index === destination.index) return

    const sorted = [...(plans || [])]
    const [moved] = sorted.splice(source.index, 1)
    sorted.splice(destination.index, 0, moved)
    const planUuids = sorted.map(p => p.plan_uuid)

    try {
      await reorderMembershipPlans(community.community_uuid, planUuids, accessToken)
      queryClient.invalidateQueries({ queryKey: queryKeys.community.plans(community.community_uuid) })
    } catch (err: any) {
      toast.error(err.message || 'Failed to reorder plans')
    }
  }

  const openCreateModal = () => {
    setEditingPlan(null)
    setPlanModal(true)
  }

  const openEditModal = (plan: MembershipPlan) => {
    setEditingPlan(plan)
    setPlanModal(true)
  }

  return (
    <div>
      <div className="h-6"></div>
      <div className="mx-4 sm:mx-10 bg-white rounded-xl shadow-xs px-4 py-4">
        <div className="flex flex-col bg-gray-50 -space-y-1 px-3 sm:px-5 py-3 rounded-md mb-3">
          <h1 className="font-bold text-lg sm:text-xl text-gray-800">
            {t('dashboard.courses.communities.settings.plans.title')}
          </h1>
          <h2 className="text-gray-500 text-xs sm:text-sm">
            {t('dashboard.courses.communities.settings.plans.subtitle')}
          </h2>
        </div>

        {isLoading ? (
          <div className="space-y-2 animate-pulse">
            {[1, 2].map((i) => (
              <div key={i} className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
                <div className="h-4 bg-gray-200 rounded w-1/3" />
                <div className="h-7 bg-gray-200 rounded w-24" />
              </div>
            ))}
          </div>
        ) : plans && plans.length > 0 ? (
          <DragDropContext onDragEnd={handleDragEnd}>
            <Droppable droppableId="plans">
              {(provided) => (
                <div ref={provided.innerRef} {...provided.droppableProps} className="space-y-2">
                  {plans.map((plan: MembershipPlan, index: number) => (
                    <Draggable key={plan.plan_uuid} draggableId={plan.plan_uuid} index={index}>
                      {(provided, snapshot) => (
                        <div
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          className={`flex items-center gap-3 px-4 py-3 bg-white border border-gray-100 rounded-lg text-sm ${snapshot.isDragging ? 'shadow-lg opacity-50' : ''}`}
                        >
                          <button {...provided.dragHandleProps} className="cursor-grab text-gray-400 hover:text-gray-600" aria-label="Reorder">
                            <GripVertical size={16} />
                          </button>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-gray-900 truncate">{plan.name}</span>
                              {plan.status !== 'active' && (
                                <span className="text-xs bg-gray-200 text-gray-500 px-2 py-0.5 rounded-full capitalize">
                                  {plan.status}
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-3 text-xs text-gray-500 mt-0.5">
                              <span>
                                {plan.price === 0
                                  ? t('dashboard.courses.communities.settings.plans.free_plan')
                                  : `${plan.price} ${plan.currency.toUpperCase()}`}
                              </span>
                              <span className="capitalize">{plan.interval}</span>
                              {plan.is_free && <span className="text-green-600">Free</span>}
                            </div>
                          </div>
                          <div className="flex items-center gap-1.5 shrink-0">
                            <button
                              onClick={() => handleDuplicate(plan.plan_uuid)}
                              className="p-1.5 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
                              title="Duplicate"
                            >
                              <Copy className="w-4 h-4 text-gray-500" />
                            </button>
                            <button
                              onClick={() => openEditModal(plan)}
                              className="p-1.5 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
                              title={t('dashboard.courses.communities.settings.plans.edit_plan')}
                            >
                              <Pencil className="w-4 h-4 text-gray-600" />
                            </button>
                            <ConfirmationModal
                              confirmationButtonText={t('dashboard.courses.communities.settings.plans.confirm_delete_button')}
                              confirmationMessage={t('dashboard.courses.communities.settings.plans.confirm_delete_message')}
                              dialogTitle={t('dashboard.courses.communities.settings.plans.confirm_delete_title')}
                              dialogTrigger={
                                <button
                                  className="p-1.5 bg-rose-50 hover:bg-rose-100 rounded-md transition-colors"
                                  title={t('dashboard.courses.communities.settings.plans.delete_plan')}
                                >
                                  <Trash2 className="w-4 h-4 text-rose-600" />
                                </button>
                              }
                              functionToExecute={() => handleDelete(plan.plan_uuid)}
                              status="warning"
                            />
                          </div>
                        </div>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </DragDropContext>
        ) : (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <DollarSign className="w-12 h-12 text-gray-300 mb-3" />
            <h3 className="text-lg font-semibold text-gray-600 mb-1">
              {t('dashboard.courses.communities.settings.plans.no_plans')}
            </h3>
            <p className="text-sm text-gray-400 max-w-md">
              {t('dashboard.courses.communities.settings.plans.no_plans_description')}
            </p>
          </div>
        )}

        <div className="flex flex-row-reverse mt-4 mr-2">
          <button
            onClick={openCreateModal}
            className="flex space-x-2 hover:cursor-pointer p-2 px-4 bg-black rounded-md font-bold items-center text-xs sm:text-sm text-white hover:bg-black/90 transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>{t('dashboard.courses.communities.settings.plans.create_plan')}</span>
          </button>
        </div>
      </div>

      <PlanFormModal
        isOpen={planModal}
        onClose={() => { setPlanModal(false); setEditingPlan(null) }}
        onSubmit={editingPlan ? (data) => handleUpdate(editingPlan.plan_uuid, data) : handleCreate}
        editingPlan={editingPlan}
        usergroups={usergroups?.data || usergroups || []}
        submitting={submitting}
      />
    </div>
  )
}

interface PlanFormModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: any) => Promise<void>
  editingPlan: MembershipPlan | null
  usergroups: any[]
  submitting: boolean
}

function PlanFormModal({ isOpen, onClose, onSubmit, editingPlan, usergroups, submitting }: PlanFormModalProps) {
  const { t } = useTranslation()
  const [name, setName] = useState(editingPlan?.name || '')
  const [description, setDescription] = useState(editingPlan?.description || '')
  const [price, setPrice] = useState(editingPlan?.price ?? 0)
  const [currency, setCurrency] = useState(editingPlan?.currency || 'usd')
  const [interval, setInterval] = useState(editingPlan?.interval || 'month')
  const [maxMembers, setMaxMembers] = useState(editingPlan?.max_members ?? 0)
  const [status, setStatus] = useState(editingPlan?.status || 'draft')
  const [usergroupId, setUsergroupId] = useState<number | null>(editingPlan?.usergroup_id ?? null)
  const [features, setFeatures] = useState(
    editingPlan?.features ? JSON.stringify(editingPlan.features, null, 2) : ''
  )

  React.useEffect(() => {
    if (editingPlan) {
      setName(editingPlan.name)
      setDescription(editingPlan.description || '')
      setPrice(editingPlan.price)
      setCurrency(editingPlan.currency || 'usd')
      setInterval(editingPlan.interval || 'monthly')
      setMaxMembers(editingPlan.max_members ?? 0)
      setStatus(editingPlan.status || 'draft')
      setUsergroupId(editingPlan.usergroup_id ?? null)
      setFeatures(editingPlan.features ? JSON.stringify(editingPlan.features, null, 2) : '')
    } else {
      setName('')
      setDescription('')
      setPrice(0)
      setCurrency('usd')
      setInterval('monthly')
      setMaxMembers(0)
      setStatus('draft')
      setUsergroupId(null)
      setFeatures('')
    }
  }, [editingPlan, isOpen])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return

    let parsedFeatures: Record<string, any> | null = null
    if (features.trim()) {
      try {
        parsedFeatures = JSON.parse(features)
      } catch {
        toast.error(t('common.invalid_json'))
        return
      }
    }

    const data: MembershipPlanCreate = {
      name: name.trim(),
      description: description.trim() || null,
      price,
      currency,
      interval,
      max_members: maxMembers,
      status,
      usergroup_id: usergroupId,
      features: parsedFeatures,
    }

    await onSubmit(data)
  }

  const intervalOptions = [
    { value: 'monthly', label: t('dashboard.courses.communities.settings.plans.interval_monthly') },
    { value: 'yearly', label: t('dashboard.courses.communities.settings.plans.interval_yearly') },
    { value: 'one_time', label: t('dashboard.courses.communities.settings.plans.interval_one_time') },
  ]

  return (
    <Modal
      isDialogOpen={isOpen}
      onOpenChange={onClose}
      minHeight="no-min"
      minWidth="lg"
      dialogContent={
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('dashboard.courses.communities.settings.plans.plan_name')} *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-black/20 focus:border-black"
              required
              placeholder="e.g. Premium Member"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('dashboard.courses.communities.settings.plans.plan_description')}
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-black/20 focus:border-black min-h-[60px]"
              placeholder="Optional description"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('dashboard.courses.communities.settings.plans.price')}
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={price}
                onChange={(e) => setPrice(parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-black/20 focus:border-black"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('dashboard.courses.communities.settings.plans.currency')}
              </label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-black/20 focus:border-black bg-white"
              >
                <option value="usd">USD</option>
                <option value="eur">EUR</option>
                <option value="gbp">GBP</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('dashboard.courses.communities.settings.plans.interval')}
              </label>
              <select
                value={interval}
                onChange={(e) => setInterval(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-black/20 focus:border-black bg-white"
              >
                {intervalOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('dashboard.courses.communities.settings.plans.max_members')}
              </label>
              <input
                type="number"
                min="0"
                value={maxMembers}
                onChange={(e) => setMaxMembers(parseInt(e.target.value) || 0)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-black/20 focus:border-black"
              />
              <p className="text-xs text-gray-400 mt-1">
                {t('dashboard.courses.communities.settings.plans.max_members_hint')}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('dashboard.courses.communities.settings.plans.usergroup')}
              </label>
              <select
                value={usergroupId ?? ''}
                onChange={(e) => setUsergroupId(e.target.value ? parseInt(e.target.value) : null)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-black/20 focus:border-black bg-white"
              >
                <option value="">{t('dashboard.courses.communities.settings.plans.select_usergroup')}</option>
                {(usergroups || []).map((ug: any) => (
                  <option key={ug.id} value={ug.id}>{ug.name}</option>
                ))}
              </select>
              <p className="text-xs text-gray-400 mt-1">
                {t('dashboard.courses.communities.settings.plans.usergroup_hint')}
              </p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('dashboard.courses.communities.settings.plans.features')}
            </label>
            <textarea
              value={features}
              onChange={(e) => setFeatures(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono focus:outline-none focus:ring-2 focus:ring-black/20 focus:border-black min-h-[80px]"
              placeholder='{"downloads": true, "max_projects": 10}'
            />
            <p className="text-xs text-gray-400 mt-1">
              {t('dashboard.courses.communities.settings.plans.features_hint')}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('dashboard.courses.communities.settings.plans.status') || 'Status'}
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-black/20 focus:border-black bg-white"
            >
              <option value="draft">{t('dashboard.courses.communities.settings.plans.status_draft') || 'Draft'}</option>
              <option value="active">{t('dashboard.courses.communities.settings.plans.status_active') || 'Active'}</option>
              <option value="archived">{t('dashboard.courses.communities.settings.plans.status_archived') || 'Archived'}</option>
            </select>
          </div>

          <div className="flex space-x-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              disabled={submitting || !name.trim()}
              className="flex-1 px-4 py-2 bg-black text-white rounded-md text-sm font-medium hover:bg-black/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <span className="flex items-center justify-center space-x-2">
                  <Loader2 size={14} className="animate-spin" />
                  <span>{t('common.saving')}</span>
                </span>
              ) : (
                editingPlan ? t('common.save_changes') : t('dashboard.courses.communities.settings.plans.create_plan')
              )}
            </button>
          </div>
        </form>
      }
      dialogTitle={editingPlan ? t('dashboard.courses.communities.settings.plans.edit_plan') : t('dashboard.courses.communities.settings.plans.create_plan')}
      dialogDescription=""
    />
  )
}

export default CommunityEditPlans
