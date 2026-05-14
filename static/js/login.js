async function intentarLogin() {
  const user  = document.getElementById('login-user').value.trim();
  const pass  = document.getElementById('login-pass').value;
  const errEl = document.getElementById('login-error');
  const form  = document.getElementById('login-form');
  const btn   = document.getElementById('login-btn');

  if (!user || !pass) {
    mostrarError(
      !user && !pass ? 'POR FAVOR INGRESE USUARIO Y CONTRASEÑA.' :
      !user          ? 'EL CAMPO DE USUARIO ESTÁ VACÍO.'         :
                       'EL CAMPO DE CONTRASEÑA ESTÁ VACÍO.',
      form
    );
    return;
  }

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
      btn.textContent = 'INICIAR SESIÓN';
    }
  } catch {
    mostrarError('ERROR DE CONEXIÓN. INTENTE NUEVAMENTE.', form);
    btn.disabled    = false;
    btn.textContent = 'INICIAR SESIÓN';
  }
}

function mostrarError(msg, form) {
  const errEl = document.getElementById('login-error');
  document.getElementById('login-error-msg').textContent = msg;
  errEl.classList.add('show');
  form.classList.remove('shake');
  void form.offsetWidth;  
  form.classList.add('shake');
}

document.addEventListener('DOMContentLoaded', () => {
  ['login-user', 'login-pass'].forEach(id => {
    document.getElementById(id).addEventListener('keydown', e => {
      if (e.key === 'Enter') intentarLogin();
    });
    document.getElementById(id).addEventListener('input', () =>
      document.getElementById('login-error').classList.remove('show')
    );
  });
});