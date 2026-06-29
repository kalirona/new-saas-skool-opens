import { Folder } from 'lucide-react'
import type { SearchMeta } from '@/lib/dashboard-search/types'

export const searchMeta: SearchMeta = {
  id: 'dash.resources',
  titleKey: 'dashboard.resources.title',
  descriptionKey: 'dashboard.search.entries.resources.description',
  keywordsKey: 'dashboard.search.entries.resources.keywords',
  icon: Folder,
  href: '/dash/resources',
  group: 'resources',
}
