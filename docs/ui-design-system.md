# Atlas — UI / UX Design System

> Aesthetic: **SoulsLab cinematic dark** × **Bloomberg Terminal density**.
> Premium institutional UI for an AI-native intelligence workflow.

---

## 1. Design principles

1. **Calm density** — show a lot, never feel busy. Negative space carries hierarchy.
2. **Information as art** — typography, motion, and chrome are co-equal with the data.
3. **Sensory restraint** — never more than two accent colors per viewport.
4. **Earned motion** — animations communicate state change, never decorate.
5. **Cinema, not chrome** — translucent surfaces, depth, blur, glow. Never neon.
6. **Trace-back-first** — every datum is one click from its source. No dead ends.

---

## 2. Color tokens

CSS variables, declared on `:root[data-theme="cinema"]` (default).

```css
:root[data-theme="cinema"] {
  /* Surfaces */
  --bg-0:           #07080B;   /* page background */
  --bg-1:           #0C0E13;   /* card */
  --bg-2:           #12151C;   /* elevated card */
  --bg-3:           #1A1E27;   /* hover */
  --bg-glass:       rgba(18, 21, 28, 0.62);
  --bg-blur:        24px;

  /* Borders */
  --line-1:         rgba(255, 255, 255, 0.04);
  --line-2:         rgba(255, 255, 255, 0.08);
  --line-strong:    rgba(255, 255, 255, 0.18);

  /* Text */
  --fg-0:           #F5F7FA;   /* primary */
  --fg-1:           #C4CAD3;   /* secondary */
  --fg-2:           #8089A0;   /* muted */
  --fg-3:           #525A70;   /* disabled */

  /* Accents */
  --accent-amber:   #E8B864;   /* primary accent — institutional gold */
  --accent-amber-soft: rgba(232, 184, 100, 0.12);
  --accent-cyan:    #6FC4E0;   /* secondary — data */
  --accent-violet:  #9D7BE8;   /* tertiary — AI / graph */

  /* Semantic */
  --pos:            #4ADE80;   /* bullish */
  --neg:            #F87171;   /* bearish */
  --warn:           #FBBF24;
  --info:           #6FC4E0;

  /* Industry palette (sampled, not exhaustive) */
  --ind-banking:    #6FC4E0;
  --ind-realestate: #E8B864;
  --ind-tech:       #9D7BE8;
  --ind-energy:     #F59E0B;
  --ind-pharma:     #4ADE80;
  --ind-auto:       #F87171;

  /* Elevation (shadow + glow) */
  --shadow-1:       0 1px 0 rgba(255,255,255,0.04) inset, 0 8px 24px rgba(0,0,0,0.32);
  --shadow-2:       0 1px 0 rgba(255,255,255,0.06) inset, 0 24px 64px rgba(0,0,0,0.48);
  --glow-amber:     0 0 0 1px rgba(232,184,100,0.18), 0 8px 32px rgba(232,184,100,0.12);
  --glow-cyan:      0 0 0 1px rgba(111,196,224,0.18), 0 8px 32px rgba(111,196,224,0.12);

  /* Motion */
  --ease-out-soft:  cubic-bezier(0.2, 0.8, 0.2, 1);
  --ease-in-soft:   cubic-bezier(0.8, 0.2, 0.8, 0.2);
  --ease-spring:    cubic-bezier(0.34, 1.56, 0.64, 1);
  --dur-1:          120ms;
  --dur-2:          220ms;
  --dur-3:          360ms;
  --dur-cinema:     640ms;
}
```

Alternative themes (`data-theme="dark"`, `data-theme="light"`) override only the surface and text tokens — accents stay constant.

---

## 3. Typography

| Role | Font | Notes |
|---|---|---|
| Display | **Söhne Breit** (or Inter Display fallback) | numerical headers, hero theses |
| Sans | **Inter Variable** | body, UI |
| Mono | **JetBrains Mono** | tickers, timestamps, percentages |
| Serif | **Söhne Mono** italic for pull-quotes | sparingly |

Type scale (rem):

