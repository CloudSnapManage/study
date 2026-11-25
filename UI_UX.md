# Cognito — UI/UX Design Specification (`UI_UX.md`)

## 1. Visual Direction: "Precision Scientific Instrument"
Cognito is modeled after native desktop engineering tools (**Linear**, **Obsidian**, **Zotero**, **Raycast**): high-contrast neutral graphite surfaces, hairline `1px` borders, crisp typographic hierarchy, and restrained warm-amber/steel-blue accents that never fatigue the eyes during multi-hour study sessions.

---

## 2. Color Tokens (CSS Custom Properties)

Define these exact tokens in `frontend/styles.css` (with an optional high-contrast light mode toggle via `[data-theme="light"]` using inverted warm-paper neutrals):

```css
:root {
  /* Surface Hierarchy (3% tonal steps — no drop shadows needed) */
  --bg-app:        #0d0e11;   /* Base window & top/bottom bars */
  --bg-sidebar:    #111317;   /* Left navigation rail */
  --bg-panel:      #15181e;   /* Primary workspace panes */
  --bg-elevated:   #1c2028;   /* Hover rows, active tabs, dropdowns */
  --bg-inset:      #0a0b0d;   /* Formula blocks, code, PDF canvas backdrop */

  /* Hairline Borders */
  --border-subtle: #222630;   /* Standard pane dividers & table rows */
  --border-strong: #323846;   /* Focused inputs, active buttons */

  /* Typography */
  --text-primary:   #eceef2;  /* Main body, headings, rendered KaTeX */
  --text-secondary: #9aa1b2;  /* Metadata, captions, secondary labels */
  --text-muted:     #5e6577;  /* Placeholders, disabled items, shortcuts */

  /* Restrained Functional Accents */
  --accent-primary: #d98a2b;  /* Warm engineering amber: primary actions & active markers */
  --accent-hover:   #e89b3c;
  --accent-subtle:  rgba(217, 138, 43, 0.12);

  /* Semantic Status Colors (Muted, non-neon) */
  --status-ok:      #3ea875;  /* Connected / Mastered / Good */
  --status-warn:    #d4943a;  /* High-yield exam alert / Hard */
  --status-err:     #d45353;  /* Disconnected / Error / Again */
  --status-info:    #4c8eda;  /* Citation links & tool execution badges */
}
```

---

## 3. Typography & Spacing Scale

* **UI Sans Stack:** `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif` (served locally if bundled in `/vendor/fonts/`, otherwise native system sans)
* **Monospace Stack (Formulas, Badges, Citations, Metrics):** `'JetBrains Mono', 'Fira Code', ui-monospace, SFMono-Regular, monospace`
* **Type Scale:**
  * Page / Workspace Title: `15px` (`font-weight: 600`, `letter-spacing: -0.01em`)
  * Section Header: `11px` (`font-weight: 600`, uppercase, `letter-spacing: 0.06em`, `--text-muted`)
  * Body / Chat Prose: `13.5px` (`line-height: 1.6`, max measure `72ch` for comfortable reading)
  * Table & List Rows: `13px` (`line-height: 1.4`)
  * Metadata / Citation Chips / KBD Hints: `11.5px` monospace (`font-variant-numeric: tabular-nums`)
* **Spacing Grid:** Strict `4px` base unit (`4px`, `8px`, `12px`, `16px`, `24px`).
* **Radii:** Panels/Cards `6px` | Buttons/Inputs `4px` | Badges/Filter Chips/KBD tags `3px` | Status dots `50%` (`6px × 6px`).

---

