import { Mic } from 'lucide-react'
import type { SearchMeta } from '@/lib/dashboard-search/types'

export const searchMeta: SearchMeta = {
  id: 'dash.podcasts',
  titleKey: 'podcasts.podcasts',
  descriptionKey: 'dashboard.search.entries.podcasts.description',
  keywordsKey: 'dashboard.search.entries.podcasts.keywords',
  icon: Mic,
  href: '/dash/podcasts',
  group: 'navigation',
  featureKey: 'podcasts',
}
