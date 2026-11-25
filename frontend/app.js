const AppState = {
  view: 'sprint',
  subject: '',
  sidebarCollapsed: false,
  loading: false,
  status: { chunks: 0, obsidian: 'Unset', llm: 'Ollama', tokens: 0 },
  subjects: [],
  sprint: [],
  sprintIndex: 0,
  sprintRevealed: false,
  radar: [],
  radarFilter: 'all',
  messages: [],
  toolTraces: [],
  stream: { active: false, text: '', pendingMath: '', citations: [] },
  pdf: null,
  vault: [],
  vaultType: 'all',
  vaultQuery: '',
  vaultSelected: null,
  mock: { active: false, submitted: false, questions: [], current: 0, answers: {}, flagged: [], remaining: 0, timer: null },
  audit: null,
  palette: { items: [], selected: 0, requestId: 0 },
  settings: {},
  license: { tier: 'free', features: [], valid: true, checkout_url: null },
  chatMode: 'agent',
};

const views = {
  sprint: 'Daily Sprint', radar: 'Exam Radar', chat: 'Agent Chat',
  vault: 'Formula & Diagram Vault', mock: 'Mock Exam', checker: 'Solution Checker',
};

const commands = Object.entries(views).map(([view, label]) => ({ type: 'action', label, view }));
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const escapeHTML = (value = '') => String(value).replace(/[&<>'"]/g, ch => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', "'":'&#39;', '"':'&quot;' })[ch]);
const cleanHTML = value => window.DOMPurify.sanitize(value, { USE_PROFILES: { html: true, mathMl: true, svg: true }, ADD_ATTR: ['data-action','data-id','data-doc-id','data-page','data-term','data-view'] });
const setWorkspace = html => { $('#workspace').innerHTML = cleanHTML(html); renderMath($('#workspace')); };

async function api(path, options = {}) {
  const config = { ...options, headers: { 'Content-Type': 'application/json', ...(options.headers || {}) } };
  const response = await fetch(path, config);
  const type = response.headers.get('content-type') || '';
  const data = type.includes('json') ? await response.json() : await response.text();
  if (!response.ok) {
    const error = new Error(data.error || data.detail || `Request failed (${response.status})`);
    error.code = data.code;
    error.status = response.status;
    if (data.code === 'pro_required') openPlan();
    throw error;
  }
  return data;
}

function isPro() { return AppState.license.tier === 'pro'; }
function proBadge() { return isPro() ? '' : '<span class="pro-badge">PRO</span>'; }

function notify(message, kind = 'info') {
  const toast = $('#toast');
  toast.textContent = message;
  toast.dataset.kind = kind;
  toast.classList.remove('is-hidden');
  window.clearTimeout(notify.timer);
  notify.timer = window.setTimeout(() => toast.classList.add('is-hidden'), 3200);
  $('#status-message').textContent = message;
}

function mathAwareMarkdown(source = '') {
  const tokens = [];
  const withTokens = String(source).replace(/\$\$([\s\S]+?)\$\$|\$([^$\n]+?)\$/g, (_, display, inline) => {
    const latex = display ?? inline;
    try {
      const html = window.katex.renderToString(latex.trim(), { displayMode: display !== undefined, throwOnError: false, strict: 'ignore' });
      const key = `COGNITOMATH${tokens.length}TOKEN`;
      tokens.push([key, html]);
      return key;
    } catch { return escapeHTML(_); }
  });
  let html = window.marked.parse(withTokens, { breaks: true, gfm: true });
  for (const [key, value] of tokens) html = html.replaceAll(key, value);
  return cleanHTML(html);
}

function renderMath(root) {
  if (!root || !window.katex) return;
  $$('[data-tex]', root).forEach(node => {
    try { window.katex.render(node.dataset.tex || '', node, { displayMode: node.dataset.display === 'true', throwOnError: false }); }
    catch { node.textContent = node.dataset.tex || ''; }
  });
}

function splitStableMath(text) {
  let open = null;
  let escaped = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (ch === '\\' && !escaped) { escaped = true; continue; }
    if (ch === '$' && !escaped) {
      const delimiter = text[i + 1] === '$' ? '$$' : '$';
      if (delimiter === '$$') i += 1;
      if (!open) open = { delimiter, index: i - (delimiter.length - 1) };
      else if (open.delimiter === delimiter) open = null;
    }
    escaped = false;
  }
  return open ? [text.slice(0, open.index), text.slice(open.index)] : [text, ''];
}

function updateChrome() {
  $('.middle-shell').classList.toggle('sidebar-collapsed', AppState.sidebarCollapsed);
  $$('.nav-item').forEach(item => item.classList.toggle('is-active', item.dataset.view === AppState.view));
  $('#due-count').textContent = String(AppState.sprint.length);
  $('#chunk-status').textContent = `${AppState.status.chunks} chunks`;
  $('#obsidian-status').textContent = AppState.status.obsidian;
  $('#llm-status').textContent = AppState.status.llm;
  $('#token-status').textContent = String(AppState.status.tokens);
  $('#plan-tier').textContent = AppState.license.tier.toUpperCase();
  $('.plan-indicator')?.classList.toggle('is-pro', isPro());
  $('#db-dot').classList.toggle('ok', true);
  $('#obsidian-dot').classList.toggle('ok', AppState.status.obsidian !== 'Unset');
  $('#llm-dot').classList.toggle('ok', !/offline|unavailable/i.test(AppState.status.llm));
  $('#subject-filter').value = AppState.subject;
  const sidebarButton = $('[data-action="toggle-sidebar"]');
  if (sidebarButton) {
    sidebarButton.setAttribute('aria-expanded', String(!AppState.sidebarCollapsed));
    sidebarButton.setAttribute('aria-label', AppState.sidebarCollapsed ? 'Expand navigation' : 'Collapse navigation');
  }
}

