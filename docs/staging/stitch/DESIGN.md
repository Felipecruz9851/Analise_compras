---
name: Emerald Procurement Analytics
colors:
  surface: '#f8f9ff'
  surface-dim: '#ccdbf3'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e6eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d5e3fc'
  on-surface: '#0d1c2e'
  on-surface-variant: '#3f4941'
  inverse-surface: '#233144'
  inverse-on-surface: '#eaf1ff'
  outline: '#6f7a70'
  outline-variant: '#becabe'
  surface-tint: '#006d3d'
  primary: '#006a3b'
  on-primary: '#ffffff'
  primary-container: '#268451'
  on-primary-container: '#f6fff4'
  inverse-primary: '#7ed99e'
  secondary: '#006d3d'
  on-secondary: '#ffffff'
  secondary-container: '#86fab0'
  on-secondary-container: '#007441'
  tertiary: '#005cab'
  on-tertiary: '#ffffff'
  tertiary-container: '#1775d1'
  on-tertiary-container: '#fefcff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#9af6b8'
  primary-fixed-dim: '#7ed99e'
  on-primary-fixed: '#00210f'
  on-primary-fixed-variant: '#00522d'
  secondary-fixed: '#86fab0'
  secondary-fixed-dim: '#69dd96'
  on-secondary-fixed: '#00210f'
  on-secondary-fixed-variant: '#00522d'
  tertiary-fixed: '#d4e3ff'
  tertiary-fixed-dim: '#a5c8ff'
  on-tertiary-fixed: '#001c3a'
  on-tertiary-fixed-variant: '#004786'
  background: '#f8f9ff'
  on-background: '#0d1c2e'
  surface-variant: '#d5e3fc'
  surface-canvas: '#f1f5f9'
  surface-card: '#ffffff'
  surface-subtle: '#f8fafc'
  surface-row-alt: '#fafbfd'
  border-subtle: '#e2e8f0'
  border-strong: '#cbd5e1'
  cell-highlight-bg: '#d4edda'
  cell-highlight-text: '#155724'
  cell-edited-bg: '#fff3e0'
  cell-edited-border: '#ff9800'
  cell-edited-text: '#c25e00'
  status-danger: '#dc3545'
  status-danger-dark: '#c0392b'
  sparkline-blue: '#1976d2'
typography:
  headline-xl:
    fontFamily: Manrope
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Manrope
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Manrope
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Manrope
    fontSize: 15px
    fontWeight: '600'
    lineHeight: 20px
  body-lg:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
  body-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-numeric:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: -0.02em
  label-numeric-bold:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
  label-micro:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.02em
  label-action:
    fontFamily: Inter
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 12px
    letterSpacing: 0.04em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-compact: 0.5rem
  margin: 1.5rem
  margin-dense: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
---

## Brand & Style

This design system targets procurement officers, supply chain directors, and financial controllers who operate in data-intensive enterprise environments. The aesthetic pairs high-density analytical utility with contemporary corporate refinement, balancing operational speed against executive clarity. 

The visual style is **Corporate Modern with High-Density Precision**:
- Surfaces employ subtle slate and cool graphite neutrals, creating a calm backdrop that allows vital financial figures and operational thresholds to communicate instantly.
- The emerald and sea-green palette projects stability, liquidity, and operational health, while deliberate warning accents signal manual modifications and purchase anomalies.
- Interfaces embrace strict visual hygiene: structured grid borders, tabular numerical alignments, compact interactive controls, and tactile state indicators that make complex decision matrices effortless to audit.

## Colors

The chromatic system is anchored by deep SeaGreen (`#2e8b57`) and vibrant MediumSeaGreen (`#3cb371`), representing procurement authorization, positive margins, and primary interactive targets. 

Data visualization and analytical anchors leverage Material Blue (`#1976d2`) for neutral data indicators, sparkline anchors, and active focus rings. Grayscale tones are derived from slate and cool gray families, maintaining high legibility while reducing eye fatigue during extended analytical sessions.

### Functional State Rules
- **Editable Modified State**: Cells altered from standard ERP values take on `cell-edited-bg` (`#fff3e0`) with an inset border and text token `cell-edited-border` (`#ff9800`) to highlight manual procurement overrides.
- **Audit Highlights**: Columns involving critical fiscal decision factors utilize `cell-highlight-bg` (`#d4edda`) and `cell-highlight-text` (`#155724`).
- **Destructive/Critical Actions**: Batch deletions and reset actions utilize `status-danger` (`#dc3545`) through `status-danger-dark` (`#c0392b`).

## Typography

The type scale combines **Manrope** for authoritative, balanced sectioning and summaries, **Inter** for high-density legibility across labels and table data, and **JetBrains Mono** for numerical values, financial metrics, currency fields, and data charts.

### Numerical Typography Guidance
- All monetary, volumetric, percentage, and tabular numeric fields must utilize `label-numeric` or `label-numeric-bold`. Enable tabular figures (`font-variant-numeric: tabular-nums; lining-nums;`) across all `td` containers to ensure clean column scanning.
- Micro action labels on table column controls utilize uppercase transforms with increased tracking (`letter-spacing: 0.04em`) to remain sharp at small sizes.

## Layout & Spacing

The system utilizes a 12-column responsive fluid grid structured for dense information architecture. The content area expands contextually to provide maximum horizontal canvas for wide purchasing ledgers and multi-metric analytics.

