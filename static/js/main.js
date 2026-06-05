const API = { status:'/api/status', upload:'/api/upload', chat:'/api/chat', reset:'/api/reset' };

const state = { storeReady:false, uploading:false, thinking:false, selectedFile:null };

const dom = {
  fileInput:   document.getElementById('fileInput'),
  uploadZone:  document.getElementById('uploadZone'),
  btnIngest:   document.getElementById('btnIngest'),
  progressWrap:document.getElementById('progressWrap'),
  progressFill:document.getElementById('progressFill'),
  progressLbl: document.getElementById('progressLabel'),
  docList:     document.getElementById('docList'),
  messages:    document.getElementById('messages'),
  emptyState:  document.getElementById('emptyState'),
  question:    document.getElementById('question'),
  btnSend:     document.getElementById('btnSend'),
  statusPill:  document.getElementById('statusPill'),
  appendToggle:document.getElementById('appendToggle'),
  btnReset:    document.getElementById('btnReset'),
};

document.addEventListener('DOMContentLoaded', () => {
  checkStatus();
  setupUploadZone();
  setupInput();
  dom.btnIngest.addEventListener('click', ingestFile);
  dom.btnReset.addEventListener('click', resetStore);
});

async function checkStatus() {
  try {
    const res  = await fetch(API.status);
    const data = await res.json();
    state.storeReady = data.store_ready;
    updateStatusPill();
  } catch {}
}

function updateStatusPill() {
  const pill = dom.statusPill;
  if (state.storeReady) {
    pill.classList.add('ready');
    pill.innerHTML = '<span class="status-dot"></span>Ready';
  } else {
    pill.classList.remove('ready');
    pill.innerHTML = '<span class="status-dot"></span>No Documents';
  }
}

function setupUploadZone() {
  dom.uploadZone.addEventListener('dragover', e => { e.preventDefault(); dom.uploadZone.classList.add('drag-over'); });
  dom.uploadZone.addEventListener('dragleave', () => dom.uploadZone.classList.remove('drag-over'));
  dom.uploadZone.addEventListener('drop', e => {
    e.preventDefault();
    dom.uploadZone.classList.remove('drag-over');
    if (e.dataTransfer.files[0]) setSelectedFile(e.dataTransfer.files[0]);
  });
  dom.fileInput.addEventListener('change', () => {
    if (dom.fileInput.files[0]) setSelectedFile(dom.fileInput.files[0]);
  });
}

function setSelectedFile(file) {
  state.selectedFile = file;
  dom.uploadZone.querySelector('.upload-label').textContent = '📄 ' + file.name;
  dom.btnIngest.disabled = false;
}

async function ingestFile() {
  if (!state.selectedFile || state.uploading) return;
  state.uploading = true;
  dom.btnIngest.disabled = true;
  showProgress('Uploading…', 20);

  const formData = new FormData();
  formData.append('file', state.selectedFile);
  formData.append('mode', dom.appendToggle.checked ? 'append' : 'replace');

  try {
    showProgress('Extracting text…', 45);
    const res  = await fetch(API.upload, { method:'POST', body:formData });
    const data = await res.json();
    showProgress('Embedding & indexing…', 80);
    await sleep(400);
    showProgress('Done!', 100);
    await sleep(500);

    if (data.success) {
      state.storeReady = true;
      updateStatusPill();
      addDocToList(data);
      toast('✓ ' + data.message, 'success');
      resetUploadUI();
    } else {
      toast('✗ ' + data.error, 'error');
    }
  } catch {
    toast('Upload failed. Is the server running?', 'error');
  } finally {
    state.uploading = false;
    dom.btnIngest.disabled = false;
    hideProgress();
  }
}

function addDocToList(data) {
  const ext  = data.filename.split('.').pop().toLowerCase();
  const icon = { pdf:'📕', docx:'📘', txt:'📄', md:'📝' }[ext] || '📄';
  const item = document.createElement('div');
  item.className = 'doc-item';
  item.innerHTML = `
    <div class="doc-icon ${ext}">${icon}</div>
    <div class="doc-info">
      <div class="doc-name" title="${data.filename}">${data.filename}</div>
      <div class="doc-meta">${data.chunks} chunks · ${data.pages} pages · ${data.elapsed_s}s</div>
    </div>`;
  dom.docList.prepend(item);
}

