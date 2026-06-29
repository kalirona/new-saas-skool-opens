import { RotateCw } from 'lucide-react'
import type { SearchMeta } from '@/lib/dashboard-search/types'

export const searchMeta: SearchMeta = {
  id: 'dash.courses.migrate',
  titleKey: 'dashboard.search.entries.courses_migrate.title',
  descriptionKey: 'dashboard.search.entries.courses_migrate.description',
  keywordsKey: 'dashboard.search.entries.courses_migrate.keywords',
  icon: RotateCw,
  href: '/dash/courses/migrate',
  group: 'navigation',
}