function emptyState(title, detail, action = '', label = '') {
  return `<section class="empty-state"><h2>${escapeHTML(title)}</h2><p>${escapeHTML(detail)}</p>${action ? `<button class="button primary" data-action="${action}">${escapeHTML(label)}</button>` : ''}</section>`;
}

function sourceBadge(item = {}) {
  const filename = item.filename || item.source_filename || item.source_ref || 'Local source';
  const page = item.page_number || item.page || 1;
  if (!item.document_id && !item.doc_id) return `<span class="badge">${escapeHTML(filename)}</span>`;
  return `<button class="citation" data-action="open-citation" data-doc-id="${Number(item.document_id || item.doc_id)}" data-page="${Number(page)}" data-term="${escapeHTML(item.term || item.topic || '')}">${escapeHTML(filename)}, p. ${Number(page)}</button>`;
}

function renderSprint() {
  const card = AppState.sprint[AppState.sprintIndex];
  const content = !card ? emptyState('No cards due', 'Scan PDFs or add a formula from the Vault to create your first review card.', 'scan-materials', 'Scan Folder') : `
    <div class="sprint-stage">
      <div class="progress-meta metric"><span>Card ${AppState.sprintIndex + 1} of ${AppState.sprint.length}</span><span>Due now</span></div>
      <div class="progress-track"><span style="width:${((AppState.sprintIndex + 1) / AppState.sprint.length) * 100}%"></span></div>
      <article class="study-card">
        <header class="card-meta"><span>${escapeHTML(card.subject || 'General')} · ${escapeHTML(card.topic || 'Review')}</span>${sourceBadge(card)}</header>
        <div class="card-body">${mathAwareMarkdown(card.question || '')}</div>
        ${AppState.sprintRevealed ? `<section class="answer-panel">${mathAwareMarkdown(card.answer || '')}${card.latex_hint ? `<div class="equation-block"><span data-tex="${escapeHTML(card.latex_hint)}" data-display="true"></span></div>` : ''}</section><div class="grade-dock">${[['1','Again','<1d'],['2','Hard','1d'],['3','Good','3d'],['4','Easy','6d']].map(([key,label,interval]) => `<button data-action="grade-card" data-grade="${key}"><kbd>${key}</kbd> ${label} <span class="metric">(${interval})</span></button>`).join('')}</div>` : `<button class="reveal-button" data-action="reveal-card">Show Answer <kbd>Space</kbd></button>`}
      </article>
    </div>`;
  setWorkspace(`<section class="view sprint-view"><header class="view-header"><h1>Daily Sprint</h1><span class="metric">SM-2 queue · ${AppState.sprint.length} due</span></header><div class="scroll-pane">${content}</div></section>`);
}

function filteredRadar() {
  return AppState.radar.filter(topic => AppState.radarFilter === 'all' || (AppState.radarFilter === 'high' ? Number(topic.probability_score || topic.probability || 0) >= 70 : !topic.mastered));
}

function renderRadar() {
  const rows = filteredRadar();
  const body = rows.length ? `<div class="scroll-pane"><table><thead><tr><th>Done</th><th>Topic / Concept</th><th>Subject</th><th class="numeric">Notes</th><th class="numeric">Past Papers</th><th class="numeric">Exam Probability</th><th>Action</th></tr></thead><tbody>${rows.map(topic => {
    const probability = Math.round(Number(topic.probability_score || topic.probability || 0));
    return `<tr><td><input type="checkbox" data-action="toggle-mastery" data-id="${Number(topic.id)}" ${topic.mastered ? 'checked' : ''} aria-label="Mark ${escapeHTML(topic.topic_name || topic.name)} mastered"></td><td><div class="topic-name">${escapeHTML(topic.topic_name || topic.name)}</div><div class="subtext">${escapeHTML(topic.source_filename || 'Indexed materials')}</div></td><td><span class="badge">${escapeHTML(topic.subject || 'General')}</span></td><td class="numeric">${Number(topic.note_mentions || 0)}</td><td class="numeric">${Number(topic.past_paper_mentions || 0)}</td><td><div class="probability"><div class="frequency-bar"><i style="width:${Math.min(100,Math.max(0,probability))}%"></i></div><span>${probability}%</span></div></td><td><button class="text-action" data-action="study-topic" data-topic="${escapeHTML(topic.topic_name || topic.name)}">Study in Chat</button></td></tr>`;
  }).join('')}</tbody></table></div>` : emptyState('No exam topics indexed', 'Add PDFs to materials/notes and materials/past_papers, then scan the folder.', 'scan-materials', 'Scan Folder');
  setWorkspace(`<section class="view radar-view"><header class="view-header"><h1>Exam Radar</h1><button class="button" data-action="sync-obsidian">Sync MOC to Obsidian</button></header><div class="filterbar"><div class="filters">${[['all','All'],['high','High Yield >=70%'],['unmastered','Unmastered Only']].map(([id,label]) => `<button class="filter-chip ${AppState.radarFilter === id ? 'is-active':''}" data-action="radar-filter" data-filter="${id}" aria-pressed="${AppState.radarFilter === id}">${label}</button>`).join('')}</div><span class="metric">${rows.length} topics</span></div>${body}</section>`);
}

