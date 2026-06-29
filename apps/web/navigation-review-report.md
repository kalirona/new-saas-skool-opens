# Navigation Review Report — Phase 2

## 1. Overview
- **Analysis date:** 2026-06-25
- **Total navigation components:** 4 primary components (DashLeftMenu, DashMobileMenu, OrgMenu, OrgMenuLinks) + 1 shared data module (dashboard-menu-items.ts)
- **Routing structure:** Two parallel route groups under `/orgs/[orgslug]`:
  - `(withmenu)/` — Public-facing pages with top navigation bar (OrgMenu)
  - `dash/` — Admin dashboard pages with sidebar (DashLeftMenu) on desktop or floating pill (DashMobileMenu) on mobile

## 2. Navigation Components

### DashLeftMenu (Desktop Sidebar)
- **File:** `components/Dashboard/Menus/DashLeftMenu.tsx`
- **Lines:** 489
- **Features:** collapsible sidebar with localStorage persistence (lines 56–68), dark mode (`bg-[#0f0f10]`), hover menus for language/help/user sections, `TooltipProvider` for collapsed tooltips, `AdminAuthorization` wrapper (line 159) restricting to admin users
- **Menu categories found:** Main navigation (8 items), Language switcher, Help menu (docs/website/discord/feedback), Notifications bell, User menu (settings/purchases/logout)
- **Actual items rendered:**
  1. Home (`/dash`)
  2. Communities (`/dash/communities`) — feature-flagged by `isEnabled('communities')` (line 88, line 168)
  3. Courses (`/dash/courses`)
  4. Resources (`/dash/resources`) — also matches `/dash/library`, `/dash/boards`, `/dash/playgrounds`, `/dash/podcasts` via `isActivePath` (line 189)
  5. Calendar (`/dash/calendar`)
  6. Members (`/dash/users/settings/users`)
  7. Analytics (`/dash/analytics`)
  8. Settings (`/dash/org/settings/general`)
- **Notes on organization:** Items defined inline rather than from a shared config source. The `isActivePath` function (lines 47–52) checks exact match or prefix match — Resources link shows active for 5 different route prefixes. All items wrapped in a single `AdminAuthorization` block — no per-item permission checks.

### DashMobileMenu (Mobile Navigation)
- **File:** `components/Dashboard/Menus/DashMobileMenu.tsx`
- **Lines:** 334
- **Features:** floating pill + slide-up drawer, `AnimatePresence` and Framer Motion spring animations (line 147), `createPortal` to `document.body`, progressive icon reveal via min-width breakpoints (lines 86–94), language picker with expand/collapse, feedback modal, command palette search trigger
- **Items rendered:**
  - **Floating pill** (progressive reveal by viewport width):
    1. Home (always)
    2. Communities (`min-[340px]`) — feature-flagged
    3. Courses (`min-[390px]`)
    4. Resources (`min-[430px]`)
    5. Calendar (`min-[470px]`)
    6. Members (`min-[510px]`)
    7. Analytics (`min-[630px]`)
    8. Settings (`min-[670px]`)
    - Plus Search and Menu toggle buttons
  - **Slide-up drawer** (full list):
    - Same 8 items + Account settings, Language picker with sub-languages, Documentation link, Discord link, Feedback button, User footer with logout
- **Breakpoint:** 1024px — determined by `useMediaQuery('(max-width: 1024px)')` in `ClientAdminLayout.tsx:21`, which conditionally renders `DashMobileMenu` vs `DashLeftMenu`
- **Notes:** `isActive` logic (lines 50–53) mirrors `DashLeftMenu`'s `isActivePath`. The drawer has a max-height of `52vh` (line 184) with `overflow-y-auto`. "Analytics" label at line 191 uses hardcoded string `"Analytics"` instead of `t()` translation — inconsistent with other items.

### DashAdminMenu
- **File:** `components/Dashboard/Menus/DashAdminMenu.tsx` — **does not exist**

