'use client'

import { Home, BookOpen, Users, Globe, HelpCircle, Settings, LogOut, Check, ChevronDown, MessageCircle, Book, BarChart3, Search, ShoppingBag, Folder, Calendar, PanelLeftOpen } from 'lucide-react'
import { useOrg } from '@components/Contexts/OrgContext'
import { signOut } from '@components/Contexts/AuthContext'

import { DiscordIcon } from '@components/Objects/Icons/DiscordIcon'
import NotificationBell from '@components/Notifications/NotificationBell'
import { BRAND_LOGOS, BRAND_LINKS } from '@/lib/brand'
import CommandPaletteTrigger from '@components/Dashboard/CommandPalette/CommandPaletteTrigger'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import React, { useEffect, useState } from 'react'
import UserAvatar from '../../Objects/UserAvatar'
import AdminAuthorization from '@components/Security/AdminAuthorization'
import { useLHSession } from '@components/Contexts/LHSessionContext'
import { getUriWithOrg } from '@services/config/config'
import { useTranslation } from 'react-i18next'
import { changeLanguage } from '@/lib/i18n'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@components/ui/tooltip"
import {
  HoverMenu,
  HoverMenuContent,
  HoverMenuItem,
  HoverMenuLabel,
  HoverMenuSeparator,
} from "@components/ui/hover-menu"
import { FeedbackModal } from '@components/Objects/Modals/FeedbackModal'
import { AVAILABLE_LANGUAGES } from '@/lib/languages'
import { getOrgLogoMediaDirectory } from '@services/media/media'
import { cn } from '@/lib/utils'
import { getDeploymentMode } from '@services/config/config'
import { usePlan } from '@components/Hooks/usePlan'

