# Task Plan: Cognito Local-First Study Workstation

## Goal
Deliver a complete, tested FastAPI + SQLite + vanilla JavaScript Cognito workstation matching every mandatory constraint in RULES.md and UI_UX.md.

## Next Step
Collect user feedback from the running canonical web app and experimental Electron wrapper.

## Current Phase
Complete

## Phases

### Phase 1: Requirements & Discovery
- [x] Read RULES.md and UI_UX.md completely
- [x] Inspect existing architecture and product documents
- [x] Document findings and design
- **Status:** complete

### Phase 2: Planning & Structure
- [x] Select layered single-process architecture
- [x] Write design specification
- [x] Write task-level implementation plan
- **Status:** complete

### Phase 3: Implementation
- [x] Build runtime foundation, schema, and path safety
- [x] Build PDF indexing, search, and rendering
- [x] Build SRS, study, Obsidian, LLM, tools, and API layers
- [x] Build six-view frontend and offline vendor bundle
- **Status:** complete

### Phase 4: Testing & Verification
- [x] Run full pytest suite (40 passed)
- [x] Run frontend policy audit
- [x] Verify server startup and static serving
- **Status:** complete

### Phase 5: Product Audit & Monetization
- [x] Complete launch-readiness UX and feature audit
- [x] Implement Cognito Free / Cognito Pro entitlement model
- [x] Add signed offline license activation and backend enforcement
- [x] Add plan comparison, upgrade, activation, and locked-feature UI
- [x] Document checkout and license fulfillment integration
- **Status:** complete

### Phase 6: Experimental Electron Wrapper
- [x] Create isolated wrapper under build/electron-experimental
- [x] Bundle local Cognito server without changing the canonical app
- [x] Produce AppImage and Debian artifacts and document limitations
- [x] Launch the packaged app and exercise all six workspace entry points
- **Status:** complete

### Phase 7: Delivery
- [x] Write README launch instructions
- [x] Create final TASK_PLAN.md status tracker
- [x] Review outputs, audits, packaged artifacts, and running processes
- **Status:** complete

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Layered FastAPI monolith | Meets single-process/offline requirements while keeping domains testable |
| SQLite FTS5 with LIKE fallback | Preserves fast local search and works on SQLite builds without FTS5 |
| Deterministic local fallbacks | Every core workflow remains functional without LLM or Obsidian |
| Static vanilla SPA | Meets zero-build and offline runtime constraints |
| No git initialization | The supplied environment explicitly says this is not a git repository; avoid altering repository semantics |

## Errors Encountered
| Error | Resolution |
|-------|------------|
| `git diff --stat` failed because the directory is not a repository | Logged environment state; continue without git operations |
| Backend subagent launch returned HTTP 400 for unsupported `claude-sonnet-5-5` gateway model | Resume the same worker using the session model with no override |
| Consolidated verification command had a bash grouping parse error before running | Split verification into explicit sequential commands and rerun fresh |
| A `.git` directory appeared during delegated work despite instructions not to initialize git | Inspection shows a pre-existing remote-backed initial commit containing the project and skills; preserve it and avoid rewriting history |
| Experimental wrapper `npm install` failed with EALLOWGIT because electron-builder 26 requested a Git dependency | Do not bypass package policy; select a registry-only builder release and retry cleanly |
| Automated security-review skill failed because `origin/HEAD...` is not a resolvable revision | Continue with explicit source review and targeted security tests; do not count the failed skill as audit evidence |
| First Linux installer build produced AppImage but `.deb` failed because package homepage and maintainer email were absent | Add neutral repository metadata to the isolated wrapper package and rerun clean packaging |
| Attempted `minimatch@11.1.1` override did not exist in the npm registry | Checked published versions, used 11.0.9, then overrode both direct and nested builder paths; npm audit now reports zero vulnerabilities |
| First real packaged Electron launch failed because `wrapper-lib.cjs` was missing from the ASAR file allowlist | Add the helper explicitly, rebuild both installers, inspect ASAR contents, and relaunch the actual package |
| Combined Electron cleanup/build command exited 144 because `pkill -f` matched its own invoking shell | Separate process inspection/cleanup from the build command; do not reuse the broad self-matching pattern |
