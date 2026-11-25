## 1. Architectural Philosophy & Design Goals
**Cognito** is a local-first, single-process STEM & engineering study studio designed for daily reliability, near-zero idle CPU usage, sub-50ms local search, bidirectional **Obsidian Vault** synchronization, and **multi-provider AI tool calling**.

### Core Constraints
* **Single-Process Footprint:** No Docker, Redis, Postgres, or external vector DB daemons. Everything runs inside one lightweight Python `FastAPI` process backed by a single SQLite file (`WAL` mode).
* **Zero-Build Frontend:** Pure HTML5, CSS3, and Vanilla ES6+ JavaScript with locally bundled **KaTeX** (`frontend/vendor/katex/`). No Node.js, Webpack, or heavy SPA memory overhead.
* **Offline-First Graceful Degradation:**
  * If **Ollama** is offline → Hybrid search falls back seamlessly to SQLite `FTS5` (BM25); flashcard generation falls back to deterministic regex/heuristic extraction.
  * If a **Cloud/Router API** fails or hits rate limits → Auto-falls back to the configured local Ollama profile.
  * If a model lacks native `tools` support → Falls back to a structured ReAct XML tool loop or pure RAG mode.
* **Non-Destructive Obsidian Sync:** Manual user notes in Obsidian are never overwritten. Auto-generated sections are strictly fenced inside `<!-- Cognito:SYNC-START -->` and `<!-- Cognito:SYNC-END -->` markers.

---

## 2. High-Level System Topology

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FRONTEND (Vanilla JS + KaTeX)                         │
│  [Daily Sprint]  [Exam Radar]  [Agent & RAG Chat]  [Vault]  [Mock/Checker]  │
│         │               │               │              │           │        │
│         └───────────────┴───────────────┼──────────────┴───────────┘        │
│                                         │ REST JSON + SSE Stream            │
└─────────────────────────────────────────┼───────────────────────────────────┘
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FASTAPI APPLICATION LAYER                          │
│                                                                             │
│  ┌─────────────────────┐   ┌───────────────────────┐   ┌─────────────────┐  │
│  │  Ingestion Engine   │   │  Agent & Tool Engine  │   │  Obsidian Sync  │  │
│  │  • PyMuPDF Parser   │   │  • OpenAI Tool Schema │   │  • Vault Watcher│  │
│  │  • LaTeX Normalizer │   │  • ReAct XML Fallback │   │  • MOC Builder  │  │
│  │  • Figure Cropper   │   │  • 8 Built-in Tools   │   │  • Safe Fencing │  │
│  └──────────┬──────────┘   └───────────┬───────────┘   └────────┬────────┘  │
│             │                          │                        │           │
│             │              ┌───────────▼───────────┐            │           │
│             │              │ Unified LLM Router    │            │           │
│             │              │ • Ollama / OmniRoute  │            │           │
│             │              │ • OpenRouter / Gemini │            │           │
│             │              │ • OpenAI / Custom     │            │           │
│             │              └───────────┬───────────┘            │           │
│             ▼                          ▼                        ▼           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │              SQLITE STORAGE ENGINE (WAL Mode + FTS5 + Blobs)          │  │
│  │  documents | chunks | chunks_fts | formulas | diagrams | topics |     │  │
│  │  flashcards | llm_profiles | chat_sessions | token_usage              │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
          │                                                       │
          ▼                                                       ▼
┌──────────────────────┐                             ┌────────────────────────┐
│ Local Filesystem     │                             │ Local Obsidian Vault   │
│ ./materials/notes/   │                             │ <Vault>/Cognito/   │
│ ./materials/past_*/  │                             │  ├── 00_Exam_Radar_MOC │
│ ./data/figures/      │                             │  ├── <Subject>/Notes/  │
└──────────────────────┘                             │  └── _assets/          │
                                                     └────────────────────────┘
