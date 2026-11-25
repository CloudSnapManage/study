# About Cognito

**Cognito** is a fast, local-first STEM and engineering study studio built to turn scattered lecture PDFs, formula-heavy slides, and past exam papers into a single, structured, and interactive learning workspace.

Designed to run smoothly on everyday student laptops without heavy background services, Cognito pairs a sub-second SQLite + KaTeX engine with **local Ollama models**, **outbound AI routers** (OmniRoute, OpenRouter, Gemini, OpenAI), **native tool-calling agents**, and **bidirectional Obsidian Vault sync**.

---

## 1. Why Cognito Exists

Technical students face four recurring problems during the semester and right before exams:

1. **Fragmented Study Materials:** Lecture slides sit in one folder, past exam questions sit in another, personal notes live in Obsidian, and circuit/vector diagrams stay trapped inside 200-page PDFs.
2. **Guessing What Matters:** Without cross-referencing lecture notes against past exams, it is easy to spend hours studying low-yield chapters while missing high-weightage topics.
3. **Unreliable Generic AI:** Standard chatbots hallucinate formulas, strip out LaTeX formatting, fail to cite exact textbook pages, and force you to repeatedly upload files.
4. **Heavy Software Bloat:** Docker stacks, Electron wrappers, and standalone vector databases consume gigabytes of RAM and slow down your system.

**Cognito** solves all four by keeping your entire knowledge base inside a single local SQLite file (`WAL` mode) with a zero-build Vanilla JS frontend—booting in under 1 second and using ~100 MB of idle RAM.

---

## 2. Core Features in Detail

### A. STEM-Aware PDF & Markdown Ingestion
* **Drop-In Folder Organization:** Drop course files into `./materials/notes/<Subject>/` and `./materials/past_papers/<Subject>/`, or drag and drop PDFs directly into the web interface.
* **Instant SHA-256 Deduplication:** Re-scanning your folders takes milliseconds—unchanged files are skipped automatically without duplicating chunks or resetting your study progress.
* **Automatic LaTeX & Math Repair:** Normalizes broken Unicode math symbols (`∫`, `∑`, `∂`, `∇`, Greek letters, exponents) extracted from PDFs into clean `$ ... $` and `$$ ... $$` KaTeX/Obsidian blocks.
* **Smart Diagram & Circuit Snipper:** Automatically detects embedded figures, circuit schematics, and vector graphs inside PDFs, filters out tiny logos/headers, converts them to compressed `.webp` assets, and links them to nearby `Fig.` or `Diagram` captions.

### B. Exam Radar (Past-Paper Weightage Analyzer)
* **Data-Driven Prioritization:** Cross-references every chapter heading, concept, and equation in your lecture notes against your past exam papers.
* **Yield & Probability Scoring:** Ranks topics from `0–100%` exam probability with appearance counts so you always know which chapters carry the highest weightage.
* **Live Progress Sync:** Checking off mastered topics updates your readiness bar in Cognito and automatically updates your Map of Content (`00_Exam_Radar_MOC.md`) inside Obsidian.

### C. Ask My PDFs & Autonomous Tool-Calling Study Agent
* **Hybrid Retrieval (BM25 + Optional Vectors):** Combines exact keyword and equation lookup (`SQLite FTS5`) with semantic cosine similarity (via local Ollama embeddings when active). If Ollama is offline, keyword and formula search still run at full speed with zero errors.
* **Split-Screen Clickable Citations:** Every answer cites `[Filename.pdf, p. 14]`. Clicking any citation badge renders that exact PDF page side-by-side with your search terms highlighted.
* **Strict Syllabus Mode vs. Tutor Mode:**
  * *Strict Syllabus Mode:* Constrains the AI to answer **only** from your indexed notes and past papers—refusing to guess if a topic is outside your syllabus.
  * *Tutor Mode:* Combines your indexed material with clear, step-by-step explanations.
* **8 Built-In AI Tools (Function Calling):** When connected to a tool-capable model (Qwen, Llama 3.1+, Gemini, Claude, GPT via Ollama, OmniRoute, or OpenRouter), Cognito works as an autonomous study agent that can:
  1. `search_course_materials` — Query specific subjects, lecture notes, or past papers.
  2. `read_pdf_page` — Inspect full page text and linked diagram captions for verification.
  3. `search_formulas_and_diagrams` — Pull exact LaTeX equations and cropped figures.
  4. `get_exam_radar` — Check high-yield topics before generating study plans.
  5. `create_flashcards` — Build new spaced-repetition flashcards straight into your review deck.
  6. `generate_mock_paper` — Assemble a practice test modeled on past-paper patterns.
  7. `save_to_obsidian` — Write formatted Markdown + LaTeX study notes directly into your Obsidian vault.
  8. `update_topic_mastery` — Mark completed topics in Exam Radar.