### OrgMenuLinks (Shared Link Definitions)
- **File:** `components/Objects/Menus/OrgMenuLinks.tsx`
- **Lines:** 89
- **Links exported:**
  - `BUILTIN` record (lines 13–20) defines 6 feature types:
    - courses → `/courses` (feature: courses)
    - library → `/library` (feature: folders)
    - podcasts → `/podcasts` (feature: podcasts)
    - communities → `/communities` (feature: communities)
    - playgrounds → `/playgrounds` (feature: playgrounds)
    - store → `/store` (feature: payments)
  - Default order: `['courses', 'library', 'podcasts', 'communities', 'playgrounds', 'store']` (line 23)
  - Support for custom menu items from org config (`customization.menu.items` or `general.menu.items` at lines 33–34)
- **Feature flags used:** `isEnabled(meta.feature)` at line 58 — each builtin item is gated by `resolved_features`. Also supports custom items with no feature gating (only `enabled` flag and URL check).

### lib/dashboard-menu-items.ts (Shared Dashboard Menu Config)
- **File:** `lib/dashboard-menu-items.ts`
- **Lines:** 62
- **Exported interface:** `DashboardMenuItem` with fields: id, href, icon, labelKey, featureKey (optional), defaultDisabled (optional)
- **Items defined:**
  1. home (`/dash`) — no featureKey
  2. community (`/dash/communities`) — featureKey: 'communities'
  3. courses (`/dash/courses`) — no featureKey
  4. resources (`/dash/resources`) — no featureKey
  5. calendar (`/dash/calendar`) — no featureKey
  6. members (`/dash/users/settings/users`) — no featureKey
  7. analytics (`/dash/analytics`) — no featureKey
  8. settings (`/dash/org/settings/general`) — no featureKey
- **Usage:** Used by `OrgMenu.tsx` (line 32) for the Dashboard dropdown menu. **Not** used by `DashLeftMenu` or `DashMobileMenu` — those define items inline.

## 3. Route Structure
### Public Routes (with menu) — `apps/web/app/orgs/[orgslug]/(withmenu)/`
| Route | Description |
|---|---|
| `/` | Home page |
| `/account/[subpage]` | User account settings |
| `/boards` | Boards listing |
| `/certificates/[uuid]` | Certificate view |
| `/communities` | Communities listing |
| `/community/[communityuuid]` | Individual community |
| `/copilot` | AI Copilot chat |
| `/course/[courseuuid]` | Individual course |
| `/courses` | Courses listing |
| `/library` | Library (folders) |
| `/library/folder/[...]` | Library folder contents |
| `/playground/[playgrounduuid]` | Individual playground |
| `/playgrounds` | Playgrounds listing |
| `/podcast/[podcastuuid]` | Individual podcast |
| `/podcasts` | Podcasts listing |
| `/search` | Search results |
| `/store` | Store / offerings |
| `/store/offers/` | Store offers detail |
| `/trail` | User learning progress trail |
| `/user/[username]` | User profile |

### Dashboard Routes — `apps/web/app/orgs/[orgslug]/dash/`
| Route | Description | In Sidebar? |
|---|---|---|
| `/dash` | Dashboard home | Yes |
| `/dash/analytics` | Analytics | Yes |
| `/dash/assignments` | Assignments | **No** |
| `/dash/assignments/[assignmentuuid]` | Assignment detail | No |
| `/dash/boards` | Boards management | **No** (but active state matches Resources) |
| `/dash/boards/[boarduuid]` | Board detail | No |
| `/dash/calendar` | Calendar | Yes |
| `/dash/communities` | Communities management | Yes (feature-flagged) |
| `/dash/communities/[communityuuid]` | Community detail | No |
| `/dash/courses` | Courses management | Yes |
| `/dash/courses/course/[...]` | Course detail/edit | No |
| `/dash/courses/migrate/` | Course migration | No |
| `/dash/library` | Library management | **No** (but active state matches Resources) |
| `/dash/library/folder/[...]` | Folder contents | No |
| `/dash/org/settings/[subpage]` | Org settings | Yes (points to general) |
| `/dash/payments/[subpage]` | Payments/ billing | **No** |
| `/dash/playgrounds` | Playgrounds management | **No** (but active state matches Resources) |
| `/dash/podcasts` | Podcasts management | **No** (but active state matches Resources) |
| `/dash/podcasts/podcast/[...]` | Podcast detail | No |
| `/dash/resources` | Resources | Yes |
| `/dash/users/settings/[subpage]` | User management settings | Yes |