function traceHTML(trace) {
  return `<details class="tool-trace"><summary>Tool: ${escapeHTML(trace.name)}(${escapeHTML(trace.arguments || '')}) — ${escapeHTML(trace.summary || 'complete')}</summary><pre>${escapeHTML(JSON.stringify(trace.result || {}, null, 2))}</pre></details>`;
}

function messageHTML(message) {
  const citations = (message.citations || []).map(item => sourceBadge({ document_id: item.docId, page_number: item.page, filename: item.filename })).join(' ');
  return `<article class="message ${message.role}">${message.role === 'assistant' ? mathAwareMarkdown(message.content || '') : `<p>${escapeHTML(message.content || '')}</p>`}${citations ? `<p>${citations}</p>` : ''}</article>`;
}

function renderChat() {
  const messages = [...AppState.messages];
  if (AppState.stream.active || AppState.stream.text) messages.push({ role: 'assistant', content: AppState.stream.text, citations: AppState.stream.citations || [] });
  const stream = messages.length ? messages.map(messageHTML).join('') + AppState.toolTraces.map(traceHTML).join('') : emptyState('No active thread', 'Ask a question grounded in indexed course materials. Citations open the exact PDF page.', '', '');
  const pdf = AppState.pdf ? `<aside class="pdf-inspector"><header class="pdf-controls"><button class="icon-button" data-action="close-pdf" aria-label="Close PDF">×</button><span class="page-label">${escapeHTML(AppState.pdf.filename || 'PDF')} · Page ${Number(AppState.pdf.page)}</span><div class="segmented"><button class="is-active">Fit</button><button>150%</button></div></header><div class="pdf-canvas"><img alt="Rendered PDF page ${Number(AppState.pdf.page)}" src="/api/pdf/${Number(AppState.pdf.docId)}/page/${Number(AppState.pdf.page)}?term=${encodeURIComponent(AppState.pdf.term || '')}"></div></aside>` : '';
  setWorkspace(`<section class="view chat-view"><header class="chat-toolbar"><div class="header-actions"><select id="profile-select" aria-label="Model profile"><option>${escapeHTML(AppState.status.llm)}</option></select><div class="segmented" aria-label="Chat mode"><button class="${AppState.chatMode==='agent'?'is-active':''}" data-action="chat-mode" data-mode="agent" aria-pressed="${AppState.chatMode==='agent'}">Agent + Tools ${proBadge()}</button><button class="${AppState.chatMode==='strict'?'is-active':''}" data-action="chat-mode" data-mode="strict" aria-pressed="${AppState.chatMode==='strict'}">Strict Syllabus</button><button class="${AppState.chatMode==='tutor'?'is-active':''}" data-action="chat-mode" data-mode="tutor" aria-pressed="${AppState.chatMode==='tutor'}">Tutor</button></div></div><button class="button" data-action="save-thread">Save Thread to Obsidian</button></header><div class="chat-split ${AppState.pdf ? 'has-pdf':''}"><section class="chat-pane"><div class="message-stream" id="message-stream">${stream}</div><form class="chat-composer" id="chat-form"><textarea name="message" placeholder="Ask about indexed notes or past papers" aria-label="Message"></textarea><button class="button primary" type="submit" ${AppState.stream.active ? 'disabled':''}>Send <kbd>Enter</kbd></button></form></section>${pdf}</div></section>`);
  const pane = $('#message-stream'); if (pane) pane.scrollTop = pane.scrollHeight;
}

function filteredVault() {
  const query = AppState.vaultQuery.toLowerCase();
  return AppState.vault.filter(item => (AppState.vaultType === 'all' || (item.type || 'formula') === AppState.vaultType) && (!query || `${item.name} ${item.context || ''}`.toLowerCase().includes(query)));
}

function renderVault() {
  const items = filteredVault();
  let selected = items.find(item => String(item.id) === String(AppState.vaultSelected)) || items[0];
  if (selected) AppState.vaultSelected = selected.id;
  const left = items.length ? items.map(item => `<button class="master-row ${String(item.id) === String(AppState.vaultSelected) ? 'is-active':''}" data-action="select-vault" data-id="${Number(item.id)}"><strong>${escapeHTML(item.name || item.caption || 'Untitled')}</strong><span class="master-row-meta"><span class="badge">${escapeHTML(item.subject || 'General')}</span><span class="metric">p. ${Number(item.page_number || 1)}</span></span></button>`).join('') : emptyState('Vault is empty', 'Scan course PDFs to extract formulas and diagrams.', 'scan-materials', 'Scan Folder');
  const detail = selected ? `<article><header class="detail-header"><div><h1>${escapeHTML(selected.name || selected.caption || 'Untitled')}</h1>${sourceBadge(selected)}</div><div class="header-actions"><button class="button" data-action="copy-tex" data-tex="${escapeHTML(selected.latex || '')}">Copy TeX</button><button class="button primary" data-action="add-to-sprint" data-id="${Number(selected.id)}">Add to Sprint</button></div></header><div class="equation-block"><span data-tex="${escapeHTML(selected.latex || selected.context || '')}" data-display="true"></span><button class="button copy-equation" data-action="copy-tex" data-tex="${escapeHTML(selected.latex || '')}">Copy TeX</button></div><h2 class="section-label">Variable legend</h2><table class="legend-table"><thead><tr><th>Symbol</th><th>Meaning</th><th>SI Unit</th></tr></thead><tbody>${(selected.variables || []).map(v => `<tr><td class="metric">${escapeHTML(v.symbol)}</td><td>${escapeHTML(v.meaning)}</td><td class="metric">${escapeHTML(v.unit || '—')}</td></tr>`).join('') || '<tr><td colspan="3" class="subtext">No variable legend extracted.</td></tr>'}</tbody></table><h2 class="section-label">Related past exam appearances</h2><p class="subtext">${escapeHTML(selected.exam_appearances || 'No linked past-paper occurrence.')}</p></article>` : '';
  setWorkspace(`<section class="view vault-view"><div class="vault-filterbar"><div class="segmented">${[['all','All'],['formula','Formulas'],['diagram','Diagrams'],['definition','Definitions']].map(([id,label]) => `<button class="${AppState.vaultType === id ? 'is-active':''}" data-action="vault-filter" data-filter="${id}" aria-pressed="${AppState.vaultType === id}">${label}</button>`).join('')}</div><input id="vault-search" type="search" value="${escapeHTML(AppState.vaultQuery)}" placeholder="Filter vault  /" aria-label="Filter vault"></div><div class="master-detail"><div class="master-list">${left}</div><div class="detail-pane">${detail}</div></div></section>`);
}

