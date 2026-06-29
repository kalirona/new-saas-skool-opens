export const spacing = {
  /** Page / Section */
  page: { x: '16px', y: '24px' },
  section: { x: '24px', y: '32px' },
  card: { x: '20px', y: '20px' },

  /** Component internals */
  input: { x: '12px', y: '8px' },
  button: { x: '16px', y: '8px' },
  badge: { x: '8px', y: '2px' },
  table: { x: '12px', y: '10px' },

  /** Gap scale */
  gap: {
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '24px',
    '2xl': '32px',
  },

  /** Stack scale (vertical rhythm) */
  stack: {
    xs: '8px',
    sm: '12px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    '2xl': '48px',
  },
} as const