function DashLeftMenu() {
  const org = useOrg() as any
  const session = useLHSession() as any
  const { t, i18n } = useTranslation()
  const pathname = usePathname() || ''
  const [isCollapsed, setIsCollapsed] = useState(false)

  const isActivePath = (path: string) => {
    if (path === '/dash') {
      return pathname === '/dash' || pathname === '/dash/'
    }
    return pathname === path || pathname.startsWith(path + '/')
  }
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false)

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('dash-menu-collapsed')
      if (saved !== null) {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setIsCollapsed(saved === 'true')
      }
    }
  }, [])

  const toggleCollapse = () => {
    const newState = !isCollapsed
    setIsCollapsed(newState)
    localStorage.setItem('dash-menu-collapsed', String(newState))
  }

  async function logOutUI() {
    await signOut({ redirect: true, callbackUrl: getUriWithOrg(org.slug, '/login') })
  }

  const plan = usePlan()
  const mode = getDeploymentMode()

  if (!org || !session) return null
  const planLabel =
    mode === 'ee' ? 'Enterprise Edition' :
    mode === 'oss' ? 'OSS' :
    plan  // SaaS: show actual plan name

  // Feature visibility from API resolved_features
  const rf = org?.config?.config?.resolved_features
  const isEnabled = (feature: string) => rf?.[feature]?.enabled === true

  const showCommunities = isEnabled('communities')

  return (
    <TooltipProvider delayDuration={0}>
    <nav
      aria-label="Dashboard sidebar navigation"
      className={cn(
        "flex flex-col text-white h-screen sticky top-0 z-overlay border-r border-white/[0.08] bg-[#0f0f10] transition-all duration-300",
        isCollapsed ? "w-[72px]" : "w-64"
      )}
    >
      {/* Header with Logo and Toggle */}
      <div className={cn(
        "flex items-center h-16 border-b border-white/[0.08] px-4 shrink-0",
        isCollapsed ? "justify-center" : "justify-between"
      )}>
        <Link
          className={cn("flex items-center transition-opacity hover:opacity-70", isCollapsed ? "" : "space-x-3")}
          href={'/'}
        >
          {plan === 'enterprise' && org?.logo_image ? (
            <img
              src={getOrgLogoMediaDirectory(org.org_uuid, org.logo_image)}
              alt={org?.name}
              className="h-9 w-9 object-contain rounded-lg"
            />
          ) : (
            <img
              src={BRAND_LOGOS.dash}
              alt=""
              className="h-8 w-8"
            />
          )}
          {!isCollapsed && (
            <div className="flex flex-col min-w-0">
              <span className="font-semibold text-sm text-white truncate">
                {org?.name}
              </span>
              <span className={cn(
                "text-[9px] font-medium uppercase tracking-wider",
                mode === 'ee' ? "text-amber-400" :
                mode === 'oss' ? "text-green-400" :
                plan === 'enterprise' ? "text-amber-400" :
                plan === 'pro' ? "text-purple-400" :
                plan === 'standard' ? "text-blue-400" :
                "text-white/40"
              )}>
                {planLabel}
              </span>
            </div>
          )}
        </Link>

        {!isCollapsed && (
          <button
            aria-label="Collapse sidebar"
            onClick={toggleCollapse}
            className="p-2 rounded-lg text-white/40 hover:text-white hover:bg-white/[0.08] transition-all"
          >
            <PanelLeftOpen size={18} />
          </button>
        )}
      </div>

      {/* Search trigger */}
      <div className="px-3 pt-3">
        <CommandPaletteTrigger isCollapsed={isCollapsed} />
      </div>

      {/* Main Navigation */}
      <div className="flex-1 flex flex-col py-4 px-3">
        <AdminAuthorization authorizationMode="component">
          <div className="space-y-0.5">
            <MenuLink
              href="/dash"
              icon={<Home size={20} />}
              label={t('common.home')}
              isCollapsed={isCollapsed}
              active={isActivePath('/dash')}
            />
            {showCommunities && (
              <MenuLink
                href="/dash/communities"
                icon={<MessageCircle size={20} />}
                label={t('communities.title')}
                isCollapsed={isCollapsed}
                active={isActivePath('/dash/communities')}
              />
            )}
            <MenuLink
              href="/dash/courses"
              icon={<BookOpen size={20} />}
              label={t('courses.courses')}
              isCollapsed={isCollapsed}
              active={isActivePath('/dash/courses')}
            />
            <MenuLink
              href="/dash/resources"
              icon={<Folder size={20} />}
              label={t('common.resources')}
              isCollapsed={isCollapsed}
              active={isActivePath('/dash/resources') || isActivePath('/dash/library') || isActivePath('/dash/boards') || isActivePath('/dash/playgrounds') || isActivePath('/dash/podcasts')}
            />
            <MenuLink
              href="/dash/calendar"
              icon={<Calendar size={20} />}
              label={t('common.calendar')}
              isCollapsed={isCollapsed}
              active={isActivePath('/dash/calendar')}
            />
            <MenuLink
              href="/dash/users/settings/users"
              icon={<Users size={20} />}
              label={t('common.members')}
              isCollapsed={isCollapsed}
              active={isActivePath('/dash/users')}
            />
            <MenuLink
              href="/dash/analytics"
              icon={<BarChart3 size={20} />}
              label={t('common.analytics')}
              isCollapsed={isCollapsed}
              active={isActivePath('/dash/analytics')}
            />
            <MenuLink
              href="/dash/org/settings/general"
              icon={<Settings size={20} />}
              label={t('common.settings')}
              isCollapsed={isCollapsed}
              active={isActivePath('/dash/org')}
            />
          </div>
        </AdminAuthorization>
      </div>

      {/* Bottom Section */}
      <div className="border-t border-white/[0.08] py-3 px-3 shrink-0">
        <div className="space-y-1">
          {/* Expand button when collapsed */}
          {isCollapsed && (
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  aria-label="Expand sidebar"
                  onClick={toggleCollapse}
                  className="flex items-center justify-center w-full h-10 rounded-lg text-white/40 hover:text-white hover:bg-white/[0.08] transition-all"
                >
                  <PanelLeftOpen size={20} />
                </button>
              </TooltipTrigger>
              <TooltipContent side="right" className="z-tooltip bg-[#1a1a1b] border-white/10 text-white text-xs px-2 py-1 shadow-lg shadow-black/20">
                {t('common.expand')}
              </TooltipContent>
            </Tooltip>
          )}

          {/* Language Switcher with hover menu */}
          <HoverMenu
            align="end"
            content={
              <HoverMenuContent className="w-64 max-h-96 overflow-y-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
                <HoverMenuLabel className="flex items-center gap-2 text-white/70 font-medium">
                  <Globe size={16} />
                  <span>{t('common.language')}</span>
                </HoverMenuLabel>
                <HoverMenuSeparator />
                {AVAILABLE_LANGUAGES.map((language) => (
                  <HoverMenuItem
                    key={language.code}
                    onClick={() => changeLanguage(language.code)}
                    className="flex items-center justify-between px-3 py-2.5 cursor-pointer text-white/70 hover:text-white hover:bg-white/[0.08] transition-colors"
                  >
                    <div className="flex flex-col">
                      <span className="font-medium text-sm">{language.nativeName}</span>
                      <span className="text-xs text-white/40">{t(language.translationKey)}</span>
                    </div>
                    {i18n.language.split('-')[0] === language.code && (
                      <Check size={16} className="text-green-500" />
                    )}
                  </HoverMenuItem>
                ))}
              </HoverMenuContent>
            }
          >
            <button aria-label="Open language menu" className={cn(
              "flex items-center w-full rounded-lg text-white/50 hover:text-white hover:bg-white/[0.08] transition-all group",
              isCollapsed ? "justify-center h-10" : "px-3 py-2 gap-3"
            )}>
              <Globe size={20} />
              {!isCollapsed && (
                <span className="text-sm font-medium">{t('common.language')}</span>
              )}
            </button>
          </HoverMenu>

          {/* Help with hover menu */}
          <HoverMenu
            align="end"
            content={
              <HoverMenuContent className="w-56">
                <HoverMenuLabel className="flex items-center gap-2 text-white/70 font-medium">
                  <HelpCircle size={16} />
                  <span>{t('common.help')}</span>
                </HoverMenuLabel>
                <HoverMenuSeparator />
                <HoverMenuItem asChild>
                  <a
                    href={BRAND_LINKS.docs}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-3 py-2 text-sm text-white/70 hover:text-white hover:bg-white/[0.08] cursor-pointer transition-colors"
                  >
                    <Book size={16} />
                    <span>{t('common.help_menu.documentation')}</span>
                  </a>
                </HoverMenuItem>
                <HoverMenuItem asChild>
                  <a
                    href={BRAND_LINKS.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-3 py-2 text-sm text-white/70 hover:text-white hover:bg-white/[0.08] cursor-pointer transition-colors"
                  >
                    <Globe size={16} />
                    <span>{t('common.help_menu.website')}</span>
                  </a>
                </HoverMenuItem>
                <HoverMenuItem asChild>
                  <a
                    href={BRAND_LINKS.discord}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-3 py-2 text-sm text-white/70 hover:text-white hover:bg-white/[0.08] cursor-pointer transition-colors"
                  >
                    <DiscordIcon size={16} />
                    <span>{t('common.help_menu.discord')}</span>
                  </a>
                </HoverMenuItem>
                <HoverMenuSeparator />
                <HoverMenuItem
                  onClick={() => setFeedbackModalOpen(true)}
                  className="flex items-center gap-2 px-3 py-2 text-sm text-white/70 hover:text-white hover:bg-white/[0.08] cursor-pointer transition-colors"
                >
                  <MessageCircle size={16} />
                  <span>{t('common.help_menu.report_feedback')}</span>
                </HoverMenuItem>
              </HoverMenuContent>
            }
          >
            <button aria-label="Open help menu" className={cn(
              "flex items-center w-full rounded-lg text-white/50 hover:text-white hover:bg-white/[0.08] transition-all group",
              isCollapsed ? "justify-center h-10" : "px-3 py-2 gap-3"
            )}>
              <HelpCircle size={20} />
              {!isCollapsed && (
                <span className="text-sm font-medium">{t('common.help')}</span>
              )}
            </button>
          </HoverMenu>

          {/* Notifications Bell */}
          <div className={cn(
            "flex items-center w-full",
            isCollapsed ? "justify-center h-10" : "px-3 py-2"
          )}>
            {isCollapsed ? (
              <Tooltip>
                <TooltipTrigger asChild>
                  <span>
                    <NotificationBell />
                  </span>
                </TooltipTrigger>
                <TooltipContent side="right" className="z-tooltip bg-[#1a1a1b] border-white/10 text-white text-xs px-2 py-1 shadow-lg shadow-black/20">
                  {t('notifications.title')}
                </TooltipContent>
              </Tooltip>
            ) : (
              <NotificationBell />
            )}
          </div>

          {/* User Menu with hover menu */}
          <HoverMenu
            align="end"
            content={
              <HoverMenuContent className="w-56">
                <div className="px-3 py-2">
                  <p className="text-sm font-semibold text-white/90">{session?.data?.user?.username}</p>
                  <p className="text-xs text-white/40">{session?.data?.user?.email}</p>
                </div>
                <HoverMenuSeparator />
                <HoverMenuItem asChild>
                  <Link href="/account/general" className="flex items-center gap-2 px-3 py-2 text-sm text-white/70 hover:text-white hover:bg-white/[0.08] cursor-pointer transition-colors">
                    <Settings size={16} />
                    <span>{t('common.settings')}</span>
                  </Link>
                </HoverMenuItem>
                <HoverMenuItem asChild>
                  <Link href={getUriWithOrg(org?.slug, '/account/purchases')} className="flex items-center gap-2 px-3 py-2 text-sm text-white/70 hover:text-white hover:bg-white/[0.08] cursor-pointer transition-colors">
                    <ShoppingBag size={16} />
                    <span>{t('account.purchases')}</span>
                  </Link>
                </HoverMenuItem>
                <HoverMenuSeparator />
                <HoverMenuItem
                  onClick={() => logOutUI()}
                  className="flex items-center gap-2 px-3 py-2 text-sm text-red-500 hover:text-red-400 hover:bg-white/[0.08] cursor-pointer transition-colors"
                >
                  <LogOut size={16} />
                  <span>{t('user.sign_out')}</span>
                </HoverMenuItem>
              </HoverMenuContent>
            }
          >
            <button className={cn(
              "flex items-center w-full rounded-lg text-white/50 hover:text-white hover:bg-white/[0.08] transition-all group",
              isCollapsed ? "justify-center h-10" : "px-3 py-2 gap-3"
            )}>
              <UserAvatar width={24} rounded="rounded-full" shadow="shadow-none" />
              {!isCollapsed && (
                <div className="flex flex-col min-w-0 flex-1 text-left">
                  <span className="text-sm font-medium truncate text-white/90">{session?.data?.user?.username}</span>
                  <span className="text-xs text-white/40 truncate">{session?.data?.user?.email}</span>
                </div>
              )}
            </button>
          </HoverMenu>
        </div>
      </div>
    </nav>

      {/* Feedback Modal */}
      <FeedbackModal
        open={feedbackModalOpen}
        onOpenChange={setFeedbackModalOpen}
        theme="dark"
        userName={session?.data?.user?.username}
        userEmail={session?.data?.user?.email}
      />
    </TooltipProvider>
  )
}