function renderMock() {
  const exam = AppState.mock;
  if (!exam.active && !exam.submitted) {
    setWorkspace(`<section class="view mock-view"><header class="exam-controls"><div class="config-controls"><select id="mock-subject"><option value="">All subjects</option>${AppState.subjects.map(s => `<option>${escapeHTML(s.name || s.subject || s)}</option>`).join('')}</select><select id="mock-count"><option>5</option><option>10</option><option>20</option></select><select id="mock-bias"><option value="past">Past Papers Weighted</option><option value="balanced">Balanced</option></select></div><button class="button primary" data-action="start-mock">Start Timed Exam</button></header><div class="scroll-pane">${emptyState('Configure a mock exam', 'Questions are assembled from indexed past papers and high-yield topics.', '', '')}</div></section>`); return;
  }
  const q = exam.questions[exam.current] || {};
  const matrix = exam.questions.map((_, i) => `<button class="${exam.answers[i] ? 'answered':''} ${exam.flagged.includes(i) ? 'flagged':''}" data-action="mock-question" data-index="${i}">${i + 1}</button>`).join('');
  const stage = exam.submitted ? `<div class="question-paper"><h2>${escapeHTML(q.prompt || q.question || '')}</h2><div class="rubric-grid"><section><h3>Your Response</h3><p>${escapeHTML(exam.answers[exam.current] || 'No response')}</p></section><section><h3>Model Solution</h3>${mathAwareMarkdown(q.solution || 'No model solution available.')}</section></div><h3>Rubric <span class="metric">${Number(q.score || 0)} / ${Number(q.marks || 5)}</span></h3><p>${escapeHTML(q.feedback || 'Review the model solution and source citations.')}</p><button class="button primary" data-action="missed-to-sprint">Send Missed Concepts to Daily Sprint</button></div>` : `<div class="question-paper"><div class="question-meta"><span>Question ${exam.current + 1}</span><span class="metric">${Number(q.marks || 5)} Marks</span></div><h2>${escapeHTML(q.prompt || q.question || '')}</h2><textarea id="mock-answer" placeholder="Write your answer or derivation">${escapeHTML(exam.answers[exam.current] || '')}</textarea><div class="stage-controls"><button class="button" data-action="mock-prev">Previous</button><button class="button" data-action="mock-next">Next</button></div></div>`;
  setWorkspace(`<section class="view mock-view"><header class="exam-controls"><div class="timer ${exam.remaining < 300 ? 'error-text':''}">${formatTime(exam.remaining)}</div><button class="button ${exam.flagged.includes(exam.current) ? 'primary':''}" data-action="toggle-flag">Flag for Review <kbd>F</kbd></button>${exam.submitted ? '<button class="button" data-action="reset-mock">New Exam</button>' : '<button class="button primary" data-action="submit-mock">Submit Exam</button>'}</header><div class="exam-layout"><aside class="question-navigator"><h2 class="section-label">Questions</h2><div class="question-grid">${matrix}</div></aside><div class="question-stage">${stage}</div></div></section>`);
}

function renderChecker() {
  const audit = AppState.audit;
  const right = audit ? `<div class="audit-summary">${escapeHTML(audit.summary || 'Audit complete')}</div>${(audit.steps || []).map((step, i) => `<article class="audit-row ${step.valid === false ? 'fail':''}"><span class="audit-icon">${step.valid === false ? 'X':'OK'}</span><div><strong>Step ${i + 1}</strong><p>${escapeHTML(step.note || step.message || '')}</p>${step.expected ? `<p class="metric">Expected ${escapeHTML(step.expected)} · found ${escapeHTML(step.found || '')}</p>`:''}${step.citation ? sourceBadge(step.citation):''}${step.valid === false ? '<p><button class="button" data-action="error-flashcard" data-step="'+i+'">Create Error Flashcard</button></p>':''}</div></article>`).join('')}` : emptyState('No audit run', 'Enter a problem and one derivation step per line, then audit the work.', '', '');
  setWorkspace(`<section class="view checker-view"><header class="view-header"><h1>Solution Checker</h1><span class="metric">Ctrl+Enter to audit</span></header><div class="checker-split"><section class="checker-pane"><h2 class="section-label">Your derivation</h2><textarea class="problem-input" id="problem-input" placeholder="Paste the problem statement"></textarea><div class="line-editor"><div class="line-numbers" id="line-numbers">1</div><textarea id="derivation-input" placeholder="Enter one step per line"></textarea></div><div class="checker-actions"><button class="button" data-action="toggle-preview">Live Preview</button><button class="button primary" data-action="audit-steps">Audit Steps <kbd>Ctrl Enter</kbd></button></div></section><section class="checker-pane"><h2 class="section-label">Step verification</h2>${right}</section></div></section>`);
}

