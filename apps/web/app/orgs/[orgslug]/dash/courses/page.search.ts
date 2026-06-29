import { BookOpen } from 'lucide-react'
import type { SearchMeta } from '@/lib/dashboard-search/types'

export const searchMeta: SearchMeta = {
  id: 'dash.courses',
  titleKey: 'common.all_courses',
  descriptionKey: 'dashboard.search.entries.courses.description',
  keywordsKey: 'dashboard.search.entries.courses.keywords',
  icon: BookOpen,
  href: '/dash/courses',
  group: 'navigation',
}
