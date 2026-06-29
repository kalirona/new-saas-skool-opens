/**
 * LearnHouse Design System — component standards.
 *
 * All components should use these patterns. Tailwind CSS v4 + shadcn/ui (New York)
 * provides the runtime; this file documents the conventions.
 *
 * ## Usage
 *
 * Prefer Tailwind utility classes over inline styles or JS objects:
 *
 *   ✅ `<button className="bg-primary text-primary-foreground rounded-lg px-4 py-2">`
 *   ❌ `<button style={{ background: 'black', color: 'white' }}>`
 *   ❌ `<button className="bg-black text-white">`
 *
 * For theme-consistency, use shadcn/ui components from `@/components/ui/` when available.
 * Only create custom components when the shadcn variants don't cover the use case.
 */

/* ───────────────────────────────────────────
 *  Button standards
 * ─────────────────────────────────────────── */

export const buttonStyles = {
  base: 'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0',
  variants: {
    default: 'bg-primary text-primary-foreground hover:bg-primary/90',
    secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
    destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
    outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
    ghost: 'hover:bg-accent hover:text-accent-foreground',
    link: 'text-primary underline-offset-4 hover:underline',
  },
  sizes: {
    sm: 'h-9 rounded-md px-3 text-xs',
    default: 'h-10 px-4 py-2',
    lg: 'h-11 rounded-md px-8',
    icon: 'h-10 w-10',
  },
} as const

/* ───────────────────────────────────────────
 *  Input / Textarea standards
 * ─────────────────────────────────────────── */

export const inputStyles = {
  base: 'flex w-full rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
} as const

export const textareaStyles = {
  base: 'flex min-h-[80px] w-full rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
} as const

/* ───────────────────────────────────────────
 *  Card standards
 * ─────────────────────────────────────────── */

export const cardStyles = {
  base: 'rounded-xl border bg-card text-card-foreground shadow-sm',
  header: 'flex flex-col space-y-1.5 p-6',
  title: 'text-lg font-semibold leading-none tracking-tight',
  description: 'text-sm text-muted-foreground',
  content: 'p-6 pt-0',
  footer: 'flex items-center p-6 pt-0',
} as const

/* ───────────────────────────────────────────
 *  Modal / Dialog standards
 * ─────────────────────────────────────────── */

export const modalStyles = {
  overlay: 'fixed inset-0 z-modal-backdrop bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0',
  content: 'fixed left-[50%] top-[50%] z-modal w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-xl',
  header: 'flex flex-col space-y-1.5 text-center sm:text-left',
  title: 'text-lg font-semibold leading-none tracking-tight',
  description: 'text-sm text-muted-foreground',
  footer: 'flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2',
} as const

/* ───────────────────────────────────────────
 *  Dropdown standards
 * ─────────────────────────────────────────── */

export const dropdownStyles = {
  content: 'z-popover min-w-[8rem] overflow-hidden rounded-lg border bg-popover p-1 text-popover-foreground shadow-md',
  item: 'relative flex cursor-default select-none items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50 [&>svg]:size-4 [&>svg]:shrink-0',
  separator: '-mx-1 my-1 h-px bg-border',
  label: 'px-2 py-1.5 text-sm font-semibold',
} as const

/* ───────────────────────────────────────────
 *  Table standards
 * ─────────────────────────────────────────── */

export const tableStyles = {
  wrapper: 'relative w-full overflow-auto',
  table: 'w-full caption-bottom text-sm',
  header: 'border-b bg-muted/50',
  headerCell: 'h-12 px-4 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0',
  body: '[&_tr:last-child]:border-0',
  row: 'border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted',
  cell: 'p-4 align-middle [&:has([role=checkbox])]:pr-0',
  footer: 'border-t bg-muted/50 font-medium [&>tr]:last:border-b-0',
  caption: 'mt-4 text-sm text-muted-foreground',
} as const

/* ───────────────────────────────────────────
 *  Badge standards
 * ─────────────────────────────────────────── */

export const badgeStyles = {
  base: 'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
  variants: {
    default: 'border-transparent bg-primary text-primary-foreground hover:bg-primary/80',
    secondary: 'border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80',
    destructive: 'border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80',
    outline: 'text-foreground',
  },
} as const

/* ───────────────────────────────────────────
 *  Tabs standards
 * ─────────────────────────────────────────── */

export const tabsStyles = {
  list: 'inline-flex h-10 items-center justify-center rounded-lg bg-muted p-1 text-muted-foreground',
  trigger: 'inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm',
  content: 'mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
} as const