const MenuLink = ({ href, icon, label, isCollapsed, isExternal, active }: {
  href: string
  icon: React.ReactNode
  label: string
  isCollapsed: boolean
  isExternal?: boolean
  active?: boolean
}) => {
  const content = (
    <div
      className={cn(
        "relative flex items-center w-full rounded-lg transition-all",
        active
          ? "text-white bg-white/[0.08]"
          : "text-white/50 hover:text-white hover:bg-white/[0.08]",
        isCollapsed ? "justify-center h-10" : "px-3 py-2 gap-3"
      )}
    >
      {active && (
        <span
          aria-hidden="true"
          className="absolute left-0.5 top-1/2 -translate-y-1/2 h-5 w-[3px] bg-white rounded-full"
        />
      )}
      {icon}
      {!isCollapsed && (
        <span className="text-sm font-medium">{label}</span>
      )}
    </div>
  )

  const ariaCurrent = active ? 'page' : undefined
  const linkElement = isExternal ? (
    <a href={href} target="_blank" rel="noopener noreferrer" aria-label={label}>
      {content}
    </a>
  ) : (
    <Link aria-label={label} aria-current={ariaCurrent} href={href}>
      {content}
    </Link>
  )

  if (isCollapsed) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          {linkElement}
        </TooltipTrigger>
        <TooltipContent side="right" className="z-tooltip bg-[#1a1a1b] border-white/10 text-white text-xs px-2 py-1 shadow-lg shadow-black/20">
          {label}
        </TooltipContent>
      </Tooltip>
    )
  }

  return linkElement
}

export default DashLeftMenu
