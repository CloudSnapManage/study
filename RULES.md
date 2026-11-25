# Cognito — Strict Engineering & Design Guardrails (`RULES.md`)

> **MANDATORY INSTRUCTION FOR AI CODE GENERATION:**
> Read and enforce every rule in this file and `UI_UX.md` before writing HTML, CSS, JavaScript, or Python. Any violation of the "Banned AI Tropes" section is considered a build failure.

## 0. Architecture & Stack Lock
* **Backend:** Python (`FastAPI` or `Flask`) serving local JSON APIs, SSE streams, and static files.
* **Frontend:** Pure Vanilla HTML5, CSS3 (Custom Properties), and modular ES6+ JavaScript (`frontend/app.js`). Zero Node/npm build steps, zero Tailwind CDN, zero React/Vue/Alpine/jQuery.
* **Offline-First Runtime:** Every font, icon, Markdown parser, HTML sanitizer, and math library must load from local `/vendor/` paths.

---

## 1. Banned "AI-Generated" UI Tropes (Zero Tolerance)
1. **NO Gradients Anywhere:**
   * Never use `linear-gradient`, `radial-gradient`, or `conic-gradient` on backgrounds, buttons, text, borders, or badges. Use flat, solid tonal surfaces only.
2. **NO Purple / Neon Cyan / Indigo-Glow Palettes:**
   * Do not use `#6366f1`, `#8b5cf6`, `#a855f7`, `#06b6d4`, or generic Tailwind default dark-blue (`#0f172a` / `#1e293b`) palettes. Use only the exact graphite + warm amber/slate tokens defined in `UI_UX.md`:
     * Surfaces: `--bg-app: #0d0e11`, `--bg-sidebar: #111317`, `--bg-panel: #15181e`, `--bg-elevated: #1c2028`, `--bg-inset: #0a0b0d`
     * Borders: `--border-subtle: #222630`, `--border-strong: #323846`
     * Text: `--text-primary: #eceef2`, `--text-secondary: #9aa1b2`, `--text-muted: #5e6577`
     * Accent: `--accent-primary: #d98a2b`, `--accent-hover: #e89b3c`, `--accent-subtle: rgba(217, 138, 43, 0.12)`
3. **NO Heavy Drop Shadows or Glassmorphism:**
   * Never use `backdrop-filter: blur(...)` or large diffused `box-shadow`s to separate containers. Separate layout regions exclusively via **`1px solid` hairline borders** and subtle `3%–5%` background luminance steps.
4. **NO Pill-Shaped Everything or Excessive Border Radius:**
   * Maximum border radius for cards/panels is `6px`; for buttons/inputs is `4px`; for code/tags/filter chips/badges is `3px`. Never use `border-radius: 9999px` on buttons, badges, or containers (only on small `6px` status dots).
5. **NO Decorative Emojis in UI Chrome:**
   * Never put emojis (`🚀`, `✨`, `📚`, `🧠`, `🔥`, `💡`) in headings, navigation tabs, buttons, empty states, or toast notifications. Use crisp `16px` stroke SVG icons (`1.5px` stroke width, Lucide/Tabler style) or plain typographic labels.
6. **NO Marketing Fluff or Robotic Copy:**
   * Ban words like *"Supercharge"*, *"Unleash"*, *"Seamless"*, *"Dive into"*, *"AI-Powered"*, *"Smart Insights"*, or *"Welcome back, Scholar!"*. Write terse, utilitarian desktop-software labels (`Scan Materials`, `Strict Syllabus`, `Due: 5`, `p. 14`).
7. **NO Gratuitous Animations:**
   * Ban `bounce`, `pulse`, `scale(1.05)` hover effects, and sliding entrance animations. Transitions must be instant or `<= 120ms ease-out` opacity/border shifts only.
