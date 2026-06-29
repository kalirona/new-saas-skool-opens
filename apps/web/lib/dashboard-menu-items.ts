import { Home, BookOpen, Users, MessageCircle, Folder, Calendar, BarChart3, Settings } from 'lucide-react'

export interface DashboardMenuItem {
  id: string
  href: string
  icon: typeof Home
  labelKey: string
  featureKey?: string
  defaultDisabled?: boolean
}

export const DASHBOARD_MENU_ITEMS: DashboardMenuItem[] = [
  {
    id: 'home',
    href: '/dash',
    icon: Home,
    labelKey: 'common.home',
  },
  {
    id: 'community',
    href: '/dash/communities',
    icon: MessageCircle,
    labelKey: 'communities.title',
    featureKey: 'communities',
  },
  {
    id: 'courses',
    href: '/dash/courses',
    icon: BookOpen,
    labelKey: 'courses.courses',
  },
  {
    id: 'resources',
    href: '/dash/resources',
    icon: Folder,
    labelKey: 'common.resources',
  },
  {
    id: 'calendar',
    href: '/dash/calendar',
    icon: Calendar,
    labelKey: 'common.calendar',
  },
  {
    id: 'members',
    href: '/dash/users/settings/users',
    icon: Users,
    labelKey: 'common.members',
  },
  {
    id: 'analytics',
    href: '/dash/analytics',
    icon: BarChart3,
    labelKey: 'common.analytics',
  },
  {
    id: 'settings',
    href: '/dash/org/settings/general',
    icon: Settings,
    labelKey: 'common.settings',
  },
]
