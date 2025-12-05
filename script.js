// -------------------------
// Config
// -------------------------
const DB_NAME = 'appDB';
const DB_VERSION = 1;
const STORE_NAME = 'ont_macs';

// -------------------------
// IndexedDB helpers
// -------------------------
function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = e => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
        store.createIndex('mac', 'mac', { unique: true });
        store.createIndex('serial', 'serial', { unique: false });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function addRecord(data) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const normalized = { ...data, mac: normalizeMac(data.mac), detectedAt: new Date().toISOString() };
    const r = store.add(normalized);
    r.onsuccess = () => resolve(r.result);
    r.onerror = () => reject(r.error);
  });
}

async function putRecord(obj) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const normalized = { ...obj, mac: normalizeMac(obj.mac) };
    const r = store.put(normalized);
    r.onsuccess = () => resolve(r.result);
    r.onerror = () => reject(r.error);
  });
}

async function getAll() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const r = store.getAll();
    r.onsuccess = () => resolve(r.result);
    r.onerror = () => reject(r.error);
  });
}

async function del(id) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const r = store.delete(id);
    r.onsuccess = () => resolve(true);
    r.onerror = () => reject(r.error);
  });
}

// -------------------------
// MAC utils
// -------------------------
function normalizeMac(raw) {
  if (!raw) return '';
  const cleaned = raw.replace(/[^0-9a-fA-F]/g, '').toUpperCase();
  if (cleaned.length === 12) return cleaned.match(/.{2}/g).join(':');
  return raw.toUpperCase();
}

function isValidMac(raw) {
  if (!raw) return false;
  const s = raw.trim();
  const hex = s.replace(/[^0-9a-fA-F]/g, '');
  return /^[0-9A-Fa-f]{12}$/.test(hex);
}

// -------------------------
// UI wiring
// -------------------------
const addForm = document.getElementById('addForm');
const macInput = document.getElementById('macInput');
const serialInput = document.getElementById('serialInput');
const modelInput = document.getElementById('modelInput');
const passwordInput = document.getElementById('passwordInput');
const msg = document.getElementById('msg');
const itemsTable = document.getElementById('itemsTable');
const itemsBody = itemsTable.querySelector('tbody');
const empty = document.getElementById('empty');
const exportBtn = document.getElementById('exportBtn');
const importBtn = document.getElementById('importBtn');
const fileInput = document.getElementById('fileInput');

function showMessage(text, isError = false, timeout = 3500) {
  msg.textContent = text;
  msg.classList.remove('hidden');
  msg.style.backgroundColor = isError ? '#f8d7da' : '#d4edda';
  msg.style.color = isError ? '#721c24' : '#155724';
  setTimeout(() => {
    if (msg.textContent === text) msg.classList.add('hidden');
  }, timeout);
}