## 4. Global Application Shell (`100dvh` Desktop Layout)

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ [Cognito]  Subject: [All Subjects ▾]          [Ctrl+K Search...]   [Scan] [⚙]│ ◄── 44px Top Bar
├───────────────┬──────────────────────────────────────────────────────────────┤
│ WORKSPACE     │                                                              │
│ ▸ Daily Sprint│                                                              │
│   Exam Radar  │                                                              │
│   Agent Chat  │                 ACTIVE WORKSPACE PANE                        │
│   Vault       │         (Split-pane capable: Main View + PDF Drawer)         │
│   Mock Exam   │                                                              │
│   Step Check  │                                                              │
│               │                                                              │
│ SUBJECTS      │                                                              │
│ • Physics II  │                                                              │
│ • Math II     │                                                              │
│ • Chemistry   │                                                              │
├───────────────┴──────────────────────────────────────────────────────────────┤
│ ● SQLite: 142 chunks   ● Obsidian: Synced   ● LLM: Ollama (qwen2.5-coder)    │ ◄── 26px Status Bar
└──────────────────────────────────────────────────────────────────────────────┘
```

1. **Top Utility Bar (`44px` height, `1px` bottom border):**
   * Left: Collapse sidebar toggle (`16px` SVG) + Wordmark `Cognito` (`14px` semibold) + Global Subject Filter dropdown (`All Subjects`, `Physics_II`, etc.).
   * Center: Trigger button styled as a crisp command bar (`Search formulas, notes, PDFs...  Ctrl K`).
   * Right: `Scan Materials` action button + `Settings` icon button.
2. **Left Navigation Rail (`210px` width, collapsible to `48px` icon rail, `1px` right border):**
   * Top group (`WORKSPACE`): 6 clean single-line items (`Daily Sprint` with `3px`-radius due-count badge, `Exam Radar`, `Agent Chat`, `Formula & Diagram Vault`, `Mock Exam`, `Solution Checker`). Active item has `2px` left amber bar (`--accent-primary`) and `--bg-elevated` fill.
   * Bottom group (`SUBJECTS`): Quick filter list of detected folders with right-aligned tabular document counts.
3. **Middle Workspace Container (`height: calc(100dvh - 44px - 26px)`, `overflow: hidden`):**
   * Houses the active view and optional right-hand **PDF Page Inspector Drawer** (`45%` width, `1px` left border, `Esc` to close).
4. **Bottom Telemetry Status Bar (`26px` height, `11.5px` monospace, `1px` top border):**
   * Displays live `6px` status dots + compact tabular text: `SQLite: <N> chunks` | `Obsidian: Connected / Unset` | `Chat: <Active Profile>` | `Tokens: <Session Total>`.

---

## 5. Screen-by-Screen UX Blueprints

### View 1: Daily Sprint (SM-2 Spaced Repetition)
* **Layout:** Centered single-column study stage (`max-width: 680px`) with a thin `2px` top progress track (`Card 2 of 5` in tabular monospace).
* **Card Structure (`--bg-panel`, `1px solid --border-subtle`, `6px` radius):**
  * Top metadata strip: `PHYSICS II • GAUSS'S LAW` on left; clickable source badge `[Lecture_02.pdf, p. 4]` (`3px` radius) on right.
  * Question body: Crisp `15px` typography with centered KaTeX display math (`--bg-inset`).
  * Reveal action: Full-width subtle button `Show Answer  [Space]`.
  * Answer state: `1px` divider line + step-by-step derivation/answer + optional `LaTeX Hint` block.
* **Bottom Grading Dock (4 equal-width buttons with key hints):**
  * `[1] Again (<1d)` | `[2] Hard (1d)` | `[3] Good (3d)` | `[4] Easy (6d)`

### View 2: Exam Radar (Priority & Weightage Matrix)
* **Layout:** Full-width high-density data table (`--bg-panel`) with square-edged filter chips (`3px` radius: `All`, `High Yield >=70%`, `Unmastered Only`) and `Sync MOC to Obsidian` button.
* **Columns:**
  1. `Done` (`16px` crisp checkbox — toggles mastery & updates Obsidian MOC)
  2. `Topic / Concept` (bold primary text + sub-label showing source PDF)
  3. `Subject` (muted monospace badge, `3px` radius)
  4. `Notes` (mention count, right-aligned tabular)
  5. `Past Papers` (mention count, right-aligned tabular)
  6. `Exam Probability` (inline `60px` horizontal bar + tabular `%` readout)
  7. `Action` (`Study in Chat →` quick link that opens Agent Chat pre-seeded with that topic)

### View 3: Agent & RAG Chat + Split-Screen PDF Verifier
* **Layout:** Resizable 2-column split view (`55%` Chat Stream / `45%` PDF Page Inspector when a citation is clicked; `100%` centered `760px` column when PDF drawer is closed).
* **Chat Header Bar (`38px`, `1px` bottom border):**
  * Model Profile Selector dropdown (`Ollama: qwen2.5-coder:7b ▾`)
  * Mode Segmented Control (`Agent + Tools` | `Strict Syllabus` | `Tutor`)
  * Right action: `Save Thread to Obsidian` button
* **Message & Tool-Trace Rendering:**
  * User messages: Subtly tinted `--bg-elevated` block with `1px solid --border-subtle` (`6px` radius).
  * **Tool Call Trace Bars:** Compact collapsible accordion bars (`12px` monospace, `--bg-inset`, `1px` border, `4px` radius):
    `▸ Tool: search_course_materials("Gauss's Law", past_papers) — 4 chunks (18ms)`
    Clicking expands the raw JSON arguments and returned snippet preview.
  * Assistant messages: Clean editorial layout (`13.5px` body, `$$...$$` display math blocks with hover `Copy TeX`, numbered steps, and inline clickable citation badges `[Past_2024.pdf, p. 3]`).