```

---

## 3. Directory Layout

```text
Cognito/
├── ARCHITECTURE.md
├── README.md
├── requirements.txt
├── .env.example
├── run.sh
├── backend/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, lifespan startup, static mount, health endpoints
│   ├── config.py               # Pydantic settings (.env + runtime DB overrides)
│   ├── database.py             # SQLite connection pool, WAL setup, schema migrations, FTS5 triggers
│   ├── parser.py               # PyMuPDF text/math extraction, figure cropping, SHA-256 hashing
│   ├── search.py               # Hybrid retrieval: FTS5 BM25 + float32 cosine RRF fusion
│   ├── exam_radar.py           # Cross-document frequency & weightage scoring engine
│   ├── srs.py                  # SM-2 spaced repetition scheduler + heuristic/LLM card generator
│   ├── llm_router.py           # Multi-provider OpenAI-compatible async SSE client + fallback logic
│   ├── tools.py                # 8 Pydantic-validated tools + OpenAI JSON schema generator
│   ├── agent.py                # Multi-turn tool-calling execution loop (Native + ReAct fallback)
│   └── obsidian_sync.py        # Bidirectional Obsidian vault reader, formatter, and MOC writer
├── frontend/
│   ├── index.html              # Single-page keyboard-driven shell
│   ├── styles.css              # Dark-mode CSS variables, split-pane grid, responsive layout
│   ├── app.js                  # State store, SSE stream parser, tool trace renderer, Ctrl+K modal
│   └── vendor/
│       └── katex/              # Bundled katex.min.js, katex.min.css, and fonts/ for offline math
├── materials/
│   ├── notes/                  # Drop-in folder: ./materials/notes/<Subject>/*.pdf
│   └── past_papers/            # Drop-in folder: ./materials/past_papers/<Subject>/*.pdf
├── data/                       # Git-ignored runtime state
│   ├── Cognito.db
│   └── figures/                # Cropped WebP diagrams (<doc_hash>_p<page>_<idx>.webp)
└── tests/
    ├── test_parser.py
    ├── test_search.py
    ├── test_agent_tools.py
    ├── test_obsidian_sync.py
    └── test_llm_router.py