function renderCurrentView() {
  updateChrome();
  ({ sprint: renderSprint, radar: renderRadar, chat: renderChat, vault: renderVault, mock: renderMock, checker: renderChecker })[AppState.view]();
}

async function loadStatus() {
  try {
    const [data, license] = await Promise.all([api('/api/health'), api('/api/license/status')]);
    AppState.license = license;
    AppState.status = {
      chunks: Number(data.chunks ?? data.chunk_count ?? 0),
      obsidian: data.obsidian?.status || data.obsidian || 'Unset',
      llm: data.llm?.profile || data.llm || 'Ollama',
      tokens: Number(data.tokens || 0),
    };
    AppState.subjects = data.subjects || [];
  } catch (error) { notify(`Health check: ${error.message}`, 'error'); }
  renderSubjects(); updateChrome();
}

function renderSubjects() {
  const options = ['<option value="">All subjects</option>'];
  $('#subject-list').innerHTML = cleanHTML(AppState.subjects.map(item => {
    const name = item.name || item.subject || item;
    const count = item.count || item.documents || 0;
    options.push(`<option value="${escapeHTML(name)}">${escapeHTML(name)}</option>`);
    return `<div class="subject-row"><span>${escapeHTML(name)}</span><span class="metric">${Number(count)}</span></div>`;
  }).join(''));
  $('#subject-filter').innerHTML = cleanHTML(options.join(''));
}

async function loadView(view = AppState.view) {
  if ((view === 'mock' || view === 'checker') && !isPro()) { openPlan(); return; }
  AppState.view = view;
  try {
    if (view === 'sprint') { const data = await api(`/api/sprint/today${AppState.subject ? `?subject=${encodeURIComponent(AppState.subject)}`:''}`); AppState.sprint = data.cards || data.items || data || []; AppState.sprintIndex = Math.min(AppState.sprintIndex, Math.max(0,AppState.sprint.length - 1)); }
    if (view === 'radar') { const data = await api(`/api/radar${AppState.subject ? `?subject=${encodeURIComponent(AppState.subject)}`:''}`); AppState.radar = data.topics || data.items || data || []; }
    if (view === 'vault') { const data = await api(`/api/vault${AppState.subject ? `?subject=${encodeURIComponent(AppState.subject)}`:''}`); AppState.vault = data.items || data.formulas || data || []; }
  } catch (error) { notify(error.message, 'error'); }
  renderCurrentView();
  const workspace = $('#workspace');
  if (workspace) workspace.focus();
}

async function scanMaterials() {
  notify('Scanning materials...');
  try {
    const result = await api('/api/ingest/scan', { method: 'POST', body: '{}' });
    notify(`Scan complete: ${Number(result.indexed || result.documents_indexed || 0)} indexed, ${Number(result.skipped || 0)} unchanged`);
    await loadStatus(); await loadView(AppState.view);
  } catch (error) { notify(`Scan failed: ${error.message}`, 'error'); }
}

async function gradeCard(grade) {
  const card = AppState.sprint[AppState.sprintIndex]; if (!card) return;
  try {
    const result = await api(`/api/sprint/${Number(card.id)}/review`, { method: 'POST', body: JSON.stringify({ rating: Number(grade) }) });
    notify(`Review saved · next in ${Number(result.interval_days || 0)}d`);
    AppState.sprint.splice(AppState.sprintIndex, 1); AppState.sprintRevealed = false;
    if (AppState.sprintIndex >= AppState.sprint.length) AppState.sprintIndex = 0;
    renderSprint(); updateChrome();
  } catch (error) { notify(error.message, 'error'); }
}

async function sendChat(message) {
  if (!message.trim() || AppState.stream.active) return;
  AppState.messages.push({ role: 'user', content: message.trim() });
  AppState.stream = { active: true, text: '', pendingMath: '', citations: [] };
  AppState.toolTraces = [];
  renderChat();
  try {
    const response = await fetch('/api/chat/stream', { method: 'POST', headers: { 'Content-Type':'application/json' }, body: JSON.stringify({ message, messages: AppState.messages, subject: AppState.subject, mode: AppState.chatMode }) });
    if (!response.ok || !response.body) throw new Error(`Chat unavailable (${response.status})`);
    const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = '';
    while (true) {
      const { value, done } = await reader.read(); if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split('\n\n'); buffer = events.pop() || '';
      for (const raw of events) processSSE(raw);
    }
    if (buffer.trim()) processSSE(buffer);
  } catch (error) {
    AppState.stream.text += `\n\nChat error: ${error.message}`;
  } finally {
    const finalText = AppState.stream.text + AppState.stream.pendingMath;
    if (finalText.trim()) AppState.messages.push({ role: 'assistant', content: finalText, citations: AppState.stream.citations || [] });
    AppState.stream = { active: false, text: '', pendingMath: '', citations: [] };
    renderChat();
  }
}

