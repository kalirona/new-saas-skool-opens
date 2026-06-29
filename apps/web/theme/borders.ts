export const borders = {
  radius: {
    none: '0',
    sm: 'calc(var(--radius) - 4px)',
    md: 'calc(var(--radius) - 2px)',
    lg: 'var(--radius)',
    xl: 'calc(var(--radius) + 4px)',
    full: '9999px',
  },
  width: {
    none: '0',
    thin: '1px',
    medium: '2px',
  },
} as const
