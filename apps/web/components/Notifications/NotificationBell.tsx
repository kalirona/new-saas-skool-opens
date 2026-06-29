'use client'
import { Bell, BellRing, Check, CheckCheck, Clock } from 'lucide-react'
import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useLHSession } from '@components/Contexts/LHSessionContext'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getNotifications, getUnreadCount, markAsRead, markAllAsRead, Notification } from '@services/notifications/notifications'

import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import Link from 'next/link'
import { getUriWithOrg } from '@services/config/config'
import { useOrg } from '@components/Contexts/OrgContext'
import EmptyState from '@components/shared/EmptyState'

dayjs.extend(relativeTime)

const NOTIFICATION_TYPE_ICONS: Record<string, React.ReactNode> = {
  new_comment: <BellRing size={16} className="text-blue-500" />,
  new_discussion: <BellRing size={16} className="text-green-500" />,
  mention: <BellRing size={16} className="text-purple-500" />,
  event_reminder: <Clock size={16} className="text-amber-500" />,
}

const DEFAULT_ICON = <BellRing size={16} className="text-gray-400" />

export function NotificationBell() {
  const { t } = useTranslation()
  const session = useLHSession() as any
  const org = useOrg() as any
  const accessToken = session?.data?.tokens?.access_token
  const queryClient = useQueryClient()
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const { data: unreadCount = 0 } = useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: () => getUnreadCount(accessToken),
    enabled: !!accessToken,
    refetchInterval: 30_000,
    staleTime: 15_000,
  })

  const { data: notifData } = useQuery({
    queryKey: ['notifications', 'list'],
    queryFn: () => getNotifications({ limit: 10 }, accessToken),
    enabled: !!accessToken && isOpen,
    staleTime: 5_000,
  })

  const notifications = notifData?.notifications || []

  const handleMarkRead = async (uuid: string) => {
    if (!accessToken) return
    await markAsRead(uuid, accessToken)
    queryClient.invalidateQueries({ queryKey: ['notifications'] })
  }

  const handleMarkAllRead = async () => {
    if (!accessToken) return
    await markAllAsRead(accessToken)
    queryClient.invalidateQueries({ queryKey: ['notifications'] })
  }

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isOpen])

  return (
    <div ref={dropdownRef} className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg text-white/40 hover:text-white hover:bg-white/[0.08] transition-all"
        aria-label={t('notifications.title')}
      >
        {unreadCount > 0 ? (
          <>
            <BellRing size={20} />
            <span className="absolute -top-0.5 -right-0.5 w-4.5 h-4.5 bg-rose-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center min-w-[18px] min-h-[18px]">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          </>
        ) : (
          <Bell size={20} />
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-[#1a1a1b] border border-white/[0.08] rounded-xl shadow-2xl shadow-black/40 z-50 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.08]">
            <h3 className="text-sm font-semibold text-white">{t('notifications.title')}</h3>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1"
              >
                <Check size={12} />
                {t('notifications.mark_all_read')}
              </button>
            )}
          </div>

          {/* List */}
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <EmptyState
                icon={<Bell className="text-white/20" size={24} />}
                title={t('notifications.empty')}
                className="px-4 py-8"
              />
            ) : (
              notifications.map((notif: Notification) => (
                <NotificationItem
                  key={notif.notification_uuid}
                  notification={notif}
                  onMarkRead={handleMarkRead}
                  orgSlug={org?.slug}
                />
              ))
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="border-t border-white/[0.08] px-4 py-2.5">
              <Link
                href={getUriWithOrg(org?.slug, '/dash/notifications')}
                onClick={() => setIsOpen(false)}
                className="block text-center text-xs text-white/40 hover:text-white/60 font-medium"
              >
                {t('notifications.view_all')}
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

interface NotificationItemProps {
  notification: Notification
  onMarkRead: (uuid: string) => void
  orgSlug: string
}

function NotificationItem({ notification, onMarkRead, orgSlug }: NotificationItemProps) {
  const icon = NOTIFICATION_TYPE_ICONS[notification.notification_type] || DEFAULT_ICON

  const handleClick = () => {
    if (!notification.is_read) {
      onMarkRead(notification.notification_uuid)
    }
  }

  const linkHref = notification.link
    ? notification.link.startsWith('/')
      ? getUriWithOrg(orgSlug, notification.link)
      : notification.link
    : '#'

  const inner = (
    <div
      className={`flex items-start gap-3 px-4 py-3 cursor-pointer transition-colors hover:bg-white/[0.04] ${
        !notification.is_read ? 'bg-white/[0.03] border-l-2 border-indigo-500' : ''
      }`}
      onClick={handleClick}
    >
      <div className="flex-shrink-0 mt-0.5">{icon}</div>
      <div className="flex-1 min-w-0">
        <p className={`text-sm leading-snug ${!notification.is_read ? 'text-white font-medium' : 'text-white/70'}`}>
          {notification.title}
        </p>
        {notification.message && (
          <p className="text-xs text-white/40 mt-0.5 line-clamp-2">{notification.message}</p>
        )}
        <p className="text-[10px] text-white/30 mt-1">
          {dayjs(notification.creation_date).fromNow()}
        </p>
      </div>
      {!notification.is_read && (
        <button
          onClick={(e) => { e.stopPropagation(); onMarkRead(notification.notification_uuid) }}
          className="flex-shrink-0 p-1 rounded-md text-white/30 hover:text-white/60 hover:bg-white/[0.08] transition-colors"
          title="Mark as read"
        >
          <CheckCheck size={12} />
        </button>
      )}
    </div>
  )

  if (notification.link) {
    return (
      <Link href={linkHref} className="block no-underline">
        {inner}
      </Link>
    )
  }

  return inner
}

export default NotificationBell