function setupInput() {
  dom.btnSend.addEventListener('click', sendMessage);
  dom.question.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });
  dom.question.addEventListener('input', () => {
    dom.question.style.height = 'auto';
    dom.question.style.height = Math.min(dom.question.scrollHeight, 140) + 'px';
  });
}

async function sendMessage() {
  const q = dom.question.value.trim();
  if (!q || state.thinking) return;

  if (!state.storeReady) {
    toast('Please upload and index a document first.', 'info');
    return;
  }

  hideEmpty();
  appendUserMessage(q);
  dom.question.value = '';
  dom.question.style.height = 'auto';
  state.thinking = true;
  dom.btnSend.disabled = true;

  const typingId = appendTypingIndicator();

  try {
    const res  = await fetch(API.chat, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({ question: q }),
    });
    const data = await res.json();
    removeTypingIndicator(typingId);

    if (data.success) {
      appendAiMessage(data.answer, data.sources);
    } else {
      appendAiMessage('⚠️ ' + data.error, []);
    }
  } catch {
    removeTypingIndicator(typingId);
    appendAiMessage('⚠️ Could not reach the server.', []);
  } finally {
    state.thinking = false;
    dom.btnSend.disabled = false;
    scrollToBottom();
  }
}

function appendUserMessage(text) {
  const msg = document.createElement('div');
  msg.className = 'message user';
  msg.innerHTML = `<div class="avatar user">You</div><div class="bubble">${escHtml(text)}</div>`;
  dom.messages.appendChild(msg);
  scrollToBottom();
}

function appendAiMessage(answer, sources) {
  const sourcesHtml = sources && sources.length
    ? `<div class="sources">
        <div class="source-label">Sources</div>
        ${sources.map(s => `
          <div class="source-item">
            <div class="source-file">📎 ${escHtml(s.source)}${s.page ? ' · p.' + s.page : ''}</div>
            <div class="source-excerpt">${escHtml(s.excerpt)}</div>
          </div>`).join('')}
       </div>` : '';

  const msg = document.createElement('div');
  msg.className = 'message ai';
  msg.innerHTML = `
    <div class="avatar ai">DM</div>
    <div>
      <div class="bubble">${formatAnswer(answer)}</div>
      ${sourcesHtml}
    </div>`;
  dom.messages.appendChild(msg);
}

function appendTypingIndicator() {
  const id  = 'typing-' + Date.now();
  const msg = document.createElement('div');
  msg.className = 'message ai';
  msg.id = id;
  msg.innerHTML = `<div class="avatar ai">DM</div><div class="bubble"><div class="typing-dots"><span></span><span></span><span></span></div></div>`;
  dom.messages.appendChild(msg);
  scrollToBottom();
  return id;
}

function removeTypingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

async function resetStore() {
  if (!confirm('Clear all indexed documents?')) return;
  await fetch(API.reset, { method:'POST' });
  state.storeReady = false;
  dom.docList.innerHTML = '';
  updateStatusPill();
  toast('Index cleared.', 'info');
}

function showProgress(label, pct) {
  dom.progressWrap.classList.add('active');
  dom.progressFill.style.width = pct + '%';
  dom.progressLbl.textContent  = label;
}
function hideProgress() {
  dom.progressWrap.classList.remove('active');
  dom.progressFill.style.width = '0%';
}
function resetUploadUI() {
  dom.uploadZone.querySelector('.upload-label').textContent = 'Drop file or click to browse';
  dom.fileInput.value = '';
  state.selectedFile  = null;
  dom.btnIngest.disabled = true;
}
function hideEmpty() {
  if (dom.emptyState) dom.emptyState.style.display = 'none';
}
function scrollToBottom() { dom.messages.scrollTop = dom.messages.scrollHeight; }
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
function escHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function formatAnswer(text) {
  return escHtml(text)
    .replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>')
    .replace(/`([^`]+)`/g,'<code style="font-family:monospace;font-size:12px;background:rgba(255,255,255,0.07);padding:1px 5px;border-radius:4px;">$1</code>')
    .replace(/\n/g,'<br>');
}
function toast(msg, type='info') {
  const el = document.createElement('div');
  el.className = 'toast ' + type;
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}
