async function intentarLogin() {
  const user  = document.getElementById('login-user').value.trim();
  const pass  = document.getElementById('login-pass').value;
  const errEl = document.getElementById('login-error');
  const form  = document.getElementById('login-form');
  const btn   = document.getElementById('login-btn');

  /* Validación de campos vacíos antes de llamar al servidor */
  if (!user || !pass) {
    mostrarError(
      !user && !pass ? 'POR FAVOR INGRESE USUARIO Y CONTRASEÑA.' :
      !user          ? 'EL CAMPO DE USUARIO ESTÁ VACÍO.'         :
                       'EL CAMPO DE CONTRASEÑA ESTÁ VACÍO.',
      form
    );
    return;
  }

  /* Estado de carga */
  btn.disabled     = true;
  btn.textContent  = 'VERIFICANDO...';

  try {
    const res  = await fetch('/login', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ usuario: user, password: pass }),
    });
    const data = await res.json();

    if (data.ok) {
      errEl.classList.remove('show');
      document.getElementById('login-overlay').classList.add('fade-out');
      setTimeout(() => { window.location.href = '/dashboard'; }, 450);
    } else {
      mostrarError(data.mensaje || 'Usuario o contraseña incorrectos.', form);
      btn.disabled    = false;
      btn.textContent = 'Iniciar sesión';
    }
  } catch {
    mostrarError('Error de conexión. Intente nuevamente.', form);
    btn.disabled    = false;
    btn.textContent = 'Iniciar sesión';
  }
}

function mostrarError(msg, form) {
  const errEl = document.getElementById('login-error');
  document.getElementById('login-error-msg').textContent = msg;
  errEl.classList.add('show');
  form.classList.remove('shake');
  void form.offsetWidth;   /* reflow para reiniciar la animación */
  form.classList.add('shake');
}

document.addEventListener('DOMContentLoaded', () => {
  /* Enter en cualquier campo del login */
  ['login-user', 'login-pass'].forEach(id => {
    document.getElementById(id).addEventListener('keydown', e => {
      if (e.key === 'Enter') intentarLogin();
    });
    /* Limpiar error al volver a escribir */
    document.getElementById(id).addEventListener('input', () =>
      document.getElementById('login-error').classList.remove('show')
    );
  });
});