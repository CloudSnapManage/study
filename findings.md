# Findings

- `RULES.md` and `UI_UX.md` fully specify stack, visual tokens, shell geometry, keyboard behavior, security rules, and all six workspaces.
- Existing `AECHITECTURE.md` (filename as supplied) and `ABOUT.md` reinforce a single FastAPI process, SQLite WAL/FTS5, PyMuPDF ingestion, local Ollama default, OpenAI-compatible providers, and non-destructive Obsidian integration.
- The project initially contained specifications only; there was no application code, package environment, or git repository.
- Binding Obsidian markers use uppercase `COGNITO` as required by RULES.md/UI_UX.md, even where older architecture prose uses mixed case.
- The selected design is documented at `docs/superpowers/specs/2026-11-25-cognito-design.md`; the executable plan is at `docs/superpowers/plans/2026-11-25-cognito-implementation.md`.
- Visual direction: exact mandated graphite/amber palette, native/system type stacks, pane-based dense UI, no ornamental dashboard artifacts. The citation-to-exact-PDF-page split is the principal distinctive interaction.