* **Split-Screen PDF Page Inspector:**
  * Shows rendered high-DPI PNG of the exact cited PDF page on `--bg-inset`, page stepper (`< Page 3 of 18 >`), zoom toggle (`Fit` / `150%`), and highlighted bounding boxes around matched search terms.

### View 4: Formula & Diagram Vault
* **Layout:** Split top filter bar (`38px`) + 2-pane master-detail split (`38%` Index List / `62%` Detail Inspector).
* **Top Filter Bar:** Segmented type filter (`All` | `Formulas` | `Diagrams` | `Definitions`) + instant keyword search input (`/` to focus).
* **Left Master List (`--bg-panel`, `1px` right border):**
  * Compact `48px` rows separated by `1px solid --border-subtle`.
  * Each row displays: Formula/Diagram name (`13px` medium), Subject badge (`3px` radius), and source page (`p. 11`, tabular monospace).
* **Right Detail Inspector (`--bg-panel`):**
  * Header with item title, clickable `[Lecture_04.pdf, p. 11]` source badge, and `Copy TeX` / `Add to Sprint` action buttons.
  * Primary viewport (`--bg-inset`, `1px` border): High-contrast KaTeX equation block or crisp extracted diagram PNG with zoom toggle.
Use code with caution.
• Variable Legend table (Symbol | Meaning | SI Unit in tabular monospace) + Related Past Exam Appearances list below.

View 5: Mock Exam (Timed Exam Simulator)

• Layout: Distraction-reduced 2-pane layout (220px Question Navigator Matrix on left / Active Question Paper on right) with a pinned 38px Exam Control Header.
• Exam Control Header:
	• Configuration bar (when unstarted): Subject selector, Question count (5, 10, 20), Source bias (Past Papers Weighted | Balanced), and Start Timed Exam button.
	• Active timer readout (44:12 in 13px tabular monospace; shifts to --status-warn under 05:00), Flag for Review [F] toggle, and Submit Exam button.
• Left Question Matrix:
	• Compact 5-column grid of 32px × 32px numbered squares (4px radius, tabular monospace) showing status via hairline borders and subtle fills: Unanswered (--bg-panel), Answered (--bg-elevated + --border-strong), Flagged (1px solid --status-warn).
• Right Question Stage & Post-Exam Rubric:
	• Displays question prompt, marks weight ([5 Marks]), LaTeX-capable scratchpad textarea (Shift+Enter for newline), and Prev [←] / Next [→] controls.
	• Graded State: Replaces scratchpad with side-by-side comparison (Your Response vs. Model Solution), rubric point breakdown (4 / 5), and one-click Send Missed Concepts to Daily Sprint button.

View 6: Solution Checker (Step-by-Step Derivation Auditor)

• Layout: Symmetric 2-column split (50% Student Work Input / 50% Line-by-Line Diagnostic Audit).
• Left Pane (Your Derivation):
	• Problem statement selector (paste text, pick from Mock Exam/Vault, or attach local image/scan of handwritten work).
	• Line-numbered monospace/LaTeX editor (--bg-inset, 1px border) with live KaTeX preview toggle and Audit Steps [Ctrl+Enter] primary amber button.
• Right Pane (Step Verification):
	• Summary status bar (Error detected at Step 3 • Algebraic sign inversion).
	• Step-by-step audit rows separated by 1px solid --border-subtle:
		• Valid steps show a 16px check icon (--status-ok) and terse verification note.
		• First failing step highlights with a 2px left border (--status-err), shows the exact discrepancy (Expected -∇V, found +∇V), cites the relevant course rule [Notes_03.pdf, p. 9], and offers a Create Error Flashcard button.

6. Global Command Palette (Ctrl+K / ⌘K) & Settings Modal

• Command Palette: Centered 560px modal (--bg-panel, 1px solid --border-strong, 6px radius, solid #000000 65% opacity backdrop—no blur). Instant keyboard-navigable (↑/↓, Enter, Esc) unified search across formulas, PDF chunks, Obsidian notes, and workspace actions.
• Settings Drawer (440px right slide-over, 1px left border): Configure MATERIALS_DIR, OBSIDIAN_VAULT_PATH, active LLM provider/model (Ollama endpoint or API keys), and theme (Graphite Dark / Paper Light), with live Test Connection status indicators.

