export const typography = {
  fontFamily: {
    sans: "'Wix Madefor Text', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif",
    mono: "'JetBrainsMono', 'SF Mono', Monaco, 'Cascadia Code', 'Consolas', monospace",
  },
  fontWeight: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },
  fontSize: {
    xs: ['0.75rem', { lineHeight: '1rem' }],
    sm: ['0.8125rem', { lineHeight: '1.25rem' }],
    base: ['0.875rem', { lineHeight: '1.5rem' }],
    lg: ['1rem', { lineHeight: '1.75rem' }],
    xl: ['1.125rem', { lineHeight: '1.75rem' }],
    '2xl': ['1.25rem', { lineHeight: '1.75rem' }],
    '3xl': ['1.5rem', { lineHeight: '2rem' }],
    '4xl': ['1.875rem', { lineHeight: '2.25rem' }],
  },
  letterSpacing: {
    tight: '-0.02em',
    normal: '0em',
    wide: '0.05em',
  },
} as const
