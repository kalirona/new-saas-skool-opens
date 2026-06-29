import { Calendar } from 'lucide-react'
import type { SearchMeta } from '@/lib/dashboard-search/types'

export const searchMeta: SearchMeta = {
  id: 'dash.calendar',
  titleKey: 'common.calendar',
  descriptionKey: 'dashboard.search.entries.calendar.description',
  keywordsKey: 'dashboard.search.entries.calendar.keywords',
  icon: Calendar,
  href: '/dash/calendar',
  group: 'calendar',
}
