'use client'
import { Breadcrumbs } from '@components/Objects/Breadcrumbs/Breadcrumbs'
import { getUriWithOrg } from '@services/config/config'
import { LayoutDashboard, Palette, Globe, Users, Shield, BarChart3, Zap, Search, School, Key, Menu, Code, ChevronRight, Sparkles } from 'lucide-react'
import React, { useEffect, use } from 'react';
import { motion } from 'motion/react'
import Link from 'next/link'
import OrgEditGeneral from '@components/Dashboard/Pages/Org/OrgEditGeneral/OrgEditGeneral'
import OrgEditBranding from '@components/Dashboard/Pages/Org/OrgEditBranding/OrgEditBranding'
import OrgEditLanding from '@components/Dashboard/Pages/Org/OrgEditLanding/OrgEditLanding'
import OrgEditOther from '@components/Dashboard/Pages/Org/OrgEditOther/OrgEditOther'
import OrgEditAPIAccess from '@components/Dashboard/Pages/Org/OrgEditAPIAccess/OrgEditAPIAccess'
import OrgEditAI from '@components/Dashboard/Pages/Org/OrgEditAI/OrgEditAI'
import OrgEditSSO from '@components/Dashboard/Pages/Org/OrgEditSSO/OrgEditSSO'
import OrgEditDomains from '@components/Dashboard/Pages/Org/OrgEditDomains/OrgEditDomains'
import OrgEditSEO from '@components/Dashboard/Pages/Org/OrgEditSEO/OrgEditSEO'
import OrgEditUsage from '@components/Dashboard/Pages/Org/OrgEditUsage/OrgEditUsage'
import OrgEditAutomations from '@components/Dashboard/Pages/Org/OrgEditAutomations/OrgEditAutomations'
import OrgEditMenu from '@components/Dashboard/Pages/Org/OrgEditMenu/OrgEditMenu'
import { useTranslation } from 'react-i18next'
import { DashTabBar, DashTabItem } from '@components/Dashboard/Shared/DashTabBar/DashTabBar'

export type OrgParams = {
  subpage: string
  orgslug: string
}

interface SettingCategory {
  id: string
  label: string
  icon: React.ElementType
  subpages: string[]
  firstSubpage: string
  externalUrl?: string
}

const SETTING_CATEGORIES: SettingCategory[] = [
  { id: 'branding', label: 'Branding', icon: Palette, subpages: ['general', 'branding', 'menu', 'landing', 'seo'], firstSubpage: 'general' },
  { id: 'domain', label: 'Domain', icon: Globe, subpages: ['domains'], firstSubpage: 'domains' },
  { id: 'members', label: 'Members', icon: Users, subpages: [], firstSubpage: '', externalUrl: '/dash/users/settings/users' },
  { id: 'security', label: 'Security', icon: Shield, subpages: ['sso', 'api'], firstSubpage: 'sso' },
  { id: 'billing', label: 'Billing', icon: BarChart3, subpages: ['usage'], firstSubpage: 'usage' },
  { id: 'integrations', label: 'Integrations', icon: Zap, subpages: ['automations', 'ai', 'other'], firstSubpage: 'automations' },
]

const SUBPAGE_LABELS: Record<string, string> = {
  general: 'General',
  branding: 'Branding',
  menu: 'Public Menu',
  landing: 'Landing Page',
  seo: 'SEO',
  domains: 'Custom Domains',
  sso: 'SSO',
  api: 'API Access',
  usage: 'Usage & Billing',
  automations: 'Webhooks',
  ai: 'AI Features',
  other: 'Advanced',
}

const SUBPAGE_ICONS: Record<string, React.ElementType> = {
  general: LayoutDashboard,
  branding: Palette,
  menu: Menu,
  landing: LayoutDashboard,
  seo: Search,
  domains: Globe,
  sso: Shield,
  api: Key,
  usage: BarChart3,
  automations: Zap,
  ai: Sparkles,
  other: Code,
}