```
display-2  4.5    700  -0.04 tracking
display-1  3.0    600  -0.03
h1         2.0    600  -0.02
h2         1.5    600  -0.015
h3         1.25   600  -0.01
body-lg    1.0625 500
body       0.9375 450
caption    0.8125 500  +0.01 tracking
overline   0.6875 600  +0.12 tracking uppercase
mono-lg    1.0    500  tabular-nums
mono       0.875  500  tabular-nums
```

Numbers always `tabular-nums`. Percentages always lead with sign (`+`, `−`, never `-`).

---

## 4. Spacing & layout

8-pt grid with 4-pt half-steps for fine alignment.

```
xs    4
sm    8
md    16
lg    24
xl    32
2xl   48
3xl   64
4xl   96
```

Page grid: 12-column, max-width `1440px`, gutter `24px`, inner padding `32px`.

The dashboard is **shell + canvas**:
- Shell (fixed): top bar 56px, left sidebar 240px, right rail 320px (collapsible).
- Canvas: scrollable, the rest.

---

## 5. Surfaces & glassmorphism

Three elevation steps:
1. **Page**: `--bg-0`, no shadow.
2. **Card**: `--bg-1`, `border: 1px solid var(--line-1)`, `--shadow-1`.
3. **Floating**: `--bg-glass`, `backdrop-filter: blur(var(--bg-blur))`, `--shadow-2`, `border: 1px solid var(--line-2)`.

Glass is reserved for: command palette, modals, toasts, the live pipeline status pill. Never for content cards (it kills text legibility on busy bg).

---

## 6. Motion language

| Pattern | Spec |
|---|---|
| Page enter | fade + 8px Y rise, 360ms, `--ease-out-soft`, stagger 24ms |
| Card hover | `translateY(-1px)`, border `--line-2 → --line-strong`, 220ms |
| Card click | scale 0.99 + glow flash, spring `--ease-spring`, 360ms |
| Toast in | slide 12px Y + fade, 220ms |
| Modal | scale 0.98 → 1 + fade, 220ms, glass blur tween 0 → 24px |
| Realtime ping | accent ring pulse, 1.2s, fade out |
| WS connect | dot fade green, 360ms |
| Cinema transition | overlay sheet sweeps L → R, 640ms, `--ease-out-soft` |
| Number tick | digit roller, individual digit 80ms stagger |
| Pipeline step | progress segment paints L → R, 220ms per node |

Reduced-motion: every animation drops to a 1-frame crossfade ≤120ms.

---

## 7. Iconography

- **Lucide** as the default set (matches shadcn/ui).
- 16/20/24px sizes only. Stroke `1.5`. Never filled by default.
- Industry icons: a curated set (Heroicons + custom 24x24 monoline). One per industry.

---

## 8. Components (contracts)

### `<NewsCard>`

```ts
interface NewsCardProps {
  id: string;
  title: string;
  thesis: string;          // first sentence — bold, larger
  bullets: string[];       // supporting points
  source: { name: string; url: string };
  publishedAt: ISODate;
  industries: Industry[];
  entities: Entity[];      // chips
  region: 'VN' | 'INT';
  bucket: 'macro' | 'corp';
  confidence: 'high'|'mid'|'low';
  isNew?: boolean;         // shows realtime pulse
  onOpen?: () => void;
  onTraceback?: (target: 'raw'|'wiki'|'report') => void;
}
```

Visual:
- Top: industry stripe (3px) + region pill + bucket tag + timestamp.
- Thesis line in display-1.
- Bullets in body, monospace numerics.
- Footer: entity chips + source citation + 3 trace-back buttons.
- Right edge: confidence indicator (filled / half / outline circle).

### `<CommandPalette>` (cmd-k)

- Glass surface, centered, 640px wide.
- Sections: `Pages`, `News`, `Reports`, `Entities`, `Industries`, `Actions`.
- Live preview pane on the right (40% width).
- Keyboard-first: arrows + enter + esc; never closes on outside-click during typing.

### `<PipelineStatusBar>`

- Bottom-fixed glass pill, 320px wide.
- Five segments (extract / classify / summarize / embed / persist).
- Each segment is a colored chevron that lights up amber when active, green when done, red on failure.
- Hover → tooltip with token spend, latency.

### `<KnowledgeGraph>`

