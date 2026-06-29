import { Link, Globe, Home, BookOpen, GraduationCap, Folder, Headphones, MessageCircle, Box, ShoppingBag, Star, Heart, Calendar, Users, Trophy, Lightbulb, FileText, Video, MapPin, HelpCircle, Gift, Rocket, Zap, Newspaper } from 'lucide-react'

// Curated icon set selectable for custom menu links. Keyed by a stable name
// stored on the menu item (item.icon).
export const MENU_ICONS: Record<string, any> = {
  Link, Globe, Home, BookOpen, GraduationCap, Folder, Headphones,
  MessageCircle, Box, ShoppingBag, Star, Heart, Calendar, Newspaper, Users,
  Trophy, Lightbulb, FileText, Video, MapPin, HelpCircle, Gift, Rocket, Zap,
}

export const MENU_ICON_NAMES = Object.keys(MENU_ICONS)
export const DEFAULT_MENU_ICON = 'Link'

export function menuIcon(name?: string) {
  return (name && MENU_ICONS[name]) || MENU_ICONS[DEFAULT_MENU_ICON]
}