function processSSE(raw) {
  let event = 'message'; const dataLines = [];
  raw.split('\n').forEach(line => { if (line.startsWith('event:')) event = line.slice(6).trim(); if (line.startsWith('data:')) dataLines.push(line.slice(5).trim()); });
  if (!dataLines.length) return;
  let data; try { data = JSON.parse(dataLines.join('\n')); } catch { data = { token: dataLines.join('\n') }; }
  if (event === 'token' || event === 'message') {
    const combined = AppState.stream.pendingMath + (data.token ?? data.text ?? data.content ?? '');
    const [stable, pending] = splitStableMath(combined);
    AppState.stream.text += stable; AppState.stream.pendingMath = pending;
  } else if (event === 'tool_start') AppState.toolTraces.push({ name: data.name || 'tool', arguments: JSON.stringify(data.arguments || {}) });
  else if (event === 'tool_result') { const trace = AppState.toolTraces.findLast(item => item.name === data.name && !item.result) || AppState.toolTraces.at(-1); if (trace) { trace.result = data.result ?? data.results; trace.summary = data.summary || `${Number(data.count || 0)} results`; } }
  else if (event === 'citation') {
    const page = data.page ?? data.page_number ?? 1;
    AppState.stream.citations = [...(AppState.stream.citations || []), { docId: data.document_id, page, filename: data.filename || 'Source' }];
  }
  else if (event === 'error') AppState.stream.text += `\n\n${data.error || 'Model stream failed.'}`;
  renderChat();
}

async function openPalette(query = '') {
  $('#palette').classList.remove('is-hidden');
  $('#palette-input').value = query; $('#palette-input').focus();
  await updatePalette(query);
}

async function updatePalette(query) {
  const requestId = ++AppState.palette.requestId;
  let items = commands.filter(item => item.label.toLowerCase().includes(query.toLowerCase()));
  if (query.trim()) {
    try { const data = await api(`/api/search?q=${encodeURIComponent(query)}&limit=8`); items = [...items, ...(data.results || data.items || data || []).map(item => ({ ...item, type: item.type || 'search', label: item.name || item.heading || item.content?.slice(0,70) || 'Search result' }))]; }
    catch { /* workspace actions remain available offline */ }
  }
  if (requestId !== AppState.palette.requestId) return;
  AppState.palette.items = items; AppState.palette.selected = 0; renderPaletteResults();
}

function renderPaletteResults() {
  $('#palette-results').innerHTML = cleanHTML(AppState.palette.items.map((item, i) => `<button class="command-result ${i === AppState.palette.selected ? 'is-selected':''}" data-action="palette-result" data-index="${i}" role="option" aria-selected="${i === AppState.palette.selected}"><span>${escapeHTML(item.label)}</span><span class="metric">${escapeHTML(item.type)}</span></button>`).join('') || '<div class="empty-state"><p>No matching commands or indexed material.</p></div>');
}

function renderPlan() {
  const license = AppState.license;
  const metadata = license.tier === 'pro' ? `<dl class="license-meta"><dt>Status</dt><dd>${license.in_grace ? 'Offline grace' : 'Active'}</dd><dt>License</dt><dd>${escapeHTML(license.license_id || 'Pro')}</dd><dt>Customer</dt><dd>${escapeHTML(license.customer || 'Licensed')}</dd><dt>Renews / expires</dt><dd>${escapeHTML(license.expires_at || 'Perpetual')}</dd></dl>` : '';
  $('#plan-content').innerHTML = cleanHTML(`
    <section class="plan-summary"><span class="plan-name">Cognito ${license.tier === 'pro' ? 'Pro' : 'Free'}</span><p>${license.tier === 'pro' ? 'Advanced study workflows are active on this device.' : 'Local study core. Upgrade for advanced synthesis and integrations.'}</p>${metadata}</section>
    <div class="tier-comparison">
      <section><header><strong>Free</strong><span>Active core</span></header><ul><li>Unlimited local PDF indexing</li><li>Search and exact-page verifier</li><li>Daily Sprint and Exam Radar</li><li>Local retrieval chat</li></ul></section>
      <section class="pro-tier"><header><strong>Pro</strong><span>Licensed workflows</span></header><ul><li>Everything in Free</li><li>Mock exams and Solution Checker</li><li>Obsidian sync and thread export</li><li>Custom model providers and exports</li></ul></section>
    </div>
    ${license.tier === 'pro' ? '<button class="button" data-action="deactivate-license">Deactivate on this device</button>' : `<div class="plan-actions">${license.checkout_url ? '<button class="button primary" data-action="view-pro">View Pro</button>' : '<p class="subtext">Checkout URL is not configured. Set COGNITO_CHECKOUT_URL before commercial distribution.</p>'}<label>License token<textarea id="license-token" placeholder="Paste signed license token"></textarea></label><button class="button" data-action="activate-license">Activate license</button></div>`}
  `);
}

function openPlan() { renderPlan(); $('#plan-drawer').classList.remove('is-hidden'); }
function closeOverlays() { $('#palette').classList.add('is-hidden'); $('#settings').classList.add('is-hidden'); $('#plan-drawer').classList.add('is-hidden'); }
function executePalette(index) {
  const item = AppState.palette.items[index]; if (!item) return;
  closeOverlays();
  if (item.view) loadView(item.view);
  else if (item.document_id || item.doc_id) { AppState.view = 'chat'; AppState.pdf = { docId: item.document_id || item.doc_id, page: item.page_number || 1, term: $('#palette-input').value, filename: item.filename }; renderChat(); }
}