```

---

## 4. Database Schema (SQLite + FTS5)

SQLite runs with `PRAGMA journal_mode=WAL;`, `PRAGMA synchronous=NORMAL;`, and `PRAGMA foreign_keys=ON;`.

### Core Tables
1. **`documents`**
   * `id` (INTEGER PRIMARY KEY), `filename` (TEXT), `filepath` (TEXT UNIQUE), `file_hash` (TEXT — SHA-256), `subject` (TEXT), `doc_type` (TEXT: `'note' | 'past_paper' | 'obsidian_note'`), `page_count` (INTEGER), `ingested_at` (TIMESTAMP).
2. **`chunks`**
   * `id` (INTEGER PRIMARY KEY), `document_id` (FK), `page_number` (INTEGER), `chunk_index` (INTEGER), `heading` (TEXT), `content` (TEXT — normalized LaTeX), `embedding` (BLOB — optional `float32` numpy array bytes), `embedding_dim` (INTEGER).
3. **`chunks_fts` (Virtual Table)**
   * `CREATE VIRTUAL TABLE chunks_fts USING fts5(content, heading, subject, filename, content='chunks', content_rowid='id', tokenize='porter unicode61');`
   * Kept in sync automatically via `AFTER INSERT / UPDATE / DELETE` SQLite triggers.
4. **`formulas`**
   * `id` (INTEGER PRIMARY KEY), `document_id` (FK), `page_number` (INTEGER), `subject` (TEXT), `name` (TEXT), `latex` (TEXT), `context` (TEXT).
5. **`diagrams`**
   * `id` (INTEGER PRIMARY KEY), `document_id` (FK), `page_number` (INTEGER), `subject` (TEXT), `image_path` (TEXT), `caption` (TEXT), `width` (INTEGER), `height` (INTEGER).
6. **`topics` (Exam Radar)**
   * `id` (INTEGER PRIMARY KEY), `subject` (TEXT), `topic_name` (TEXT), `note_mentions` (INTEGER), `past_paper_mentions` (INTEGER), `probability_score` (REAL 0–100), `estimated_weightage` (TEXT), `mastered` (BOOLEAN DEFAULT 0).
7. **`flashcards` (SM-2 Spaced Repetition)**
   * `id` (INTEGER PRIMARY KEY), `subject` (TEXT), `topic` (TEXT), `question` (TEXT), `answer` (TEXT), `latex_hint` (TEXT), `source_ref` (TEXT), `ease_factor` (REAL DEFAULT 2.5), `interval_days` (INTEGER DEFAULT 0), `repetitions` (INTEGER DEFAULT 0), `next_review_at` (TIMESTAMP).
8. **`llm_profiles`**
   * `id` (INTEGER PRIMARY KEY), `name` (TEXT UNIQUE), `provider_type` (TEXT: `'ollama' | 'omniroute' | 'openrouter' | 'gemini' | 'openai' | 'custom'`), `base_url` (TEXT), `api_key` (TEXT), `model_id` (TEXT), `tool_mode` (TEXT: `'native' | 'react' | 'disabled'`), `role` (TEXT: `'chat' | 'background' | 'embedding' | 'none'`), `is_fallback` (BOOLEAN DEFAULT 0).
9. **`token_usage`**
   * `id` (INTEGER PRIMARY KEY), `profile_id` (FK), `prompt_tokens` (INTEGER), `completion_tokens` (INTEGER), `created_at` (TIMESTAMP).

---

## 5. Subsystem Deep-Dives

### A. STEM Ingestion & LaTeX Normalization Pipeline (`backend/parser.py`)
1. **Deduplication:** Computes SHA-256 of each file in `./materials/notes/<Subject>/` and `./materials/past_papers/<Subject>/`. Skips unchanged files in <1ms.
2. **Math Symbol Repair:** PDFs often extract math symbols as broken Unicode (`∫`, `∑`, `∂`, `∇`, `α..ω`, `≤`, `≥`, `×`, `÷`, superscripts `²³`). The parser normalizes broken glyphs and wraps detected equation blocks in `$ ... $` (inline) or `$$ ... $$` (display) so KaTeX and Obsidian render them cleanly.
Use code with caution.
3. Formula & Definition Extraction: Regex + structural heuristics identify standalone equations (=, \frac, \int, \sum) and Theorem / Definition / Law blocks, storing them in formulas for instant Ctrl+K lookup.
4. Diagram Extraction: Uses fitz (page.get_images(full=True)) to extract embedded raster figures. Filters out banners/icons (width < 120 or height < 120 or extreme aspect ratios > 6:1), converts to compressed WebP in ./data/figures/, and scans the bounding box below/above the image for Fig., Figure, Circuit, or Diagram captions.

B. Hybrid Retrieval Engine (backend/search.py)

• Step 1 (Lexical BM25): Queries chunks_fts using SQLite bm25(chunks_fts, 1.0, 2.0, 0.5, 0.5) (boosting heading matches).
• Step 2 (Semantic Cosine — Optional): If an embedding profile is active (e.g., Ollama nomic-embed-text), embeds the user query and computes vectorized dot-product similarity via numpy across candidate chunks for that subject.
• Step 3 (Reciprocal Rank Fusion): Combines rankings via $RRF(d) = \frac{1}{60 + r_{bm25}(d)} + \frac{1}{60 + r_{vec}(d)}$. If embeddings are unavailable, returns pure BM25 results with zero errors.

C. Multi-Provider AI Router (backend/llm_router.py)

All providers are normalized onto the OpenAI Chat Completions wire format (POST {base_url}/chat/completions with stream=True):

Provider Template	Default base_url	Auth Header	Notes
Ollama (Local)	http://localhost:11434/v1	Bearer ollama	Auto-discovers installed models via GET /api/tags
OmniRoute	http://localhost:<port>/v1	Bearer <key>	Routes to custom local/cloud model combinations
OpenRouter	https://openrouter.ai	Bearer <key>	Sends HTTP-Referer & X-Title: Cognito
Google Gemini	https://googleapis.com	Bearer <key>	Uses Google's official OpenAI-compatible endpoint
OpenAI	https://openai.com	Bearer <key>	Standard OpenAI endpoint
Custom	User-defined URL	Bearer <key>	Works with vLLM, LM Studio, llama.cpp, Groq, etc.


D. Tool-Calling Agent Loop (backend/agent.py & backend/tools.py)

When Agent Mode is enabled in chat:
1. tools.py generates standard OpenAI JSON Schema definitions from Pydantic input models for all 8 study tools:
	• search_course_materials
	• read_pdf_page
	• search_formulas_and_diagrams
	• get_exam_radar
	• create_flashcards
	• generate_mock_paper
	• save_to_obsidian
	• update_topic_mastery
2. Execution Loop (Max 6 Iterations):
	• Streams tokens to the client via SSE (event: token).
	• If the model emits tool_calls, the backend pauses text streaming, emits event: tool_start (with tool name + sanitized args), executes the local Python function, appends the role: "tool" message to conversation state, emits event: tool_result, and resumes model generation.
	• ReAct Fallback: If a profile has tool_mode == "react", the system prompt injects XML tool instructions (<tool_call>{"name": ..., "arguments": ...}</tool_call>), parses the XML stream, executes the tool, and feeds <tool_result> back into the prompt.

E. Local Obsidian Vault Bridge (backend/obsidian_sync.py)

1. Vault Structure:
   text <OBSIDIAN_VAULT_PATH>/Cognito/ ├── 00_Exam_Radar_MOC.md ├── _assets/ │   └── <doc_hash>_p3_1.webp └── <Subject>/ ├── Sources/ │   └── Chapter_02.pdf └── Notes/ └── Chapter_02.lens.md    
2. 

Generated Markdown Format:
   ```markdown


