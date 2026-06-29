'use client'

import React from 'react'
import { LucideIcon } from 'lucide-react'

export const ICON_SIZES = {
  xs: 12,
  sm: 14,
  md: 16,
  lg: 18,
  xl: 20,
  '2xl': 24,
  '3xl': 32,
  '4xl': 40,
  '5xl': 48,
  '6xl': 64,
} as const

export type IconSize = keyof typeof ICON_SIZES

export function resolveIconSize(size: IconSize | number): number {
  if (typeof size === 'number') return size
  return ICON_SIZES[size] ?? ICON_SIZES.md
}

interface IconProps extends React.ComponentPropsWithoutRef<'svg'> {
  icon: LucideIcon
  size?: IconSize | number
  className?: string
}

export default function Icon({
  icon: LucideIconComponent,
  size = 'md',
  className = '',
  ...props
}: IconProps) {
  const pixelSize = resolveIconSize(size)
  return <LucideIconComponent size={pixelSize} className={className} {...props} />
}

export { ICON_SIZES as ICON_SIZE_MAP }