## 4. Feature Flag Coverage
List of navigation items protected by feature flags (`resolved_features` from org API config):

| Feature Key | Items Gated | Location |
|---|---|---|
| `communities` | Communities link in DashLeftMenu (line 168), DashMobileMenu pill + panel (lines 87, 186), OrgMenuLinks BUILTIN, dashboard-menu-items.ts (line 24) | `DashLeftMenu.tsx:168`, `DashMobileMenu.tsx:87`, `OrgMenuLinks.tsx:58`, `dashboard-menu-items.ts:24` |
| `boards` | Boards icon button in OrgMenu (line 196) | `OrgMenu.tsx:196` |
| `ai` | AI Copilot button in OrgMenu (line 219) | `OrgMenu.tsx:219` |
| `courses` | Courses link in OrgMenuLinks (line 14) | `OrgMenuLinks.tsx:14` |
| `folders` | Library link in OrgMenuLinks (line 15) | `OrgMenuLinks.tsx:15` |
| `podcasts` | Podcasts link in OrgMenuLinks (line 16) | `OrgMenuLinks.tsx:16` |
| `playgrounds` | Playgrounds link in OrgMenuLinks (line 17) | `OrgMenuLinks.tsx:17` |
| `payments` | Store link in OrgMenuLinks (line 19) | `OrgMenuLinks.tsx:19` |

Items **without** feature flag protection:
- Home, Courses, Resources, Calendar, Members, Analytics, Settings in DashLeftMenu/DashMobileMenu (gated only by `AdminAuthorization` wrapper, not by individual feature flags)
- Assignments (`/dash/assignments`) — no menu entry at all
- Boards management (`/dash/boards`) — no menu entry at all
- Payments (`/dash/payments`) — no menu entry at all

## 5. Issues Found

### Duplicate / Orphan Routes
- **Dashboard routes without sidebar links:** `/dash/assignments`, `/dash/boards`, `/dash/payments`, `/dash/library` (separate page), `/dash/playgrounds`, `/dash/podcasts` — these routes exist but have no dedicated menu item. Some (library, boards, playgrounds, podcasts) are only reachable via the Resources link's active state; others (assignments, payments) have no menu link at all.
- **Resources link conflates 5 routes:** `DashLeftMenu.tsx:189` uses `isActivePath('/dash/resources') || isActivePath('/dash/library') || isActivePath('/dash/boards') || isActivePath('/dash/playgrounds') || isActivePath('/dash/podcasts')` — a single "Resources" menu link covers 5 distinct top-level dashboard sections.

### Missing Feature Flags
- **Courses, Resources, Calendar, Members, Analytics, Settings** in DashLeftMenu/DashMobileMenu have no individual feature flag gating. They are only wrapped by the blanket `AdminAuthorization` component (line 159 of DashLeftMenu) which checks admin rights, not per-feature availability.
- **Payments** route exists at `/dash/payments/[subpage]` but has no menu entry and no feature flag in the dashboard menu definition.

### Hardcoded Text/Links
- `DashMobileMenu.tsx:191` — `label="Analytics"` is hardcoded in English instead of using `t('common.analytics')` like the desktop version.
- `DashMobileMenu.tsx:85` — `aria-label="Home"` hardcoded instead of using `t('common.home')`.
- `OrgMenu.tsx:207,211` — Boards button `aria-label` and tooltip use hardcoded `"Boards"` instead of `t()`.