- D3 force-directed; nodes are entities/industries/themes.
- Node radius = log(mentions).
- Edge weight = co-occurrence count.
- Zoom: trackpad pinch + ctrl-scroll; pan: drag canvas.
- Click node → opens detail rail with timeline of news.
- Time scrubber along the bottom: filter to last 24h / 7d / 30d / all.

### `<ReportViewer>`

- Two-column: PDF iframe on left (60%), navigator + annotations on right.
- Navigator: section TOC + thumbnail strip.
- Annotation chips: hover a paragraph → see related raw/news cards.
- Top bar: download PDF, share link, build status, version dropdown.

### `<IndustryHeatmap>`

- 4×7 grid (28 industries) showing today's volume × sentiment.
- Color = sentiment (red → neutral → green).
- Intensity = volume.
- Hover → expand tooltip with top thesis.

---

## 9. Page templates

### `/` Daily Intelligence

```
┌─────────────────────────────────────────────────────────────────┐
│  Top bar: logo · date · WS dot · cmd-k · theme toggle           │
├──────────┬──────────────────────────────────────────┬───────────┤
│ Sidebar  │                                          │ Right rail│
│          │   ▸ Daily Brief Header (today's thesis)  │           │
│ • Today  │   ▸ Industry Heatmap                     │ Entity    │
│ • Reports│   ▸ Intelligence Feed (cards by date)    │ rail:     │
│ • Graph  │     ─ macro vs corporate split           │ trending  │
│ • Search │     ─ filter chips: industry/geo/entity  │ entities  │
│ • Settings│                                          │ today     │
│          │                                          │           │
│          │                                          │ Watchlist │
│          │                                          │           │
│          │                                          │ Pipeline  │
│          │                                          │ status    │
└──────────┴──────────────────────────────────────────┴───────────┘
           ▸ Pipeline status pill (fixed bottom-right)
```

### `/reports` Report Archive

- Timeline view (year → month → day expand).
- Each row shows thesis snippet + PDF preview on hover.

### `/reports/:id` Report

- Full `<ReportViewer>` (above).

### `/graph` Knowledge Graph

- Fullscreen `<KnowledgeGraph>` + bottom time scrubber + right detail rail.

### `/search` Search

- Big query bar with mode toggle (lexical / semantic / hybrid).
- Faceted results: industry, entity, date, source.
- Each result expandable inline.

### `/entities/:slug` Entity

- Hero: name, ticker, aliases, sector chip.
- Tabs: Timeline · Reports · Network · Notes.

### `/industries/:slug` Industry

- Hero: industry name, sector summary, top 5 entities.
- Heatmap-like volume chart over time.
- Filtered feed.

---

## 10. Accessibility

- Color contrast: WCAG AA in cinema theme. Verified for `--fg-0`, `--fg-1` on `--bg-0/1/2`.
- Focus rings: 2px `--accent-amber`, 2px offset.
- Keyboard: tab order matches visual; cmd-k from anywhere; esc closes overlays.
- Screen reader: `aria-live="polite"` for the pipeline status; semantic landmarks (`header`, `nav`, `main`, `aside`).
- Reduced motion: see §6.
- High-contrast theme variant available via `data-theme="contrast"`.

---

## 11. Empty / error / loading states

Every component declares three states:
- **Loading** → shimmer skeleton (linear-gradient sweep, 1200ms loop).
- **Empty** → illustration glyph + one-line guidance + primary CTA.
- **Error** → red icon + actionable copy + retry button.

Skeletons match the final layout's exact bounding boxes — no layout shift when content arrives.

---

## 12. i18n notes

- Default `vi-VN`. Toggle to `en-US` in settings.
- Vietnamese diacritics MUST render with correct line-height; test with `ờ ề ử ự` ascenders.
- Numbers: VN format (`1.234.567,89`); allow user override.
- Currency: VND default, USD secondary on entities w/ ADRs.

---

## 13. Brand voice (UI copy)

- **Tone**: precise, neutral, slightly formal. Never marketing-speak.
- **Length**: <80 chars per UI string. Buttons <16 chars.
- **Numbers** before adjectives: "+12 articles · 4 industries · 09:42 ICT".
- **Time** in ICT by default with 24h clock.
- **Action verbs**: Open, Trace, Pin, Build, Refresh — never "Click", "Submit", "OK".
