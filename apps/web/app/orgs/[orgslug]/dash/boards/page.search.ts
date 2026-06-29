import { Presentation } from 'lucide-react'
import type { SearchMeta } from '@/lib/dashboard-search/types'

export const searchMeta: SearchMeta = {
  id: 'dash.boards',
  titleKey: 'common.boards',
  descriptionKey: 'dashboard.search.entries.boards.description',
  keywordsKey: 'dashboard.search.entries.boards.keywords',
  icon: Presentation,
  href: '/dash/boards',
  group: 'navigation',
  featureKey: 'boards',
  featureDefaultDisabled: true,
}
