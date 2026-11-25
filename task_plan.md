# Task Plan: Cognito Local-First Study Workstation

## Goal
Deliver a complete, tested FastAPI + SQLite + vanilla JavaScript Cognito workstation matching every mandatory constraint in RULES.md and UI_UX.md.

## Next Step
Write failing tests for the runtime foundation, SQLite schema, and path sandbox.

## Current Phase
Phase 3

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
- [ ] Build runtime foundation, schema, and path safety
- [ ] Build PDF indexing, search, and rendering
- [ ] Build SRS, study, Obsidian, LLM, tools, and API layers
- [ ] Build six-view frontend and offline vendor bundle
- **Status:** in_progress

### Phase 4: Testing & Verification
- [ ] Run full pytest suite
- [ ] Run frontend policy audit
- [ ] Verify server startup and static serving
- **Status:** pending

### Phase 5: Delivery
- [ ] Write README launch instructions
- [ ] Create final TASK_PLAN.md status tracker
- [ ] Review all outputs and report results
- **Status:** pending

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