### Accessibility Issues
- **OrgMenu.tsx line 149-160:** `<img>` inside `<Link>` has empty `alt=""` for the org logo when `org?.logo_image` is set — this is acceptable as decorative if the link text conveys the purpose, but the link wraps only the image with no additional accessible text.
- **DashLeftMenu/DashMobileMenu:** Custom scrollbar hiding in drawer (`[&::-webkit-scrollbar]:hidden` at DashMobileMenu.tsx:184) may hide scroll indicators from keyboard users. The HoverMenu content uses `[&::-webkit-scrollbar]:hidden` at DashLeftMenu.tsx:248 similarly.
- **`aria-current="page"`** is correctly set on active links in DashLeftMenu (line 462) and DashMobileMenu (line 317).

### Performance Concerns
- **DashLeftMenu re-renders:** `isActivePath` is called on every render for each menu link (8 times) and recomputes pathname matching — acceptable but could be memoized.
- **DashMobileMenu portal:** `createPortal` to `document.body` at line 274 — renders the full menu component tree on every render even when closed (though returns null early if not mounted).
- **OrgMenu dashboard dropdown:** Fetches RAG chat sessions only when dropdown opens (`enabled: isOpen` at `OrgMenu.tsx:436`), which is a good pattern for lazy loading.

### Code Duplication
- **Inline menu definitions:** `DashLeftMenu.tsx` and `DashMobileMenu.tsx` both define their menu items inline (JSX) rather than consuming the shared `DASHBOARD_MENU_ITEMS` array from `lib/dashboard-menu-items.ts`. The desktop and mobile menus have slightly different item structures but share the same logical items.
- **i18n key "common.home"** is used in both DashLeftMenu and DashMobileMenu; the mobile menu also hardcodes `t('communities.title')` inconsistently with desktop.
- **`isActive` logic** duplicated exactly between DashLeftMenu (`isActivePath`, lines 47-52) and DashMobileMenu (`isActive`, lines 50-53).

## 6. Recommendations

### Add Feature Flag for
- Courses, Resources, Calendar, Members, Analytics, Settings in `DashLeftMenu` and `DashMobileMenu` — consider adding `featureKey` support and gating by `resolved_features` like Communities already does
- Payments menu item — add a menu entry gated by `config?.payments?.is_active` or `resolved_features.payments`

### Consolidate
- **Menu definitions:** Migrate `DashLeftMenu` and `DashMobileMenu` to use the shared `DASHBOARD_MENU_ITEMS` array from `lib/dashboard-menu-items.ts` like `OrgMenu.tsx` already does. This would reduce duplication and ensure consistency across desktop, mobile, and public dashboard dropdown menus.
- **Active-path logic:** Extract `isActive`/`isActivePath` into a shared utility function.
- **Resources catch-all:** Either promote boards, library, playgrounds, and podcasts to their own sidebar items or add a sub-menu under Resources.

### Improve
- **Hardcoded strings:** Replace `"Analytics"` (DashMobileMenu.tsx:191) and `"Home"` (DashMobileMenu.tsx:85) with `t()` calls. Replace `"Boards"` (OrgMenu.tsx:207,211) with `t()`.
- **Feature flag consistency:** Align dashboard menu gating with the pattern used in `OrgMenuLinks.tsx` — use `resolved_features` uniformly rather than a mix of `AdminAuthorization` and inline feature checks.
- **Scrollbar accessibility:** Reconsider `webkit-scrollbar:hidden` on menu panels — either use standard browser scrollbars or ensure keyboard accessibility with `overscroll-behavior`.

## 7. Summary
- **Overall navigation health:** Good structural foundation with clear separation between public (`(withmenu)`) and admin (`dash/`) route groups. The feature flag system (`resolved_features`) is used correctly in `OrgMenuLinks.tsx` and for the Communities link, but is not consistently applied to all dashboard sidebar items. The main area for improvement is reducing code duplication between `DashLeftMenu` and `DashMobileMenu`, which define nearly identical menu items in JSX rather than consuming the shared `DASHBOARD_MENU_ITEMS` config. Several dashboard routes exist without sidebar entries (assignments, payments, boards, library), suggesting incomplete menu coverage. The i18n coverage is excellent overall, with only 3 identified instances of hardcoded strings.
