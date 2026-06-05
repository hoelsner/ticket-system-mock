---
name: frontend-design
description: Build or restyle a frontend with a deliberate visual direction held through palette, typography, structure, and texture while keeping real on-screen content, standard UI copy, and this repository's Django, Cotton, Pico CSS, HTMX, dark-mode, and i18n rules intact. Use when building or restyling a frontend, screen, page, flow, or visual system.
argument-hint: Describe the screen, audience, product purpose, and restyling goal.
user-invocable: true
license: MIT
---

# Frontend Design

## What This Skill Does

This skill turns a frontend request into a deliberate visual direction that holds together across palette, typography, structure, and texture without drifting into generic UI work or fabricated screen content.

In this repository, the current codebase rules are authoritative. Use this skill to choose and apply a strong visual direction inside the existing stack and architecture, not to bypass them.

## Repository Authority

Before making design decisions, lock these repository rules:

- the frontend is server-rendered Django templates, not a SPA
- reusable UI pieces belong in Django Cotton components where that structure already exists
- Pico CSS is the baseline visual layer; start with semantic HTML and Pico variables before adding custom styling
- from a color perspective, stay within Pico CSS surfaces, borders, and semantic tokens by default; avoid tinted gradients, blurred color washes, or custom background colorization unless the task explicitly requires them
- HTMX is preferred for interaction and progressive enhancement over client-heavy scripting
- all static assets must be served locally from `src/webapp/static`; do not use CDNs
- both light mode and dark mode are required behavior
- multilingual support is required; copy must remain compatible with Django i18n
- the login and sign-up experience uses a split layout with functional content on the left and contextual illustration on the right
- the authenticated application uses a top-down shell with persistent top navigation, a left burger menu, a top-right utility area, and a main content region
- use repository terminology from `UBIQUITOUS_LANGUAGE.md`; prefer `Issue`, `Workflow State`, `Group`, and `User`

If a design move conflicts with these rules, the repository rules win.

## When to Use

Use this skill when:

- building a new frontend screen, flow, or component set
- restyling an existing page that feels generic or visually directionless
- choosing a visual direction for a product surface while preserving real product content
- reviewing a frontend implementation for token drift, filler copy, or generic design output

Do not use this skill when:

- the task is primarily backend or domain-model work
- the main need is dependency setup; use the repository dependency workflow instead
- the request is about broad product architecture rather than visual implementation

## How to Work

Before writing code, run this sequence.

1. **Context** — Identify the purpose, audience, domain, content density, and the real product information the screen must present. State the problem in one sentence.
2. **Anchor** — Pick one anchor. Lean toward unexpected pairings rather than the safest visual match. State the choice and the reason in one line.
3. **Differentiator** — Define one memorable anchor-internal move such as a signature interaction, typographic gesture, layout motif, or material treatment. Make it visible in the rendered output.
4. **System** — Match the chosen anchor's allowed tokens exactly. Do not blend anchors.
5. **Repository fit** — Map the direction onto this stack: semantic HTML first, Pico structure and variables first, Cotton components where reuse exists, HTMX for interaction, local static assets only, dark and light mode parity, and i18n-safe copy.
6. **Implementation** — Outline structure, then build the smallest complete slice.
7. **Verification** — Check token fidelity, content discipline, responsiveness, mode parity, and repository constraints before shipping.

Commit fully to one anchor. `Swiss with Brutalist edge` is a category error.

## Content Is Not Design

Design is visuals: palette, typography, structure, and texture. Content is authored separately and must still be correct.

Every string on screen must either:

- name real information from the product
- use repository terminology that matches the current domain model
- be authored UI copy that clearly knows what it is, such as a heading, field label, helper text, button label, or explicit sample placeholder

Forbidden:

- fabricated data that pretends to be real issue records, telemetry, user identities, or environment state
- filler labels or decorative subtitles that add no information
- themed replacements for standard UI copy such as `Authenticate Session` instead of `Next` or `Remember this operator` instead of `Remember me`
- Unicode glyphs used as icon substitutes; use the repository's icon approach or no icon
- AI-slop register, including twee subcopy, fake technical mystique, ornamental pseudo-structure, or invented dashboards full of synthetic values

If a slot has no real content yet, leave it structurally honest. Do not fabricate life into the interface.

## Repository-Specific Implementation Rules

- put templates under `src/webapp/templates` in the appropriate app-aligned subdirectory
- put custom static assets under `src/webapp/static`
- prefer semantic HTML and Pico primitives before introducing custom wrappers
- keep background treatment close to Pico defaults; prefer `var(--pico-background-color)` and `var(--pico-card-background-color)` over custom color-mixed fills
- when custom CSS is needed, keep it minimal and use the existing BEM-style naming pattern
- prefer data attributes for JavaScript and HTMX hooks instead of styling classes as selectors
- preserve the authenticated shell and auth split-layout patterns unless the task explicitly changes them
- keep standard UI copy standard; visual tone comes from design tokens, not rewritten button labels
- if a new dependency seems necessary, stop and route it through the repository's dependency workflow instead of adding it here