function findCategory(subpage: string): SettingCategory | undefined {
  return SETTING_CATEGORIES.find(cat => cat.subpages.includes(subpage))
}

function OrgSettingsPage(props: { params: Promise<OrgParams> }) {
  const { t } = useTranslation()
  const params = use(props.params);
  const orgslug = params.orgslug
  const currentSubpage = params.subpage
  const activeCategory = findCategory(currentSubpage) || SETTING_CATEGORIES[0]

  const [H1Label, setH1Label] = React.useState('')
  const [H2Label, setH2Label] = React.useState('')

  function handleLabels() {
    if (currentSubpage == 'general') {
      setH1Label(t('dashboard.organization.settings.pages.general.title'))
      setH2Label(t('dashboard.organization.settings.pages.general.subtitle'))
    } else if (currentSubpage == 'branding') {
      setH1Label(t('dashboard.organization.settings.pages.branding.title'))
      setH2Label(t('dashboard.organization.settings.pages.branding.subtitle'))
    } else if (currentSubpage == 'menu') {
      setH1Label(t('dashboard.organization.settings.pages.menu.title') || 'Public menu')
      setH2Label(t('dashboard.organization.settings.pages.menu.subtitle') || 'Choose and order the links shown in your public navigation')
    } else if (currentSubpage == 'landing') {
      setH1Label(t('dashboard.organization.settings.pages.landing.title'))
      setH2Label(t('dashboard.organization.settings.pages.landing.subtitle'))
    } else if (currentSubpage == 'seo') {
      setH1Label('SEO')
      setH2Label('Manage search engine optimization settings')
    } else if (currentSubpage == 'ai') {
      setH1Label(t('dashboard.organization.settings.pages.ai.title') || 'AI Features')
      setH2Label(t('dashboard.organization.settings.pages.ai.subtitle') || 'Configure AI capabilities for your organization')
    } else if (currentSubpage == 'domains') {
      setH1Label(t('dashboard.organization.settings.pages.domains.title') || 'Custom Domains')
      setH2Label(t('dashboard.organization.settings.pages.domains.subtitle') || 'Configure custom domains for your organization')
    } else if (currentSubpage == 'automations') {
      setH1Label(t('dashboard.organization.settings.tabs.automations') || 'Automations')
      setH2Label(t('dashboard.organization.automations.webhooks_subtitle') || 'Connect external services with webhooks')
    } else if (currentSubpage == 'api') {
      setH1Label(t('dashboard.organization.settings.pages.api.title') || 'API Access')
      setH2Label(t('dashboard.organization.settings.pages.api.subtitle') || 'Manage API tokens and access')
    } else if (currentSubpage == 'sso') {
      setH1Label(t('dashboard.organization.settings.pages.sso.title') || 'Single Sign-On')
      setH2Label(t('dashboard.organization.settings.pages.sso.subtitle') || 'Configure SSO for your organization')
    } else if (currentSubpage == 'usage') {
      setH1Label(t('dashboard.organization.settings.pages.usage.title') || 'Usage')
      setH2Label(t('dashboard.organization.settings.pages.usage.subtitle') || 'Monitor your organization\'s resource usage and plan limits')
    } else if (currentSubpage == 'other') {
      setH1Label(t('dashboard.organization.settings.pages.other.title'))
      setH2Label(t('dashboard.organization.settings.pages.other.subtitle'))
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    handleLabels()
  }, [currentSubpage, params, t])

  const categoryTabs: DashTabItem[] = SETTING_CATEGORIES.map((cat) => ({
    key: cat.id,
    label: cat.label,
    icon: <cat.icon size={16} />,
    href: cat.externalUrl
      ? cat.externalUrl
      : getUriWithOrg(orgslug, '') + `/dash/org/settings/${cat.firstSubpage}`,
    active: cat.id === activeCategory.id,
  }))

  const subTabs: DashTabItem[] = activeCategory.subpages.length > 1
    ? activeCategory.subpages.map((sp) => {
        const IconCmp = SUBPAGE_ICONS[sp]
        return {
          key: sp,
          label: SUBPAGE_LABELS[sp] || sp,
          icon: IconCmp ? <IconCmp size={14} /> : null,
          href: getUriWithOrg(orgslug, '') + `/dash/org/settings/${sp}`,
          active: currentSubpage === sp,
        }
      })
    : []

  return (
    <div className="h-full w-full bg-background flex flex-col">
      <div className="pl-4 pr-4 sm:pl-10 sm:pr-10 tracking-tight bg-background z-10 nice-shadow flex-shrink-0 relative">
        <div className="pt-6 pb-4">
          <Breadcrumbs items={[
            { label: t('common.settings'), href: '/dash/org/settings/general', icon: <School size={14} /> }
          ]} />
        </div>
        <div className="my-2 py-2">
          <div className="w-full flex flex-col space-y-1 min-w-0">
            <div className="pt-3 flex font-bold text-3xl sm:text-4xl tracking-tighter truncate">
              {H1Label}
            </div>
            <div className="flex font-medium text-gray-400 text-md truncate">
              {H2Label}
            </div>
          </div>
        </div>
        <DashTabBar tabs={categoryTabs} />
        {subTabs.length > 0 && (
          <div className="flex gap-1 pb-3 -mt-1">
            {subTabs.map((st) => {
              const subTabClass = `px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                st.active
                  ? 'bg-gray-100 text-gray-900'
                  : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'
              }`
              return st.href ? (
                <Link key={st.key} href={st.href} prefetch={false} className={subTabClass}>
                  <div className="flex items-center gap-1.5">
                    {st.icon}
                    {st.label}
                  </div>
                </Link>
              ) : null
            })}
          </div>
        )}
      </div>
      <div className="h-6 flex-shrink-0"></div>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.1, type: 'spring', stiffness: 80 }}
        className="flex-1 overflow-y-auto"
      >
        {activeCategory.id === 'members' ? (
          <div className="px-4 sm:px-10 py-8">
            <div className="max-w-lg mx-auto bg-white rounded-2xl border border-gray-100 p-8 text-center nice-shadow">
              <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center mx-auto mb-4">
                <Users size={24} className="text-blue-500" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">{t('dashboard.organization.settings.members_title') || 'Member Management'}</h3>
              <p className="text-sm text-gray-500 mb-6">{t('dashboard.organization.settings.members_description') || 'Manage your organization members, roles, and permissions from the Members page.'}</p>
              <Link
                href={getUriWithOrg(orgslug, '/dash/users/settings/users')}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-gray-900 text-white text-sm font-semibold rounded-lg hover:bg-gray-800 transition-colors"
              >
                {t('dashboard.organization.settings.go_to_members') || 'Go to Members'}
                <ChevronRight size={16} />
              </Link>
            </div>
          </div>
        ) : currentSubpage == 'general' ? <OrgEditGeneral />
        : currentSubpage == 'branding' ? <OrgEditBranding />
        : currentSubpage == 'menu' ? <OrgEditMenu />
        : currentSubpage == 'landing' ? <OrgEditLanding />
        : currentSubpage == 'seo' ? <OrgEditSEO />
        : currentSubpage == 'ai' ? <OrgEditAI />
        : currentSubpage == 'domains' ? <OrgEditDomains />
        : currentSubpage == 'automations' ? <OrgEditAutomations />
        : currentSubpage == 'api' ? <OrgEditAPIAccess />
        : currentSubpage == 'sso' ? <OrgEditSSO />
        : currentSubpage == 'usage' ? <OrgEditUsage />
        : currentSubpage == 'other' ? <OrgEditOther />
        : null}
      </motion.div>
    </div>
  )
}

export default OrgSettingsPage
