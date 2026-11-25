# Findings

- `RULES.md` and `UI_UX.md` fully specify stack, visual tokens, shell geometry, keyboard behavior, security rules, and all six workspaces.
- Existing `AECHITECTURE.md` (filename as supplied) and `ABOUT.md` reinforce a single FastAPI process, SQLite WAL/FTS5, PyMuPDF ingestion, local Ollama default, OpenAI-compatible providers, and non-destructive Obsidian integration.
- The project initially contained specifications only; there was no application code, package environment, or git repository.
- Binding Obsidian markers use uppercase `COGNITO` as required by RULES.md/UI_UX.md, even where older architecture prose uses mixed case.
- The selected design is documented at `docs/superpowers/specs/2026-11-25-cognito-design.md`; the executable plan is at `docs/superpowers/plans/2026-11-25-cognito-implementation.md`.
- Visual direction: exact mandated graphite/amber palette, native/system type stacks, pane-based dense UI, no ornamental dashboard artifacts. The citation-to-exact-PDF-page split is the principal distinctive interaction.
- Final hardening adds trusted-host enforcement, restrictive CSP and response headers, cross-site mutation rejection, bounded input models, per-client rate limits, owner-only runtime paths, optional capability authentication, and outbound provider URL validation.
- SQLite backup and restore use the online backup API, integrity checks, and owner-only files.
- Dependency audits are clean after upgrading cryptography and the isolated Electron dependency graph and pinning the safe builder `minimatch` resolution.
- The original packaged Electron failure was caused by an incomplete explicit ASAR allowlist, not runtime module resolution; rebuilding with `wrapper-lib.cjs` included fixed the real launch.
- Packaged Electron verification confirms a random loopback origin, isolated desktop bridge, six navigable workspaces, local-only browser dependencies, and a live bundled backend.
- Commercial distribution still needs production icon/desktop metadata, release code signing, an update channel, and externally managed license-signing infrastructure. OS-keyring storage is recommended before storing production provider credentials.