### Form Factor Behavior
- **Desktop (1200px+)**: Multi-column dashboard with a persistent or collapsible 280px operational sidebar, sticky two-tier table headers, and persistent contextual filter bars. Gutters settle at `1rem` with standard container padding of `1.5rem`.
- **Tablet / Laptop (768px - 1199px)**: Sidebar docks into an overlay or icon-only navigation bar. Table containers become horizontally scrollable with sticky frozen columns for primary identifier tags.
- **Mobile (< 768px)**: Dense tabular matrices collapse into stacked metric card components, with primary analytical summaries surfaced as swipeable carousels.

### Dense Data Grid Spacing Rhythm
- **Table Cells**: Header cells use `0.5rem 0.625rem` padding; data cells use `0.375rem 0.5rem` to prioritize visibility of 20+ rows without vertical scrolling.
- **Sparkline Containers**: Enforce a strict minimum width of `210px` and inline height of `36px` to maintain consistent row heights across data rows.

## Elevation & Depth

Visual hierarchy uses crisp, structured boundaries complemented by selective drop shadows and translucent layering. Deep elevation is reserved strictly for operational interruptions (such as bulk export drawers and modal overlays), preventing background shadows from obscuring numerical legibility.

### Surface Tiers & Overlays
- **Tier 0 (Base Canvas)**: Background rendered in `surface-canvas` (`#f1f5f9`), grounding elevated work panels.
- **Tier 1 (Flat Cards & Panels)**: Content wrappers and table shells use clean white surfaces framed by `1px solid var(--border-subtle)` (`#e2e8f0`). No shadows are applied here, keeping table scan lines crisp.
- **Tier 2 (Floating Controls & Sticky Elements)**: Sticky column headers and top-level filter ribbons employ `0 2px 8px rgba(0, 0, 0, 0.06)` with a solid white background, preventing background text bleed during scrolling.
- **Tier 3 (Dropdowns, Menus & Action Tooltips)**: Filter popouts and column sorters use `0 8px 24px rgba(15, 23, 42, 0.12)` alongside hairline borders.
- **Tier 4 (Critical Overlays & Modals)**: Export dialogues and batch processing dialogs hover over a `rgba(15, 23, 42, 0.6)` backdrop with `backdrop-filter: blur(4px)`. The modal container uses `0 20px 48px rgba(0, 0, 0, 0.22)`.

## Shapes

The design uses **Soft (Level 1)** shaping to reinforce structural discipline, screen density, and enterprise reliability. 

- **Base Components**: Input fields, table filter buttons, batch selector tags, and table chips use `0.25rem` (4px) radii.
- **Cards & Data Shelves**: Dashboard metric panels, table wrappers, and sidebar summary boxes use `0.375rem` to `0.5rem` (6px to 8px) radii.
- **Micro-Action Controls**: Table pagination triggers, row revert buttons, and close buttons use full circular geometry (`50%`) to create unambiguous, tap-safe micro targets.

## Components

### Buttons & Action Triggers
- **Primary Action**: Gradient fill transitioning from `#2e8b57` to `#3cb371`, white text (`#ffffff`), `0.25rem` border-radius, font weight 600. On hover, apply `translateY(-1px)` and a subtle ambient glow `0 4px 12px rgba(46, 139, 87, 0.3)`.
- **Secondary / Action Ghost**: Translucent surface with `border: 1px solid var(--border-strong)`, color `neutral_color_hex`. On hover, background transitions to `var(--surface-subtle)`.
- **Destructive**: Dual-tone red gradient (`#dc3545` to `#c0392b`), text white, used exclusively for bulk deletion or hard reset flows.
- **Micro Row Actions (Revert / Download)**: Sized at 24px x 24px with centered glyphs. The cell revert button (`↩`) uses a circular shape with `#ff9800` background and white icon, displaying only when `cell-edited` is true.

### Inputs & Column Filters
- **Filter Fields**: Height constrained to 28px in table sub-headers. Background `#ffffff`, border `1px solid var(--border-subtle)`, text `12px Inter`. Focus state introduces an inner outline halo `0 0 0 2px rgba(25, 118, 210, 0.25)` and border color `#1976d2`.
- **Column Header Sort Buttons**: Integrated directly beside header labels; active sort displays directional arrows with `#2e8b57` chromatic fill.

### Data Tables & Editable Cells
- **Table Structure**: Sticky first row headers at `z-index: 10`, column borders `1px solid var(--border-subtle)`, alternating striping using `surface-row-alt` (`#fafbfd`).
- **Interactive Editable Cell**: Default state has no heavy visual chrome. On cursor hover, apply `box-shadow: inset 0 0 0 1.5px #3cb371` with subtle background `#e8f5e9`. When clicked/active, apply `box-shadow: inset 0 0 0 2px #1976d2` and background `#ffffff`.
- **Dirty / Edited Cell**: Upon value alteration, cell background transitions to `cell-edited-bg` (`#fff3e0`), displays an inset border in `cell-edited-border` (`#ff9800`), and embeds the floating micro revert button on the cell's right boundary.

### Sparklines & Metrics
- Inline line plots must be rendered with an tension spline of `0.3`, stroke width `1.5px`, line color `#1976d2`, and circular anchor points of `3px`. Floating labels display numeric values using `JetBrains Mono` at `11px` bold with an offset of `4px` above data peaks.

### Collapsible Analytical Sidebar
- Styled in deep emerald gradient (`#2e8b57` to `#1e5d3a`) with white typographic contrast. Metric tiles within the sidebar use stacked translucency (`background: rgba(255, 255, 255, 0.12)`, `border: 1px solid rgba(255, 255, 255, 0.25)`), providing glassmorphic depth while preserving scannability for aggregate figures.