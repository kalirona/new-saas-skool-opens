'use client'
import { Calendar, Clock, Video, MapPin, ArrowRight } from 'lucide-react'
import React from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { useOrg } from '@components/Contexts/OrgContext'
import { useLHSession } from '@components/Contexts/LHSessionContext'
import { queryKeys } from '@/lib/query/keys'
import { getUpcomingEvents } from '@services/events/events'

import Link from 'next/link'
import { getUriWithOrg } from '@services/config/config'
import dayjs from 'dayjs'

interface UpcomingEventsWidgetProps {
  maxEvents?: number
}

export function UpcomingEventsWidget({ maxEvents = 5 }: UpcomingEventsWidgetProps) {
  const { t } = useTranslation()
  const org = useOrg() as any
  const session = useLHSession() as any
  const accessToken = session?.data?.tokens?.access_token

  const { data: events, isLoading } = useQuery({
    queryKey: queryKeys.events.upcoming(org?.id),
    queryFn: () => getUpcomingEvents(org.id, maxEvents, accessToken),
    enabled: !!(org?.id && accessToken),
    staleTime: 60_000,
  })

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-xs p-5">
        <div className="animate-pulse space-y-3">
          <div className="h-5 bg-gray-200 rounded w-1/3" />
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-14 bg-gray-100 rounded-lg" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-xs p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Calendar className="text-gray-500" size={20} />
          <h3 className="font-semibold text-gray-900">{t('events.upcoming_title')}</h3>
        </div>
        <Link
          href={getUriWithOrg(org?.slug, '/dash/calendar')}
          className="text-xs text-indigo-600 hover:text-indigo-700 font-medium flex items-center gap-1"
        >
          {t('events.view_all')}
          <ArrowRight size={12} />
        </Link>
      </div>

      {!events || events.length === 0 ? (
        <div className="text-center py-6">
          <Calendar className="mx-auto text-gray-300 mb-2" size={32} />
          <p className="text-sm text-gray-500">{t('events.no_upcoming')}</p>
        </div>
      ) : (
        <div className="space-y-2">
          {events.map((event) => {
            const eventDate = dayjs(event.event_date)
            const isToday = eventDate.isSame(dayjs(), 'day')
            const isTomorrow = eventDate.isSame(dayjs().add(1, 'day'), 'day')
            const dayLabel = isToday ? t('events.today') : isTomorrow ? t('events.tomorrow') : eventDate.format('MMM D')

            return (
              <div
                key={event.event_uuid}
                className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors group"
              >
                <div className="flex-shrink-0 w-10 text-center">
                  <div className={`text-xs font-bold uppercase ${isToday ? 'text-indigo-600' : 'text-gray-400'}`}>
                    {dayLabel}
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 leading-snug">{event.title}</h4>
                      {event.description && (
                        <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">{event.description}</p>
                      )}
                    </div>
                    {event.meeting_url && (
                      <a
                        href={event.meeting_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex-shrink-0 p-1.5 rounded-md text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 opacity-0 group-hover:opacity-100 transition-all"
                        title={t('events.join_meeting')}
                      >
                        <Video size={14} />
                      </a>
                    )}
                  </div>
                  <div className="flex items-center gap-3 mt-1">
                    {event.event_time && (
                      <span className="flex items-center gap-1 text-xs text-gray-400">
                        <Clock size={12} />
                        {event.event_time}
                      </span>
                    )}
                    {event.timezone && (
                      <span className="text-xs text-gray-400">{event.timezone}</span>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default UpcomingEventsWidget