function formatTime(seconds) { const safe = Math.max(0, Number(seconds || 0)); return `${String(Math.floor(safe / 60)).padStart(2,'0')}:${String(safe % 60).padStart(2,'0')}`; }
function startTimer() { clearInterval(AppState.mock.timer); AppState.mock.timer = setInterval(() => { if (AppState.mock.remaining > 0 && AppState.mock.active) { AppState.mock.remaining -= 1; const timer = $('.timer'); if (timer) timer.textContent = formatTime(AppState.mock.remaining); } }, 1000); }
function saveMockAnswer() { const field = $('#mock-answer'); if (field) AppState.mock.answers[AppState.mock.current] = field.value; }

async function handleAction(target) {
  const action = target.dataset.action;
  if (action === 'navigate') await loadView(target.dataset.view);
  else if (action === 'toggle-sidebar') { AppState.sidebarCollapsed = !AppState.sidebarCollapsed; updateChrome(); }
  else if (action === 'open-palette') openPalette();
  else if (action === 'open-settings') $('#settings').classList.remove('is-hidden');
  else if (action === 'open-plan') openPlan();
  else if (action === 'chat-mode') { if (target.dataset.mode === 'agent' && !isPro()) { openPlan(); } else { AppState.chatMode=target.dataset.mode; renderChat(); } }
  else if (action === 'close-overlay') closeOverlays();
  else if (action === 'scan-materials') scanMaterials();
  else if (action === 'reveal-card') { AppState.sprintRevealed = true; renderSprint(); }
  else if (action === 'grade-card') gradeCard(target.dataset.grade);
  else if (action === 'radar-filter') { AppState.radarFilter = target.dataset.filter; renderRadar(); }
  else if (action === 'toggle-mastery') { try { await api(`/api/radar/${Number(target.dataset.id)}/mastery`, { method:'POST', body:JSON.stringify({ mastered: target.checked }) }); notify('Mastery updated'); } catch (e) { target.checked = !target.checked; notify(e.message,'error'); } }
  else if (action === 'study-topic') { AppState.view='chat'; await sendChat(`Teach me ${target.dataset.topic} using only my indexed course materials.`); }
  else if (action === 'sync-obsidian') { try { const result=await api('/api/obsidian/sync',{method:'POST',body:'{}'}); notify(result.message || 'Obsidian MOC synced'); } catch(e){notify(e.message,'error');} }
  else if (action === 'open-citation') { AppState.pdf={docId:target.dataset.docId,page:target.dataset.page,term:target.dataset.term,filename:target.textContent.split(',')[0]}; AppState.view='chat'; renderChat(); }
  else if (action === 'close-pdf') { AppState.pdf=null; renderChat(); }
  else if (action === 'select-vault') { AppState.vaultSelected=target.dataset.id; renderVault(); }
  else if (action === 'vault-filter') { AppState.vaultType=target.dataset.filter; renderVault(); }
  else if (action === 'copy-tex') { await navigator.clipboard.writeText(target.dataset.tex || ''); notify('TeX copied'); }
  else if (action === 'add-to-sprint') { try { await api(`/api/vault/${Number(target.dataset.id)}/flashcard`,{method:'POST',body:'{}'}); notify('Added to Daily Sprint'); } catch(e){notify(e.message,'error');} }
  else if (action === 'start-mock') { try { const data=await api('/api/mock/generate',{method:'POST',body:JSON.stringify({subject:$('#mock-subject').value,count:Number($('#mock-count').value),source_bias:$('#mock-bias').value==='past'?'past_papers_weighted':'balanced'})}); AppState.mock={active:true,submitted:false,questions:data.questions||data.items||[],current:0,answers:{},flagged:[],remaining:Number(data.duration_seconds||3600),timer:null}; startTimer(); renderMock(); } catch(e){notify(e.message,'error');} }
  else if (action === 'mock-question') { saveMockAnswer(); AppState.mock.current=Number(target.dataset.index); renderMock(); }
  else if (action === 'mock-prev' || action === 'mock-next') { saveMockAnswer(); AppState.mock.current=Math.max(0,Math.min(AppState.mock.questions.length-1,AppState.mock.current+(action==='mock-next'?1:-1))); renderMock(); }
  else if (action === 'toggle-flag') { const i=AppState.mock.current; AppState.mock.flagged=AppState.mock.flagged.includes(i)?AppState.mock.flagged.filter(x=>x!==i):[...AppState.mock.flagged,i]; renderMock(); }
  else if (action === 'submit-mock') { saveMockAnswer(); try { const data=await api('/api/mock/grade',{method:'POST',body:JSON.stringify({questions:AppState.mock.questions,answers:AppState.mock.answers})}); AppState.mock.questions=data.questions||AppState.mock.questions; AppState.mock.submitted=true; AppState.mock.active=false; clearInterval(AppState.mock.timer); renderMock(); } catch(e){notify(e.message,'error');} }
  else if (action === 'reset-mock') { AppState.mock={active:false,submitted:false,questions:[],current:0,answers:{},flagged:[],remaining:0,timer:null}; renderMock(); }
  else if (action === 'missed-to-sprint') { try { await api('/api/mock/missed-to-sprint',{method:'POST',body:JSON.stringify({questions:AppState.mock.questions})}); notify('Missed concepts added to Daily Sprint'); } catch(e){notify(e.message,'error');} }
  else if (action === 'toggle-preview') {
    const derivation = $('#derivation-input')?.value || '';
    AppState.audit = { summary: 'Live derivation preview', steps: derivation.split('\n').filter(Boolean).map(note => ({ valid: true, note })) };
    renderChecker();
  }
  else if (action === 'audit-steps') auditSteps();
  else if (action === 'error-flashcard') { try { await api('/api/checker/flashcard',{method:'POST',body:JSON.stringify({step:Number(target.dataset.step),audit:AppState.audit})}); notify('Error flashcard created'); } catch(e){notify(e.message,'error');} }
  else if (action === 'palette-result') executePalette(Number(target.dataset.index));
  else if (action === 'test-connection') testConnection();
  else if (action === 'view-pro') { if (AppState.license.checkout_url) window.open(AppState.license.checkout_url, '_blank', 'noopener'); }
  else if (action === 'activate-license') { const token=$('#license-token')?.value.trim(); if(!token){notify('Paste a license token','error');return;} try{AppState.license=await api('/api/license/activate',{method:'POST',body:JSON.stringify({token})});updateChrome();renderPlan();notify('Cognito Pro activated');}catch(e){notify(e.message,'error');} }
  else if (action === 'deactivate-license') { AppState.license=await api('/api/license/deactivate',{method:'POST',body:'{}'});updateChrome();renderPlan();notify('License deactivated'); }
  else if (action === 'save-thread') { try { await api('/api/obsidian/thread',{method:'POST',body:JSON.stringify({messages:AppState.messages})}); notify('Thread saved to Obsidian'); } catch(e){notify(e.message,'error');} }
}