## The Eight Anchors

Each anchor locks specific CSS tokens. Picking one commits to those tokens.

### 1. Swiss

- surface: pure white `#FFFFFF` or neutral `#F7F7F8`
- typography: Akzidenz-Grotesk, Helvetica Neue, or Sohne; one sans family for display and body
- accent: one of `#E4002B`, `#FF4F00`, or `#002FA7`
- structure: visible grid lines or 1 px hairline rules, left-aligned type, asymmetric balance, numerals as composition elements
- breaks if: warm paper, serif display, grain texture, or centered typography appears

### 2. Industrial

- surface: `#000000` or `#0B0C0A`
- typography: IBM Plex Mono, JetBrains Mono, or Berkeley Mono for both display and body
- signal color: one semantic color from `#00E676`, `#FF3B30`, `#FFB800`, or `#C6FF4A`
- structure: flat surfaces, 1 px borders, tabular numerics
- breaks if: serif or proportional type, warm paper, grain, decorative shadows, or rounded corners appear

### 3. Brutalist

- surface: pick 2 to 3 equal competitors from `#FF0000`, `#0000FF`, `#FFFF00`, `#000000`, `#FFFFFF`
- typography: system fonts only, mixed deliberately
- shadows: hard offset, no blur
- controls: native browser controls and underlined blue links that stay blue
- breaks if: webfonts, tuned colors beyond pure primaries, soft shadows, rounded corners, or centered layout appear

### 4. Aurora Maximalism

- surface: saturated gradient through violet, magenta, and cyan
- typography: Inter Variable, PP Neue Machina, or Sharp Grotesk for oversized display
- texture: mesh gradient as a primary surface feature with committed glow
- motion: spring-led orchestration and parallax where appropriate
- breaks if: flat backgrounds, warm paper, restraint, or hairline rules become the primary structure

### 5. Chaotic Maximalism

- surface: clashing palette of pastels and neons in the same composition
- typography: three or more deliberately colliding typefaces
- texture: patterns across surfaces and oversized display type against busy ground
- breaks if: coherent palette, single typeface, whitespace as the main structure, or tidy dominance ratios appear

### 6. Retro-Futuristic

- surface: `#0A0014` or deep navy-black
- typography: period-specific display and body choices such as VT323, Orbitron, Space Mono, Monoton, Press Start 2P, or IBM Plex Mono
- accent: neon magenta and cyan, or phosphor green and amber
- texture: committed CRT scanlines, chromatic aberration, or both
- breaks if: flatness, modern neutral sans-serifs, paper surfaces, or absent texture appears

### 7. Organic

- surface: earth tones such as sage `#8B9D83`, clay `#B08B6E`, terracotta `#C66B3D`, ochre `#C08E3A`, moss `#606C38`, with sand `#E8DCC7` or oat `#D4B895` when a light surface is needed
- typography: a humanist serif or warm geometric sans; Fraunces belongs only here
- structure: rounded corners from 16 px to 32 px
- texture: low-grain surface and gentle motion
- breaks if: cream warm-paper surfaces, cold greys, pure whites, pure blacks, or hard rectangles dominate

### 8. Lo-Fi

- surface: paper-yellow `#E8E0C0` or `#EDE4CF`
- typography: mixed system fonts colliding deliberately
- structure: rotated elements 2 to 8 degrees off-grid
- texture: halftone transitions, Risograph-style misregistration, and tactile paper details
- breaks if: precision, a single typeface, smooth motion, square-to-grid rigidity, or cream surfaces appear

## Output

Every implementation should deliver:

- a short design-direction preamble before the code that names the chosen anchor, why it is the right tension for the brief, the differentiator, and the key palette, type, and texture choices
- token fidelity that stays within the chosen anchor's allowed range
- content discipline with real information, honest placeholders, and standard UI copy for standard actions
- a visible differentiator that actually renders on screen
- repository fit: semantic HTML, Pico-first structure, local assets, dark and light mode support, and i18n-safe content
- color discipline: preserve Pico CSS's native visual tone unless the user explicitly asks for a stronger color direction

## Before Shipping

- unexpected pairing: did the choice reach for creative tension instead of the safest visual answer
- token fidelity: does every rendered token stay inside the anchor's allowed range
- content discipline: are all strings real, honest, and useful with no fabricated data or filler
- differentiator visible: is the memorable move implemented, not merely described
- hybrid resistance: did one anchor hold without drift into a blended style
- repository fit: does the work preserve the split auth layout or authenticated shell where applicable, avoid CDN usage, and keep light and dark mode behavior intact
- responsive behavior: does the layout still read cleanly on narrow screens and larger desktops
- i18n safety: will the copy and structure survive translation without relying on fragile fixed widths or decorative text hacks

## Output Expectations

When using this skill, produce:

1. a one-paragraph design-direction preamble
2. the smallest complete implementation slice that proves the direction
3. a brief verification summary covering anchor fidelity, content discipline, repository fit, and mode parity