### D. Today’s 5-Card Recall Sprint (SM-2 Spaced Repetition)
* **Daily Micro-Habit:** Serves a focused daily queue of high-yield conceptual questions, derivation steps, and numerical problems drawn from your weakest topics.
* **Keyboard-First Speed:** Press `Space` to reveal the answer, then rate your recall with `1` (Again), `2` (Hard), `3` (Good), or `4` (Easy). The SM-2 algorithm calculates optimal review intervals automatically.
* **Offline Fallback:** Generates cards using your active LLM when available, or falls back to deterministic definition/formula cards offline.

### E. Step-by-Step Numerical Solution Checker
* Paste a numerical or derivation problem along with your step-by-step working.
* Cognito verifies each algebraic or physics step against the formulas and methods indexed in your course material, pinpointing the exact line where a sign error, unit conversion slip, or wrong formula occurred.

### F. Formula & Diagram Vault + `Ctrl+K` Command Palette
* **Sub-30ms Global Search (`Ctrl+K`):** Press `Ctrl+K` from anywhere in the app to search across all PDF pages, Obsidian notes, extracted formulas, and diagrams instantaneously.
* **1-Click Copy LaTeX:** Copy raw LaTeX strings for any extracted equation with a single click for lab reports, assignments, or Obsidian notes.

### G. Mock Exam & Cheat-Sheet Generator
* Select 2–4 high-weightage topics from Exam Radar to generate a custom practice exam complete with step-by-step LaTeX solutions.
* **5 Export Targets:** Export directly to your **Obsidian Vault**, **Markdown (`.md`)**, **LaTeX source (`.tex`)**, **Print-Ready PDF**, or **Anki CSV**.

### H. Native Bidirectional Obsidian Vault Bridge
* **Clean Vault Structure:** Organizes synced files neatly under `<Vault>/Cognito/`:
  * `00_Exam_Radar_MOC.md` — Auto-updated Map of Content linking all subjects, notes, and PDFs.
  * `<Subject>/Sources/` — Linked PDFs supporting `[[file.pdf#page=X]]` deep page links inside Obsidian.
  * `<Subject>/Notes/` — Formatted `.cognito.md` notes with YAML frontmatter, `$$...$$` display math, `> [!important]` callouts, and `![[diagram.webp]]` embeds.
  * `_assets/` — Extracted circuit and vector diagrams.
* **Non-Destructive Sync:** Auto-synced blocks stay strictly inside `<!-- COGNITO:SYNC-START -->` and `<!-- COGNITO:SYNC-END -->` markers so your personal annotations above or below are never overwritten.
* **Two-Way Search:** Any personal Markdown notes you write inside your Obsidian folder are indexed back into Cognito so your AI assistant can search your own notes alongside your textbooks.

### I. Multi-Provider AI Router
* Switch models on the fly from the chat header or assign dedicated profiles for **Chat & Agent**, **Background Card/Exam Generation**, and **Embeddings**.
* Supports **Ollama (Local)**, **OmniRoute / Local Agent Routers**, **OpenRouter**, **Google Gemini**, **OpenAI**, and any **Custom OpenAI-Compatible** endpoint—with automatic fallback to local Ollama if an external API is unreachable, plus live token tracking.

---

## 3. Typical Daily Study Routine (15–25 Minutes)

1. **Launch Cognito (`< 1s` startup):** Check the top **Health Bar** to verify your SQLite index, Obsidian vault connection, and active LLM profile.
2. **Clear Today's 5-Card Sprint (`5 mins`):** Review due formulas and derivations using keys `1–4`.
3. **Check Exam Radar (`2 mins`):** Pick the highest-probability unmastered topic for your upcoming exam.
4. **Study with the Agent (`10 mins`):** Ask Cognito to break down that topic from your lecture notes and past papers, inspect cited PDF pages side-by-side, and ask it to *"Save a summary note with key formulas to Obsidian and create 3 numerical flashcards."*
5. **Verify Practice Problems (`5 mins`):** Run your homework or past-paper working through the **Numerical Solution Checker** before wrapping up.
