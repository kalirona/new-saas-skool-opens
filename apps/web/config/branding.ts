import { getConfig } from '@services/config/config'

export const APP_NAME = getConfig('NEXT_PUBLIC_BRAND_NAME', 'LearnHouse')
export const APP_DESCRIPTION = getConfig('NEXT_PUBLIC_BRAND_DESCRIPTION', 'LearnHouse - Open source learning platform')

export const APP_COLORS = {
  primary: getConfig('NEXT_PUBLIC_BRAND_PRIMARY_COLOR', '#000000'),
  secondary: getConfig('NEXT_PUBLIC_BRAND_SECONDARY_COLOR', '#6b7280'),
}

export const APP_LOGOS = {
  svg: getConfig('NEXT_PUBLIC_BRAND_LOGO_SVG', '/lrn.svg'),
  dash: getConfig('NEXT_PUBLIC_BRAND_LOGO_DASH', '/lrn-dash.svg'),
  text: getConfig('NEXT_PUBLIC_BRAND_LOGO_TEXT', '/lrn-text.svg'),
  icon: getConfig('NEXT_PUBLIC_BRAND_LOGO_ICON', '/lrn.svg'),
  bigIcon: getConfig('NEXT_PUBLIC_BRAND_LOGO_BIG', '/learnhouse_bigicon.png'),
  favicon: getConfig('NEXT_PUBLIC_BRAND_FAVICON', '/favicon.ico'),
  aiIcon: getConfig('NEXT_PUBLIC_BRAND_AI_ICON', '/learnhouse_ai_simple.png'),
  aiLogoBlack: getConfig('NEXT_PUBLIC_BRAND_AI_LOGO_BLACK', '/learnhouse_ai_black_logo.png'),
  aiLogoColored: getConfig('NEXT_PUBLIC_BRAND_AI_LOGO_COLORED', '/learnhouse_ai_simple_colored.png'),
}

export const APP_SEO = {
  title: getConfig('NEXT_PUBLIC_BRAND_SEO_TITLE', 'LearnHouse'),
  description: getConfig('NEXT_PUBLIC_BRAND_SEO_DESCRIPTION', 'LearnHouse - Open source learning platform'),
  dashboardTitle: getConfig('NEXT_PUBLIC_BRAND_DASHBOARD_TITLE', 'Dashboard'),
  adminTitle: getConfig('NEXT_PUBLIC_BRAND_ADMIN_TITLE', 'Admin'),
  defaultOgImage: getConfig('NEXT_PUBLIC_BRAND_OG_IMAGE', '/learnhouse_bigicon_1.png'),
}

export const APP_LINKS = {
  website: getConfig('NEXT_PUBLIC_BRAND_WEBSITE_URL', 'https://learnhouse.app'),
  docs: getConfig('NEXT_PUBLIC_BRAND_DOCS_URL', 'https://docs.learnhouse.app'),
  discord: getConfig('NEXT_PUBLIC_BRAND_DISCORD_URL', 'https://discord.gg/learnhouse'),
  university: getConfig('NEXT_PUBLIC_BRAND_UNIVERSITY_URL', 'https://university.learnhouse.io'),
  classroom: getConfig('NEXT_PUBLIC_BRAND_CLASSROOM_URL', 'https://classroom.learnhouse.io'),
}

export function buildPageTitle(...parts: (string | undefined | null)[]): string {
  const nonEmpty = parts.filter(Boolean) as string[]
  if (nonEmpty.length === 0) return APP_SEO.title
  return [...nonEmpty, APP_SEO.title].join(' — ')
}

export function getBrandLogo(logoKey: keyof typeof APP_LOGOS): string {
  return APP_LOGOS[logoKey]
}
