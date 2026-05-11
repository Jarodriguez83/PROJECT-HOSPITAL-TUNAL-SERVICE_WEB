/* ═══════════════════════════════════════════
   app.js  —  Lógica principal del sistema
   Hospital del Tunal · Urgencias
═══════════════════════════════════════════ */

/* ──────────────────────────────────────────
   Constantes de triage (inyectadas por Flask
   en index.html como variable global)
────────────────────────────────────────── */
const TRIAGE_BADGE_CLASS = {
  1: 'badge-t1', 2: 'badge-t2', 3: 'badge-t3',
  4: 'badge-t4', 5: 'badge-t5',
};

const TRIAGE_LABEL = {
  1: '🔴 T1 · ROJO',     2: '🟠 T2 · NARANJA',
  3: '🟡 T3 · AMARILLO', 4: '🟢 T4 · VERDE',
  5: '🔵 T5 · AZUL',
};

/* Estado del tab activo en "Ver Pacientes" */
let currentTab = 'en_espera';

/* ══════════════════════════════
   NAVEGACIÓN
══════════════════════════════ */
const SECTION_TITLES = {
  dashboard: ['Dashboard',          'Resumen del sistema en tiempo real'],
  doctores:  ['Doctores',           'Gestión del personal médico'],
  registrar: ['Registrar Paciente', 'Ingreso de nuevos pacientes'],
  triage:    ['Asignar Triage',     'Clasificación y priorización'],
  pacientes: ['Ver Pacientes',      'Listado por estado'],
  cola:      ['Cola de Turnos',     'Orden de atención por prioridad'],
  atencion:  ['En Atención',        'Pacientes siendo atendidos ahora'],
};

function goTo(id, el) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('sec-' + id).classList.add('active');
  el.classList.add('active');
  const [title, sub] = SECTION_TITLES[id];
  document.getElementById('topbar-title').textContent = title;
  document.getElementById('topbar-sub').textContent   = sub;
  refreshSection(id);
}

function refreshSection(id) {
  if (id === 'dashboard') { loadStats(); loadColaDash(); loadAtencionDash(); }
  if (id === 'doctores')  { loadDoctores(); }
  if (id === 'triage')    { loadPacientesSinTriage(); buildTriageSelect(); }
  if (id === 'pacientes') { loadPacientesTab(); }
  if (id === 'cola')      { loadCola(); }
  if (id === 'atencion')  { loadAtencion(); }
}

function refreshAll() {
  const active = document.querySelector('.section.active');
  if (!active) return;
  refreshSection(active.id.replace('sec-', ''));
}

