# Talentra — UI & Design System Specification

## 1. Design Philosophy: Superset-Inspired Clarity

Talentra’s user interface is designed to emulate modern enterprise recruitment and campus placement systems (inspired by the information architecture, density, and clarity of platforms like Superset).

### Core Design Principles:
1. **High Information Density**: Screen real estate is optimized for actionable data — candidates, jobs, pipeline status, and placement analytics — without unnecessary whitespace.
2. **Restrained, Professional Visuals**: No decorative pastel gradients, oversized rounded corners, or AI-generated card bloat. Clean borders, subtle shadows, and crisp lines convey institutional trust.
3. **Light Mode as Default**: High-contrast, clean white/slate backgrounds optimized for daytime institutional use, with seamless dark mode switching for evening sessions.
4. **Standard Blinking Caret Fidelity**: Standard blinking text carets (`caret-primary`) are strictly preserved exclusively in text-entry fields (`input`, `textarea`). Non-editable badges, labels, and statistics never display pseudo-carets.
5. **Workflow-Oriented Layouts**: Every screen centers on a clear user workflow — whether screening 200 candidates, reviewing campus placement drive slots, or reconciling payment invoices.

---

## 2. Color System & Theme Tokens

The design system utilizes HSL-based CSS custom properties defined in `frontend/src/app/globals.css`.

### 2.1. Light Mode Tokens (Default)
```css
:root {
  --background: 210 20% 98%;       /* Soft slate background #f8fafc */
  --foreground: 222 47% 11%;       /* Deep slate ink #0f172a */
  --card: 0 0% 100%;               /* Crisp pure white */
  --card-foreground: 222 47% 11%;
  --popover: 0 0% 100%;
  --popover-foreground: 222 47% 11%;
  --primary: 221 83% 53%;          /* Enterprise royal blue #2563eb */
  --primary-foreground: 210 40% 98%;
  --secondary: 210 40% 96.1%;      /* Muted slate tint */
  --secondary-foreground: 222 47% 11.2%;
  --muted: 210 40% 96.1%;
  --muted-foreground: 215 16% 47%; /* Subdued body text #64748b */
  --accent: 210 40% 96.1%;
  --accent-foreground: 222 47% 11.2%;
  --destructive: 0 84.2% 60.2%;    /* High-contrast alert crimson */
  --destructive-foreground: 210 40% 98%;
  --border: 214 32% 91%;           /* Crisp border line #e2e8f0 */
  --input: 214 32% 91%;
  --ring: 221 83% 53%;             /* Accessible focus indicator */
  --radius: 0.375rem;              /* Subdued enterprise radius */
}
```

### 2.2. Dark Mode Tokens
```css
.dark {
  --background: 224 71% 4%;        /* Deep obsidian #020617 */
  --foreground: 210 40% 98%;       /* Clean light text */
  --card: 222 47% 11%;             /* Elevated slate card */
  --card-foreground: 210 40% 98%;
  --popover: 222 47% 11%;
  --popover-foreground: 210 40% 98%;
  --primary: 217 91% 60%;          /* Vibrant sapphire */
  --primary-foreground: 222 47% 11.2%;
  --secondary: 217 33% 17%;
  --secondary-foreground: 210 40% 98%;
  --muted: 217 33% 17%;
  --muted-foreground: 215 20% 65%;
  --accent: 217 33% 17%;
  --accent-foreground: 210 40% 98%;
  --destructive: 0 62.8% 30.6%;
  --destructive-foreground: 210 40% 98%;
  --border: 217 33% 17%;
  --input: 217 33% 17%;
  --ring: 224 76% 48%;
}
```

---

## 3. Typography Hierarchy

The typography stack relies on clean, modern sans-serif fonts: `Inter`, `-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `Roboto`, `sans-serif`.

| Token / Class | Size | Line Height | Weight | Typical Usage |
|:---|:---|:---|:---|:---|
| `text-2xl` | 24px (1.5rem) | 2rem | Semibold (600) | Portal Page Titles, Major Section Headers |
| `text-xl` | 20px (1.25rem) | 1.75rem | Semibold (600) | Card Headers, Modal Titles |
| `text-lg` | 18px (1.125rem)| 1.5rem | Medium (500) | Sub-headings, Featured Metric Callouts |
| `text-base` | 16px (1.0rem) | 1.5rem | Regular (400) | Body Copy, Lead Form Inputs |
| `text-sm` | 14px (0.875rem)| 1.25rem | Regular / Medium | Data Tables, Form Labels, List Items |
| `text-xs` | 12px (0.75rem) | 1.0rem | Medium (500) | Status Badges, Timestamps, Table Footers |

---

## 4. Key Component Patterns

### 4.1. Status Badges & Pills
Badges indicate workflow states using semantic color variants:
- **Success / Offered / Verified**: Green tint (`bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-400`).
- **In Progress / Screening**: Blue tint (`bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/50 dark:text-blue-400`).
- **Pending / Action Required**: Amber tint (`bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/50 dark:text-amber-400`).
- **Rejected / Terminated**: Red/Rose tint (`bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/50 dark:text-rose-400`).
- **Draft / Inactive**: Neutral slate tint (`bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300`).

### 4.2. High-Density Data Tables
- Alternating row zebra striping or subtle border separators (`border-b border-border/60`).
- Sticky header rows for long candidate and job lists.
- Inline contextual action buttons (View Profile, Advance Stage, Download Resume).
- Empty state patterns providing helpful iconography, explanatory copy, and a primary CTA.

### 4.3. Form Controls & Caret Preservation
- All `<input>` and `<textarea>` elements feature explicit focus rings (`focus:ring-2 focus:ring-primary/40 focus:border-primary`).
- Default native caret color is enforced via `caret-primary` so the user always has clear typing feedback.
- Disabled inputs carry `cursor-not-allowed opacity-50` without focus rings.

---

## 5. Accessibility Compliance (WCAG 2.1 AA)

- **Contrast Ratios**: All text against its corresponding background meets or exceeds 4.5:1 for normal text and 3.0:1 for large headings.
- **Keyboard Navigation**: All interactive elements (buttons, inputs, dropdowns, tabs) are keyboard reachable with clear `focus-visible` styling.
- **Screen Reader Support**: Meaningful `aria-label`, `role="status"`, and `aria-expanded` attributes are provided on collapsible sidebars and modal dialogs.
