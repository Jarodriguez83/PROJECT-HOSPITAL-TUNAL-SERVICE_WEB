/* ═══════════════════════════════════════════
   login.js  —  Lógica de inicio de sesión
═══════════════════════════════════════════ */

const CRED_USUARIO = 'ADMINISTRADOR';
const CRED_PASS    = 'HospitalTunal';

function intentarLogin() {
  const user  = document.getElementById('login-user').value.trim();
  const pass  = document.getElementById('login-pass').value;
  const errEl = document.getElementById('login-error');
  const form  = document.getElementById('login-form');

  if (user === CRED_USUARIO && pass === CRED_PASS) {
    errEl.classList.remove('show');
    const overlay = document.getElementById('login-overlay');
    overlay.classList.add('fade-out');
    setTimeout(() => {
      overlay.style.display = 'none';
      /* Cargar datos del sistema al entrar */
      loadStats();
      loadColaDash();
      loadAtencionDash();
    }, 450);
  } else {
    errEl.classList.add('show');
    document.getElementById('login-error-msg').textContent =
      !user && !pass ? 'Por favor ingrese usuario y contraseña.' :
      !user          ? 'El campo de usuario está vacío.'         :
      !pass          ? 'El campo de contraseña está vacío.'      :
                       'Usuario o contraseña incorrectos.';
    form.classList.remove('shake');
    void form.offsetWidth; /* reflow para reiniciar animación */
    form.classList.add('shake');
  }
}

function initLogin() {
  /* Enter en cualquier campo del login */
  ['login-user', 'login-pass'].forEach(id => {
    document.getElementById(id).addEventListener('keydown', e => {
      if (e.key === 'Enter') intentarLogin();
    });
  });

  /* Limpiar mensaje de error al escribir */
  ['login-user', 'login-pass'].forEach(id => {
    document.getElementById(id).addEventListener('input', () =>
      document.getElementById('login-error').classList.remove('show')
    );
  });
}