function escapeHtml(str) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  };
  return String(str).replace(/[&<>"']/g, s => map[s]);
}

function render(items) {
  itemsBody.innerHTML = '';
  if (!items || items.length === 0) {
    itemsTable.classList.add('hidden');
    empty.style.display = 'block';
    return;
  }
  empty.style.display = 'none';
  itemsTable.classList.remove('hidden');

  items.sort((a, b) => a.id - b.id).forEach(i => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>#${i.id}</td>
      <td><input data-id="${i.id}" data-field="mac" value="${escapeHtml(i.mac || '')}" style="width:100%;padding:6px;border-radius:6px;border:1px solid var(--color-border)"/></td>
      <td><input data-id="${i.id}" data-field="serial" value="${escapeHtml(i.serial || '')}" style="width:100%;padding:6px;border-radius:6px;border:1px solid var(--color-border)"/></td>
      <td><input data-id="${i.id}" data-field="model" value="${escapeHtml(i.model || '')}" style="width:100%;padding:6px;border-radius:6px;border:1px solid var(--color-border)"/></td>
      <td><input data-id="${i.id}" data-field="password" value="${escapeHtml(i.password || '')}" style="width:100%;padding:6px;border-radius:6px;border:1px solid var(--color-border)"/></td>
      <td>${new Date(i.detectedAt).toLocaleString()}</td>
      <td class="actions">
        <button class="edit" data-action="save" data-id="${i.id}">Salvar</button>
        <button class="del" data-action="delete" data-id="${i.id}">Excluir</button>
      </td>
    `;
    itemsBody.appendChild(tr);
  });
}

itemsBody.addEventListener('click', async (e) => {
  const btn = e.target.closest('button');
  if (!btn) return;
  const action = btn.getAttribute('data-action');
  const id = parseInt(btn.getAttribute('data-id'));

  if (action === 'delete') {
    if (!confirm('Confirma exclusão do registro #' + id + '?')) return;
    await del(id);
    showMessage('Registro excluído com sucesso.');
    await loadAndRender();
  } else if (action === 'save') {
    const row = btn.closest('tr');
    const mac = row.querySelector('input[data-field="mac"]').value.trim();
    const serial = row.querySelector('input[data-field="serial"]').value.trim();
    const model = row.querySelector('input[data-field="model"]').value.trim();
    const password = row.querySelector('input[data-field="password"]').value;
    if (!isValidMac(mac)) return showMessage('MAC inválido. Verifique o formato.', true);
    try {
      await putRecord({ id, mac: normalizeMac(mac), serial, model, password, detectedAt: new Date().toISOString() });
      showMessage('Registro atualizado com sucesso.');
      await loadAndRender();
    } catch (err) {
      showMessage('Erro ao salvar: ' + err.message, true);
    }
  }
});

addForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const mac = macInput.value.trim();
  const serial = serialInput.value.trim();
  const model = modelInput.value.trim();
  const password = passwordInput.value;
  if (!isValidMac(mac)) return showMessage('MAC inválido. Verifique o formato.', true);
  try {
    await addRecord({ mac: normalizeMac(mac), serial, model, password });
    macInput.value = '';
    serialInput.value = '';
    modelInput.value = '';
    passwordInput.value = '';
    showMessage('Novo registro adicionado com sucesso.');
    await loadAndRender();
  } catch (err) {
    showMessage('Erro ao adicionar registro: ' + err.message, true);
  }
});

exportBtn.addEventListener('click', async () => {
  const items = await getAll();
  const blob = new Blob([JSON.stringify(items, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'ont_macs_export.json';
  a.click();
  URL.revokeObjectURL(url);
  showMessage('Dados exportados para ont_macs_export.json.');
});

importBtn.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', async (e) => {
  const f = e.target.files[0];
  if (!f) return;
  try {
    const text = await f.text();
    if (f.type.includes('json') || text.trim().startsWith('[')) {
      const data = JSON.parse(text);
      if (!Array.isArray(data)) return showMessage('JSON inválido: o arquivo deve conter um array de registros.', true);
      const db = await openDB();
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      for (const item of data) {
        store.put({ ...item, mac: normalizeMac(item.mac), detectedAt: item.detectedAt || new Date().toISOString() });
      }
      tx.oncomplete = async () => { showMessage('Importação concluída com sucesso.'); await loadAndRender(); };
      tx.onerror = () => showMessage('Erro ao importar dados.', true);
    } else {
      const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
      let importedCount = 0;
      for (const ln of lines) {
        const parts = ln.split(/[;, ]/).map(p => p.trim()).filter(Boolean);
        const mac = parts[0];
        const serial = parts[1] || '';
        const model = parts[2] || '';
        const password = parts[3] || '';
        if (isValidMac(mac)) {
          try { await addRecord({ mac: normalizeMac(mac), serial, model, password }); importedCount++; } catch (e) { }
        }
      }
      showMessage(`Importação CSV tentada. ${importedCount} registros adicionados/atualizados.`);
      await loadAndRender();
    }
  } catch (err) {
    showMessage('Erro ao ler arquivo: ' + err.message, true);
  }
  fileInput.value = '';
});

async function loadAndRender() {
  const items = await getAll();
  render(items);
}

// Inicializa
(async () => { await loadAndRender(); })();
