'use client'
import { Calendar, Plus, Trash2, Clock, Video, MapPin, Loader2, ExternalLink } from 'lucide-react'
import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useOrg } from '@components/Contexts/OrgContext'
import { useLHSession } from '@components/Contexts/LHSessionContext'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/lib/query/keys'
import { getEvents, createEvent, deleteEvent, Event, EventCreate } from '@services/events/events'

import dayjs from 'dayjs'
import toast from 'react-hot-toast'
import ConfirmationModal from '@components/Objects/StyledElements/ConfirmationModal/ConfirmationModal'
import Modal from '@components/Objects/StyledElements/Modal/Modal'
import EmptyState from '@components/shared/EmptyState'

export default function CalendarClient() {
  const { t } = useTranslation()
  const org = useOrg() as any
  const session = useLHSession() as any
  const accessToken = session?.data?.tokens?.access_token
  const queryClient = useQueryClient()

  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.events.list(org?.id),
    queryFn: () => getEvents(org.id, { sort_by: 'date_asc', limit: 100 }, accessToken),
    enabled: !!(org?.id && accessToken),
    staleTime: 30_000,
  })

  const events = data?.events || []

  const handleCreate = async (formData: EventCreate) => {
    setSubmitting(true)
    try {
      await createEvent(org.id, formData, accessToken)
      toast.success(t('events.toasts.create_success'))
      queryClient.invalidateQueries({ queryKey: queryKeys.events.list(org.id) })
      queryClient.invalidateQueries({ queryKey: queryKeys.events.upcoming(org.id) })
      setCreateModalOpen(false)
    } catch (err: any) {
      toast.error(err.message || t('events.toasts.create_error'))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (eventUuid: string) => {
    try {
      await deleteEvent(eventUuid, accessToken)
      toast.success(t('events.toasts.delete_success'))
      queryClient.invalidateQueries({ queryKey: queryKeys.events.list(org.id) })
      queryClient.invalidateQueries({ queryKey: queryKeys.events.upcoming(org.id) })
    } catch (err: any) {
      toast.error(err.message || t('events.toasts.delete_error'))
    }
  }

  // Users events by month
  const groupedEvents = events.reduce((groups: Record<string, Event[]>, event: Event) => {
    const monthKey = dayjs(event.event_date).format('YYYY-MM')
    if (!groups[monthKey]) groups[monthKey] = []
    groups[monthKey].push(event)
    return groups
  }, {})

  const sortedMonths = Object.keys(groupedEvents).sort()

  return (
    <div className="h-full w-full bg-background">
      <div className="px-4 sm:px-10 pt-8 pb-10">
        <div className="space-y-6 max-w-[1600px] mx-auto w-full">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{t('events.title')}</h1>
              <p className="text-sm text-gray-500 mt-1">{t('events.subtitle')}</p>
            </div>
            <button
              onClick={() => setCreateModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2.5 bg-black text-white rounded-lg text-sm font-medium hover:bg-black/90 transition-colors"
            >
              <Plus size={16} />
              {t('events.create_event')}
            </button>
          </div>

          {/* Events List */}
          {isLoading ? (
            <div className="space-y-4 animate-pulse">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-white rounded-xl shadow-xs p-6">
                  <div className="h-4 bg-gray-200 rounded w-1/4 mb-3" />
                  <div className="h-12 bg-gray-100 rounded" />
                </div>
              ))}
            </div>
          ) : events.length === 0 ? (
            <EmptyState
              icon={<Calendar className="text-gray-300" size={48} />}
              title={t('events.title')}
              description={t('events.no_upcoming')}
              action={
                <button
                  onClick={() => setCreateModalOpen(true)}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-black text-white rounded-lg text-sm font-medium hover:bg-black/90 transition-colors"
                >
                  <Plus size={16} />
                  {t('events.create_event')}
                </button>
              }
            />
          ) : (
            <div className="space-y-6">
              {sortedMonths.map((monthKey) => {
                const monthDate = dayjs(monthKey + '-01')
                return (
                  <div key={monthKey}>
                    <h2 className="text-lg font-bold text-gray-800 mb-3">
                      {monthDate.format('MMMM YYYY')}
                    </h2>
                    <div className="bg-white rounded-xl shadow-xs divide-y divide-gray-100">
                      {groupedEvents[monthKey].map((event: Event) => {
                        const eventDate = dayjs(event.event_date)
                        return (
                          <div key={event.event_uuid} className="p-4 hover:bg-gray-50 transition-colors">
                            <div className="flex items-start gap-4">
                              {/* Date Badge */}
                              <div className="flex-shrink-0 w-14 text-center">
                                <div className="text-xs font-bold uppercase text-gray-400">
                                  {eventDate.format('MMM')}
                                </div>
                                <div className="text-2xl font-bold text-gray-900 leading-tight">
                                  {eventDate.format('D')}
                                </div>
                              </div>

                              {/* Event Details */}
                              <div className="flex-1 min-w-0">
                                <div className="flex items-start justify-between gap-2">
                                  <div>
                                    <h3 className="font-semibold text-gray-900">{event.title}</h3>
                                    {event.description && (
                                      <p className="text-sm text-gray-500 mt-0.5 line-clamp-2">{event.description}</p>
                                    )}
                                  </div>
                                  <ConfirmationModal
                                    confirmationButtonText={t('events.delete_event')}
                                    confirmationMessage={`Delete "${event.title}"?`}
                                    dialogTitle={t('events.delete_event')}
                                    dialogTrigger={
                                      <button className="flex-shrink-0 p-1.5 rounded-md text-gray-400 hover:text-rose-600 hover:bg-rose-50 transition-colors">
                                        <Trash2 size={16} />
                                      </button>
                                    }
                                    functionToExecute={() => handleDelete(event.event_uuid)}
                                    status="warning"
                                  />
                                </div>
                                <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                                  {event.event_time && (
                                    <span className="flex items-center gap-1">
                                      <Clock size={14} />
                                      {event.event_time}
                                    </span>
                                  )}
                                  {event.timezone && <span>{event.timezone}</span>}
                                  {event.meeting_url && (
                                    <a
                                      href={event.meeting_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="flex items-center gap-1 text-indigo-600 hover:text-indigo-700 font-medium"
                                    >
                                      <Video size={14} />
                                      {t('events.join_meeting')}
                                      <ExternalLink size={12} />
                                    </a>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Create Event Modal */}
      <CreateEventModal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onSubmit={handleCreate}
        submitting={submitting}
      />
    </div>
  )
}

interface CreateEventModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: EventCreate) => Promise<void>
  submitting: boolean
}

function CreateEventModal({ isOpen, onClose, onSubmit, submitting }: CreateEventModalProps) {
  const { t } = useTranslation()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [eventDate, setEventDate] = useState(dayjs().format('YYYY-MM-DD'))
  const [eventTime, setEventTime] = useState('')
  const [timezone, setTimezone] = useState(Intl.DateTimeFormat().resolvedOptions().timeZone)
  const [meetingUrl, setMeetingUrl] = useState('')

  React.useEffect(() => {
    if (!isOpen) {
      setTitle('')
      setDescription('')
      setEventDate(dayjs().format('YYYY-MM-DD'))
      setEventTime('')
      setTimezone(Intl.DateTimeFormat().resolvedOptions().timeZone)
      setMeetingUrl('')
    }
  }, [isOpen])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return

    await onSubmit({
      title: title.trim(),
      description: description.trim() || null,
      event_date: eventDate,
      event_time: eventTime || null,
      timezone: timezone || null,
      meeting_url: meetingUrl || null,
    })
  }

  return (
    <Modal
      isDialogOpen={isOpen}
      onOpenChange={onClose}
      minHeight="no-min"
      minWidth="md"
      dialogContent={
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('events.form.title')} *</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-black/20 focus:border-black"
              required
              placeholder={t('events.form.title_placeholder')}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('events.form.description')}</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-black/20 focus:border-black min-h-[60px]"
              placeholder={t('events.form.description_placeholder')}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('events.form.date')} *</label>
              <input
                type="date"
                value={eventDate}
                onChange={(e) => setEventDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-black/20 focus:border-black"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('events.form.time')}</label>
              <input
                type="time"
                value={eventTime}
                onChange={(e) => setEventTime(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-black/20 focus:border-black"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('events.form.timezone')}</label>
              <input
                type="text"
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-black/20 focus:border-black"
                placeholder="America/New_York"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('events.form.meeting_url')}</label>
              <input
                type="url"
                value={meetingUrl}
                onChange={(e) => setMeetingUrl(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-black/20 focus:border-black"
                placeholder={t('events.form.meeting_url_placeholder')}
              />
            </div>
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
              disabled={submitting || !title.trim()}
              className="flex-1 px-4 py-2 bg-black text-white rounded-md text-sm font-medium hover:bg-black/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 size={14} className="animate-spin" />
                  {t('common.saving')}
                </span>
              ) : (
                t('events.create_event')
              )}
            </button>
          </div>
        </form>
      }
      dialogTitle={t('events.create_event')}
      dialogDescription=""
    />
  )
}