async function auditSteps() {
  const problem=$('#problem-input')?.value||''; const derivation=$('#derivation-input')?.value||'';
  if (!derivation.trim()) { notify('Enter at least one derivation step','error'); return; }
  try { AppState.audit=await api('/api/checker/verify',{method:'POST',body:JSON.stringify({problem,derivation,steps:derivation.split('\n').filter(Boolean)})}); renderChecker(); }
  catch(e){notify(e.message,'error');}
}

async function testConnection() {
  const data=Object.fromEntries(new FormData($('#settings-form')));
  try { const result=await api('/api/profiles/test',{method:'POST',body:JSON.stringify(data)}); $('#connection-result').textContent=result.message||'Connection available'; }
  catch(e){$('#connection-result').textContent=e.message;}
}

document.addEventListener('click', event => { const target=event.target.closest('[data-action]'); if (target) handleAction(target).catch(error => notify(error.message, 'error')); if (event.target === $('#palette')) closeOverlays(); });
document.addEventListener('submit', event => {
  if (event.target.id === 'chat-form') { event.preventDefault(); const field=event.target.elements.message; sendChat(field.value); field.value=''; }
  if (event.target.id === 'settings-form') { event.preventDefault(); const data=Object.fromEntries(new FormData(event.target)); api('/api/settings',{method:'POST',body:JSON.stringify(data)}).then(()=>{document.documentElement.dataset.theme=data.theme;closeOverlays();notify('Settings saved');}).catch(e=>notify(e.message,'error')); }
});
document.addEventListener('input', event => {
  if (event.target.id === 'palette-input') updatePalette(event.target.value);
  if (event.target.id === 'vault-search') { AppState.vaultQuery=event.target.value; renderVault(); $('#vault-search')?.focus(); }
  if (event.target.id === 'derivation-input') { const lines=Math.max(1,event.target.value.split('\n').length); $('#line-numbers').textContent=Array.from({length:lines},(_,i)=>i+1).join('\n'); }
});
document.addEventListener('change', event => {
  if (event.target.id === 'subject-filter') { AppState.subject=event.target.value; loadView(AppState.view); }
  if (event.target.name === 'theme') document.documentElement.dataset.theme=event.target.value;
});
document.addEventListener('keydown', event => {
  const typing = /INPUT|TEXTAREA|SELECT/.test(event.target.tagName);
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase()==='k') { event.preventDefault(); openPalette(); return; }
  if (event.key==='Escape') { if (AppState.pdf) { AppState.pdf=null;renderChat(); } closeOverlays(); return; }
  if (!$('#palette').classList.contains('is-hidden')) {
    if (event.key==='ArrowDown'||event.key==='ArrowUp') { event.preventDefault(); const n=AppState.palette.items.length; if(n){AppState.palette.selected=(AppState.palette.selected+(event.key==='ArrowDown'?1:-1)+n)%n;renderPaletteResults();} }
    if (event.key==='Enter') { event.preventDefault();executePalette(AppState.palette.selected); }
    return;
  }
  if (AppState.view==='sprint'&&!typing) { if(event.code==='Space'){event.preventDefault();AppState.sprintRevealed=true;renderSprint();} if(AppState.sprintRevealed&&/^[1-4]$/.test(event.key))gradeCard(event.key); }
  if (AppState.view==='mock'&&!typing&&event.key.toLowerCase()==='f'){event.preventDefault();const i=AppState.mock.current;AppState.mock.flagged=AppState.mock.flagged.includes(i)?AppState.mock.flagged.filter(x=>x!==i):[...AppState.mock.flagged,i];renderMock();}
  if (AppState.view==='checker'&&event.ctrlKey&&event.key==='Enter'){event.preventDefault();auditSteps();}
  if (AppState.view==='vault'&&!typing&&event.key==='/'){event.preventDefault();$('#vault-search')?.focus();}
});

async function bootstrap() {
  renderCurrentView();
  await loadStatus();
  await loadView('sprint');
}

bootstrap();