8. **NO Fake Metrics or Placeholder Charts:**
   * Never render decorative sparklines, fake circular progress rings, or dummy numbers when a database table is empty. Show a clean, actionable empty state (`No PDFs indexed in ./materials/notes. [Scan Folder]`).

---

## 2. Layout & Information Density Rules
1. **App-Shell Viewport Lock (Desktop Workstation Feel):**
   * The main application shell must occupy `100dvh` (with `100vh` fallback) and `overflow: hidden`, structured as:
     * Fixed `44px` top utility bar
     * Middle workspace grid (`height: calc(100dvh - 44px - 26px)`) with a collapsible `210px` left navigation rail (collapses to `48px`) and independently scrollable workspace panes
     * Fixed `26px` bottom telemetry status bar
   * Never build a marketing-style vertically scrolling webpage.
2. **Tabular Numbers (`tabular-nums`) Mandatory:**
   * Every percentage, page number, exam weightage score, token count, latency readout, timer, and SM-2 interval must use `font-variant-numeric: tabular-nums` and monospace font so columns align vertically without jitter.
3. **Dense, Scannable Rows Over Bloated Cards:**
   * Prefer structured data tables, split-pane lists, and inspector drawers over giant multi-column grids of padded cards.
4. **LaTeX & Equation Respect:**
   * Display equations (`$$...$$`) must sit in dedicated, subtly tinted equation blocks (`--bg-inset`, `1px solid --border-subtle`) with generous vertical breathing room and a quiet `Copy TeX` button that appears on hover—never cramped inside narrow badges.
5. **Accessible Focus Rings Without Shadows:**
   * Never use `outline: none` without a replacement. All interactive controls must show a crisp `:focus-visible` ring (`2px solid var(--accent-primary)`, `outline-offset: 1px`).

---

## 3. Frontend Engineering Rules
1. **Zero External CDN Dependencies at Runtime:**
   * KaTeX CSS/JS/fonts (`/vendor/katex/`), Markdown parser (`/vendor/marked/`), and sanitizer (`/vendor/dompurify/`) must be served locally. Fonts must load from `/vendor/fonts/` or cleanly fall back to local system sans/monospace stacks. Cognito must render 100% identically with Wi-Fi disabled.
2. **State & DOM Discipline:**
   * Keep frontend state in a single predictable `AppState` object in `frontend/app.js`. Avoid inline `onclick="..."` HTML string soup; attach delegated event listeners cleanly.
3. **XSS & HTML Sanitization:**
   * Never inject raw unescaped Markdown or user/PDF strings into `innerHTML`. Always sanitize parsed Markdown via local `DOMPurify.sanitize(...)` before rendering, while protecting KaTeX math spans.
4. **Keyboard-First Parity:**
   * Every primary action must have a visible keyboard shortcut hint (`⌘K` / `Ctrl+K`, `Space` to reveal, `1–4` in Sprint, `Esc` to close drawers/modals, `Enter` to send chat, `Shift+Enter` for newline).
5. **Streaming Markdown + KaTeX Safety:**
   * During SSE streaming in chat, buffer partial `$$...$$` and `$ ... $` delimiters properly so raw unclosed LaTeX tokens do not flicker or break DOM layout mid-stream.

---

## 4. Backend & Data Integrity Rules
1. **Strict Path Sandboxing:**
   * Every file operation (PDF rendering, diagram serving, Obsidian note writing) must verify `target_path.resolve().is_relative_to(allowed_root.resolve())`.
2. **Non-Destructive Obsidian Writes:**
   * Never overwrite an entire `.md` file in the user's Obsidian vault unless creating a brand-new `.cognito.md` file. Always preserve user text outside `<!-- COGNITO:SYNC-START --> ... <!-- COGNITO:SYNC-END -->`.
3. **Graceful Degradation:**
   * Every endpoint must return clean JSON errors (`{"error": "...", "code": "..."}`) and fall back gracefully if Ollama is stopped, an API key is missing, or `OBSIDIAN_VAULT_PATH` is unconfigured.