tags: [Cognito, Physics_II, exam-high-yield]
subject: Physics_II
source_pdf: "[[Chapter_02.pdf]]"
exam_probability: 88%
updated: 2026-11-25


Chapter 02 — Gauss's Law & Applications

[!important] Core Formula
$$\oint \vec{E} \cdot d\vec{A} = \frac{Q_{\text{enc}}}{\varepsilon_0}$$
Source: [[Chapter_02.pdf#page=4]]
![[a1b2c3_p4_0.webp]]
Fig 2.1: Gaussian surface around a cylindrical conductor
   ```
3. Bidirectional Indexing: Scanning the vault indexes all .md files (excluding `.obsidian/`) into SQLite with `doc_type = 'obsidian_note'`, allowing RAG chat and `Ctrl+K` search to reference your personal notes seamlessly.

6. Key API Endpoints & SSE Event Protocol


Method & Path	Purpose
POST /api/ingest/scan	Triggers incremental SHA-256 scan of ./materials/ + Obsidian vault sync
POST /api/ingest/upload	Drag-and-drop PDF upload into a chosen subject & type (note or past_paper)
GET /api/search?q=...	Sub-50ms Ctrl+K hybrid search across chunks, formulas, diagrams, and Obsidian notes
GET /api/pdf/{doc_id}/page/{page}	Renders exact PDF page via PyMuPDF as PNG with optional search-term highlight boxes
POST /api/chat/stream	SSE endpoint (token, tool_start, tool_result, citation, done, error)
GET /api/radar	Returns ranked Exam Radar topics + mastery toggles
GET /api/sprint/today	Fetches due SM-2 flashcards; POST /api/sprint/{id}/review records 1–4 rating
POST /api/checker/verify	Step-by-step numerical/algebraic solution verifier
POST /api/mock/generate	Generates mock exam + exports to Obsidian, .tex, .md, Print PDF, or Anki CSV
GET / POST /api/profiles	CRUD for Ollama, OmniRoute, OpenRouter, Gemini, OpenAI, and Custom LLM profiles
POST /api/obsidian/sync	Forces full bidirectional Obsidian Vault sync & MOC regeneration


7. Security, Performance & Verification Guardrails

• Path Traversal Prevention: All PDF page renders, figure serves, and save_to_obsidian tool calls strictly validate resolved paths (Path.resolve().is_relative_to(...)) against ./materials/, ./data/figures/, and OBSIDIAN_VAULT_PATH.
• Performance Targets:
	• Cold server startup: < 800ms
	• Idle memory usage: < 120 MB
	• Ctrl+K FTS5 search latency: < 30ms
	• KaTeX client math render: < 10ms
• Automated Test Suite (pytest):
	1. test_parser.py: Verifies PDF text/LaTeX normalization, SHA-256 skip logic, and WebP diagram cropping.
	2. test_search.py: Benchmarks FTS5 BM25 + mocked vector RRF ranking accuracy.
	3. test_agent_tools.py: Tests multi-turn tool_calls execution (both Native JSON and ReAct XML fallback) using a mock OpenAI server.
	4. test_obsidian_sync.py: Verifies YAML frontmatter, $$...$$ math blocks, ![[asset]] copying, MOC generation, and non-destructive fence updates.
	5. test_llm_router.py: Verifies multi-provider routing and automatic fallback to Ollama on upstream HTTP 500/timeout.

---