/* ══════════════════════════════
   RELOJ
══════════════════════════════ */
function updateClock() {
  document.getElementById('topbar-clock').textContent =
    new Date().toLocaleTimeString('es-CO', {
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
}

/* ══════════════════════════════
   TOAST
══════════════════════════════ */
let _toastTimer;

function toast(msg, ok = true) {
  const el = document.getElementById('toast');
  el.className = 'show ' + (ok ? 'ok' : 'err');
  document.getElementById('toast-icon').textContent = ok ? '✅' : '⚠️';
  document.getElementById('toast-msg').textContent  = msg;
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => el.classList.remove('show'), 3500);
}

/* ══════════════════════════════
   API helper
══════════════════════════════ */
async function api(url, body = null) {
  const opts = body
    ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
    : {};
  const r = await fetch(url, opts);
  return r.json();
}

/* ══════════════════════════════
   ESTADÍSTICAS
══════════════════════════════ */
async function loadStats() {
  const d = await api('/api/estadisticas');
  document.getElementById('st-total').textContent       = d.total;
  document.getElementById('st-espera').textContent      = d.en_espera;
  document.getElementById('st-atencion').textContent    = d.en_atencion;
  document.getElementById('st-finalizados').textContent = d.finalizados;
  document.getElementById('st-docs-disp').textContent   = d.docs_disp;
  document.getElementById('st-docs-turno').textContent  = d.docs_turno;
}

/* ══════════════════════════════
   DOCTORES
══════════════════════════════ */
async function loadDoctores() {
  const docs = await api('/api/doctores');
  const grid = document.getElementById('doctor-grid');
  if (!docs.length) {
    grid.innerHTML = '<div class="empty"><div class="em-icon">👨‍⚕️</div><p>No hay doctores registrados</p></div>';
    return;
  }
  grid.innerHTML = docs.map(d => `
    <div class="doctor-card">
      <div class="dc-head">
        <span class="dc-id">${d.id}</span>
        <span class="${d.disponible ? 'dot-green' : 'dot-red'}">${d.disponible ? '● Disponible' : '● En turno'}</span>
      </div>
      <div class="dc-name">Dr(a). ${d.nombre}</div>
      <div class="dc-esp">${d.especialidad}</div>
      <div class="dc-foot">
        ${d.paciente
          ? `<span style="font-size:11px;color:var(--text2)">🧑‍🤝‍🧑 ${d.paciente}</span>`
          : '<span></span>'}
        ${d.disponible
          ? `<button class="btn btn-danger btn-sm" onclick="eliminarDoctor('${d.id}')">Eliminar</button>`
          : '<span class="badge badge-warn">En turno</span>'}
      </div>
    </div>
  `).join('');
}

async function agregarDoctor() {
  const id  = document.getElementById('doc-id').value.trim();
  const nom = document.getElementById('doc-nombre').value.trim();
  const esp = document.getElementById('doc-esp').value.trim();
  if (!id || !nom || !esp) { toast('Completa todos los campos.', false); return; }
  const r = await api('/api/doctores/agregar', { id, nombre: nom, especialidad: esp });
  toast(r.mensaje, r.ok);
  if (r.ok) {
    ['doc-id', 'doc-nombre', 'doc-esp'].forEach(id => document.getElementById(id).value = '');
    loadDoctores();
  }
}

async function eliminarDoctor(id) {
  const r = await api('/api/doctores/eliminar', { id });
  toast(r.mensaje, r.ok);
  if (r.ok) loadDoctores();
}

/* ══════════════════════════════
   REGISTRAR PACIENTE
══════════════════════════════ */
async function registrarPaciente() {
  const campos = {
    nombre: 'p-nombre', cedula: 'p-cedula', telefono: 'p-tel',
    sexo: 'p-sexo', eps: 'p-eps', fecha_nacimiento: 'p-fnac',
    telefono_emergencia: 'p-telemerg',
  };
  const data = {};
  for (const [key, id] of Object.entries(campos)) {
    data[key] = document.getElementById(id).value.trim();
  }
  if (!data.nombre || !data.cedula || !data.sexo) {
    toast('Nombre, cédula y sexo son obligatorios.', false); return;
  }
  const r = await api('/api/pacientes/registrar', data);
  toast(r.mensaje, r.ok);
  if (r.ok) limpiarFormPaciente();
}

function limpiarFormPaciente() {
  ['p-nombre','p-cedula','p-tel','p-sexo','p-eps','p-fnac','p-telemerg']
    .forEach(id => document.getElementById(id).value = '');
}

/* ══════════════════════════════
   TRIAGE
══════════════════════════════ */
function buildTriageSelect() {
  const sel = document.getElementById('triage-tipo');
  sel.innerHTML = '<option value="">Seleccionar emergencia...</option>';
  TIPOS_EMERGENCIA.forEach(t => {
    const opt = document.createElement('option');
    opt.value       = t.nombre;
    opt.textContent = `${t.nombre}  (${t.badge.label} · ${t.tiempo} min)`;
    sel.appendChild(opt);
  });
}

async function loadPacientesSinTriage() {
  const d   = await api('/api/pacientes');
  const sel = document.getElementById('triage-paciente');
  if (!d.registrados.length) {
    sel.innerHTML = '<option value="">Sin pacientes pendientes de triage</option>';
    return;
  }
  sel.innerHTML = '<option value="">Seleccionar paciente...</option>';
  d.registrados.forEach(p => {
    const opt = document.createElement('option');
    opt.value       = p.cedula;
    opt.textContent = `${p.nombre}  (CC: ${p.cedula})`;
    sel.appendChild(opt);
  });
}

function initTriagePreview() {
  document.getElementById('triage-tipo').addEventListener('change', function () {
    const prev = document.getElementById('triage-preview');
    if (!this.value) { prev.style.display = 'none'; return; }
    const tipo = TIPOS_EMERGENCIA.find(t => t.nombre === this.value);
    if (!tipo) return;
    prev.style.display = 'block';
    document.getElementById('triage-preview-badge').innerHTML =
      `<span class="badge ${TRIAGE_BADGE_CLASS[tipo.nivel]}">${TRIAGE_LABEL[tipo.nivel]}</span>`;
    document.getElementById('triage-preview-tiempo').textContent =
      `Tiempo estimado de atención: ${tipo.tiempo} minutos`;
  });
}

async function asignarTriage() {
  const cedula          = document.getElementById('triage-paciente').value;
  const tipo_emergencia = document.getElementById('triage-tipo').value;
  if (!cedula || !tipo_emergencia) {
    toast('Selecciona paciente y tipo de emergencia.', false); return;
  }
  const r = await api('/api/pacientes/triage', { cedula, tipo_emergencia });
  toast(r.mensaje, r.ok);
  if (r.ok) {
    loadPacientesSinTriage();
    document.getElementById('triage-tipo').value = '';
    document.getElementById('triage-preview').style.display = 'none';
  }
}

/* ══════════════════════════════
   VER PACIENTES + TABS
══════════════════════════════ */
function switchTab(tab, el) {
  currentTab = tab;
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active', 'btn-primary'));
  el.classList.add('active');
  loadPacientesTab();
}

async function loadPacientesTab() {
  const data  = await api('/api/pacientes');
  const lista = data[currentTab] || [];
  const tbody = document.querySelector('#tbl-pacientes tbody');
  if (!lista.length) {
    tbody.innerHTML = `<tr><td colspan="8">
      <div class="empty"><div class="em-icon">📭</div><p>Sin pacientes en esta categoría</p></div>
    </td></tr>`;
    return;
  }
  tbody.innerHTML = lista.map(p => `
    <tr>
      <td><code style="font-family:'JetBrains Mono',monospace;font-size:12px">#${p.numero_turno ?? '—'}</code></td>
      <td><strong>${p.nombre}</strong></td>
      <td style="color:var(--text2);font-size:12px">${p.cedula}</td>
      <td style="font-size:12px">${p.eps || '—'}</td>
      <td>${p.nivel_triage
        ? `<span class="badge ${TRIAGE_BADGE_CLASS[p.nivel_triage]}">${TRIAGE_LABEL[p.nivel_triage]}</span>`
        : '<span class="badge badge-muted">Sin triage</span>'}</td>
      <td style="font-size:12px">${p.tipo_emergencia || '—'}</td>
      <td style="font-size:12px;color:var(--text2)">${p.hora_registro}</td>
      <td><span class="badge badge-info">${p.estado}</span></td>
    </tr>
  `).join('');
}

/* ══════════════════════════════
   COLA
══════════════════════════════ */
async function loadCola() {
  const cola  = await api('/api/cola');
  const tbody = document.querySelector('#tbl-cola tbody');
  if (!cola.length) {
    tbody.innerHTML = `<tr><td colspan="7">
      <div class="empty"><div class="em-icon">✅</div><p>Cola vacía — todos los pacientes han sido atendidos</p></div>
    </td></tr>`;
    return;
  }
  const maxEspera = cola[cola.length - 1].espera_acumulada + cola[cola.length - 1].tiempo_atencion || 1;
  tbody.innerHTML = cola.map((p, i) => `
    <tr>
      <td style="color:var(--text2)">${i + 1}</td>
      <td><code style="font-family:'JetBrains Mono',monospace">#${p.numero_turno}</code></td>
      <td><strong>${p.nombre}</strong></td>
      <td style="font-size:12px">${p.tipo_emergencia}</td>
      <td><span class="badge ${TRIAGE_BADGE_CLASS[p.nivel_triage]}">${TRIAGE_LABEL[p.nivel_triage]}</span></td>
      <td style="font-size:12px">${p.tiempo_atencion} min</td>
      <td>
        <div class="wait-bar-wrap">
          <div class="wait-bar-bg">
            <div class="wait-bar-fill" style="width:${Math.min(100,(p.espera_acumulada/maxEspera)*100)}%"></div>
          </div>
          <span class="wait-label">${p.espera_acumulada} min</span>
        </div>
      </td>
    </tr>
  `).join('');
}

async function loadColaDash() {
  const cola  = await api('/api/cola');
  const tbody = document.querySelector('#tbl-cola-dash tbody');
  const preview = cola.slice(0, 5);
  if (!preview.length) {
    tbody.innerHTML = `<tr><td colspan="4">
      <div class="empty" style="padding:20px"><p>Cola vacía</p></div>
    </td></tr>`;
    return;
  }
  tbody.innerHTML = preview.map(p => `
    <tr>
      <td><code style="font-family:'JetBrains Mono',monospace;font-size:12px">#${p.numero_turno}</code></td>
      <td>${p.nombre}</td>
      <td><span class="badge ${TRIAGE_BADGE_CLASS[p.nivel_triage]}">${TRIAGE_LABEL[p.nivel_triage]}</span></td>
      <td style="font-size:12px;color:var(--text2)">${p.espera_acumulada} min</td>
    </tr>
  `).join('');
}

/* ══════════════════════════════
   EN ATENCIÓN
══════════════════════════════ */
async function loadAtencion() {
  const d     = await api('/api/pacientes');
  const lista = d.en_atencion;
  const tbody = document.querySelector('#tbl-atencion tbody');
  if (!lista.length) {
    tbody.innerHTML = `<tr><td colspan="7">
      <div class="empty"><div class="em-icon">🏥</div><p>Ningún paciente en atención actualmente</p></div>
    </td></tr>`;
    return;
  }
  tbody.innerHTML = lista.map(p => `
    <tr>
      <td><code style="font-family:'JetBrains Mono',monospace">#${p.numero_turno}</code></td>
      <td><strong>${p.nombre}</strong></td>
      <td style="font-size:12px">${p.tipo_emergencia}</td>
      <td><span class="badge ${TRIAGE_BADGE_CLASS[p.nivel_triage]}">${TRIAGE_LABEL[p.nivel_triage]}</span></td>
      <td style="font-size:12px">${p.doctor_asignado ?? '—'}</td>
      <td style="font-size:12px">${p.tiempo_atencion} min</td>
      <td><button class="btn btn-success btn-sm" onclick="finalizarAtencion('${p.cedula}')">✔ Finalizar</button></td>
    </tr>
  `).join('');
}

async function loadAtencionDash() {
  const d     = await api('/api/pacientes');
  const lista = d.en_atencion;
  const tbody = document.querySelector('#tbl-atencion-dash tbody');
  if (!lista.length) {
    tbody.innerHTML = `<tr><td colspan="4">
      <div class="empty" style="padding:20px"><p>Ningún paciente en atención</p></div>
    </td></tr>`;
    return;
  }
  tbody.innerHTML = lista.map(p => `
    <tr>
      <td><code style="font-family:'JetBrains Mono',monospace;font-size:12px">#${p.numero_turno}</code></td>
      <td>${p.nombre}</td>
      <td style="font-size:12px">${p.doctor_asignado ?? '—'}</td>
      <td><button class="btn btn-success btn-sm" onclick="finalizarAtencion('${p.cedula}')">✔</button></td>
    </tr>
  `).join('');
}

/* ══════════════════════════════
   ACCIONES TURNO
══════════════════════════════ */
async function atenderSiguiente() {
  const r = await api('/api/turnos/atender', {});
  toast(r.mensaje, r.ok);
  if (r.ok) { loadColaDash(); loadAtencionDash(); loadStats(); loadCola(); loadAtencion(); }
}

async function finalizarAtencion(cedula) {
  const r = await api('/api/turnos/finalizar', { cedula });
  toast(r.mensaje, r.ok);
  if (r.ok) { loadAtencionDash(); loadAtencion(); loadStats(); loadDoctores(); }
}

/* ══════════════════════════════
   INICIALIZACIÓN
══════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  initLogin();
  initTriagePreview();
  buildTriageSelect();
  updateClock();
  setInterval(updateClock, 1000);

  /* Auto-refresh cada 15 s (solo si el login ya fue superado) */
  setInterval(() => {
    const overlay = document.getElementById('login-overlay');
    if (overlay.style.display === 'none' || overlay.classList.contains('fade-out')) {
      const active = document.querySelector('.section.active');
      if (active) refreshSection(active.id.replace('sec-', ''));
    }
  }, 15000);
});