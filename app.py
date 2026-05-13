# INICIAR CON: python app.py
# EJECUTAR EN: http://127.0.0.1:5000
# app.py -> IMPLEMENTACIÓN DE LA CAPA FLASK

#IMPORTANCIÓN DE MÓDULOS 
import heapq
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
#IMPORTACIÓN DE CLASES Y CONSTANTES DESDE EL MÓDULO DEL PROYECTO
from proyecto_salud import (
    SistemaUrgencias, Doctor, Paciente,
    EstadoDoctor, EstadoPaciente,
    TIPOS_EMERGENCIA, DESCRIPCIONES_TRIAGE,
)

app = Flask(__name__) # CREACIÓN DE LA APLICACIÓN FLASK
app.secret_key = 'hospital_tunal_secret_2024'   #PARA USAR SESSIONS EN FLASK

# INSTANCIA DEL SISTEMA DE URGENCIAS
sistema = SistemaUrgencias()

# INFORMACIÓN DEL TRIAGE PARA SIGU
TRIAGE_BADGE = {
    1: {"color": "#e53e3e", "label": "T1 · ROJO",     "TIEMPO": "INMEDIATO"},
    2: {"color": "#dd6b20", "label": "T2 · NARANJA",  "TIEMPO": "< 10 MINUTOS"},
    3: {"color": "#d69e2e", "label": "T3 · AMARILLO", "TIEMPO": "< 30 MINUTOS"},
    4: {"color": "#38a169", "label": "T4 · VERDE",    "TIEMPO": "< 2 HORAS"},
    5: {"color": "#3182ce", "label": "T5 · AZUL",     "TIEMPO": "< 4 HORAS"},
}

# CREDENCIALES DE ACCESO PARA EL SISTEMA 
USUARIO_VALIDO   = "ADMINISTRADOR"
PASSWORD_VALIDO  = "HospitalTunal"

# FUNCIONES AUXILIARES PARA CONVERTIR OBJETOS A DICCIONARIOS (DOCTOR -> dict) - FACILITAR SU USO EN LAS PLANTILLAS Y RESPUESTAS JSON
def doctor_a_dict(doc: Doctor) -> dict:
    return {
        "id":           doc.doctor_id,
        "nombre":       doc.nombre,
        "especialidad": doc.especialidad,
        "estado":       doc.estado.value,
        "disponible":   doc.estado == EstadoDoctor.DISPONIBLE,
        "paciente":     doc.paciente_actual.nombre if doc.paciente_actual else None,
    }
# CONVIERTE UN OBJETO A UN DICCIONARIO (PACIENTE -> dict) - FACILITAR SU USO EN LAS PLANTILLAS Y RESPUESTAS JSON
def paciente_a_dict(p: Paciente) -> dict:
    return {
        "nombre":           p.nombre,
        "cedula":           p.cedula,
        "telefono":         p.telefono,
        "sexo":             p.sexo,
        "eps":              p.eps,
        "fecha_nacimiento": p.fecha_nacimiento,
        "tel_emergencia":   p.telefono_emergencia,
        "estado":           p.estado.value,
        "hora_registro":    p.hora_registro.strftime("%H:%M:%S"),
        "tipo_emergencia":  p.tipo_emergencia,
        "nivel_triage":     p.nivel_triage,
        "tiempo_atencion":  p.tiempo_atencion,
        "numero_turno":     p.numero_turno,
        "triage_badge":     TRIAGE_BADGE.get(p.nivel_triage) if p.nivel_triage else None,
        "doctor_asignado":  next(
            (d.nombre for d in sistema.doctores.values() if d.paciente_actual == p), None
        ),
    }
# PREPARA LA INFORMACIÓN DE LOS TIPOS DE EMERGENCIA PARA SER USADA EN LAS PLANTILLAS 
def tipos_para_template():
    return [
        {
            "nombre": nombre,
            "nivel":  nivel,
            "tiempo": tiempo,
            "badge":  TRIAGE_BADGE[nivel],
        }
        for nombre, (nivel, tiempo) in TIPOS_EMERGENCIA.items()
    ]
# VERIFICA SI EL USUARIO ESTÁ AUTENTICADO
def autenticado():
    return session.get('logged_in') is True

# RUTAS DE LA APLICACIÓN
@app.route("/")
def root():
    # SI PASA LA AUTENTICACIÓN: REDIRIGE A DASHBOARD
    if autenticado():
        return redirect(url_for('dashboard'))
    # SI NO PASA LA AUTENTICACIÓN: REDIRIGE A LOGIN 
    return redirect(url_for('login'))

# RUTAS DE AUTENTICACIÓN
# GET: MUESTRA EL FORMULARIO DE LOGIN
@app.route("/login", methods=["GET"])
def login():
    if autenticado():
        # return redirect(url_for('dashboard'))
        return render_template("index.html") # ME DIRIGE AL index.html (DASHBOARD)
    return render_template("login.html")

# POST: PROCESA LOS DATOS DEL FORMULARIO DE LOGIN
@app.route("/login", methods=["POST"])
def login_post():
    data     = request.get_json(silent=True) or {}
    usuario  = data.get("usuario", "").strip()
    password = data.get("password", "")
    if usuario == USUARIO_VALIDO and password == PASSWORD_VALIDO:
        session['logged_in'] = True
        return jsonify({"ok": True})
    return jsonify({"ok": False, "mensaje": "USUARIO O CONTRASEÑA DE ADMINISTRADOR INCORRECTOS."})

# RUTA PARA CERRAR SESIÓN
@app.route("/logout")
def logout():
    session.clear()
    return render_template("login.html", mensaje="SESIÓN CERRADA EXITOSAMENTE.")

# RUTA PRINCIPAL DEL DASHBOARD (LUEGO DE ENTRAR AL MOD: ADMINISTRADOR)
@app.route("/dashboard")
def dashboard():
    if not autenticado():
        return redirect(url_for('login'))
    return render_template("index.html", tipos_emergencia=tipos_para_template())

# RUTA PARA OBTENER LA LISTA DE DOCTORES EN FORMATO JSON
@app.route("/api/doctores")
def api_doctores():
    return jsonify([doctor_a_dict(d) for d in sistema.doctores.values()])

# RUTA PARA AGREGAR DOCTORES
@app.route("/api/doctores/agregar", methods=["POST"])
def api_agregar_doctor():
    d   = request.json
    did = d.get("id", "").strip()
    nom = d.get("nombre", "").strip()
    esp = d.get("especialidad", "").strip()
    if not did or not nom or not esp:
        return jsonify({"ok": False, "mensaje": "Todos los campos son obligatorios."})
    if did in sistema.doctores:
        return jsonify({"ok": False, "mensaje": "Ya existe un doctor con ese ID."})
    sistema.doctores[did] = Doctor(did, nom, esp)
    return jsonify({"ok": True, "mensaje": f"Doctor {nom} agregado correctamente."})

#RUTA PARA ELIMINAR DOCTORES
@app.route("/api/doctores/eliminar", methods=["POST"])
def api_eliminar_doctor():
    did = request.json.get("id", "").strip()
    if did not in sistema.doctores:
        return jsonify({"ok": False, "mensaje": "Doctor no encontrado."})
    doc = sistema.doctores[did]
    if doc.estado == EstadoDoctor.EN_TURNO:
        return jsonify({"ok": False, "mensaje": f"El doctor {doc.nombre} está en turno activo."})
    del sistema.doctores[did]
    return jsonify({"ok": True, "mensaje": f"Doctor {doc.nombre} eliminado."})

# RUTA PARA VER LOS PACIENTES (ESTADO)
@app.route("/api/pacientes")
def api_pacientes():
    result = {"registrados": [], "en_espera": [], "en_atencion": [], "finalizados": []}
    for p in sistema.pacientes:
        pd = paciente_a_dict(p)
        if   p.estado == EstadoPaciente.REGISTRADO:  result["registrados"].append(pd)
        elif p.estado == EstadoPaciente.EN_ESPERA:   result["en_espera"].append(pd)
        elif p.estado == EstadoPaciente.EN_ATENCION: result["en_atencion"].append(pd)
        else:                                         result["finalizados"].append(pd)
    return jsonify(result)

# RUTA PARA REGISTRAR UN PACIENTE  
@app.route("/api/pacientes/registrar", methods=["POST"])
def api_registrar_paciente():
    d      = request.json
    cedula = d.get("cedula", "").strip()
    for p in sistema.pacientes:
        if p.cedula == cedula:
            return jsonify({"ok": False, "mensaje": "YA EXISTE UN PACIENTE CON ESA C.C."})
    pac = Paciente(
        d.get("nombre", "").strip(),
        cedula,
        d.get("telefono", "").strip(),
        d.get("sexo", "").strip().upper(),
        d.get("eps", "").strip(),
        d.get("fecha_nacimiento", "").strip(),
        d.get("telefono_emergencia", "").strip(),
    )
    sistema.pacientes.append(pac)
    return jsonify({"ok": True, "mensaje": f"PACIENTE {pac.nombre} IDENTIFICADO CON C.C {pac.cedula} HA SIDO REGISTRADO."})

# RUTA PARA ASIGNACIÓN DE TRIAGE PARA EL PACIENTE
@app.route("/api/pacientes/triage", methods=["POST"])
def api_triage():
    d      = request.json
    cedula = d.get("cedula", "").strip()
    tipo   = d.get("tipo_emergencia", "").strip()
    if tipo not in TIPOS_EMERGENCIA:
        return jsonify({"ok": False, "mensaje": "EL TIPO DE EMERGENCIA NO ES VÁLIDO."})
    for p in sistema.pacientes:
        if p.cedula == cedula and p.estado == EstadoPaciente.REGISTRADO:
            p.asignar_triage(tipo)
            heapq.heappush(sistema.cola_prioridad, p)
            return jsonify({"ok": True,
                            "mensaje": f"TRIAGE ASIGNADO. EL TURNO ES: #{p.numero_turno}.",
                            "turno": p.numero_turno})
    return jsonify({"ok": False, "mensaje": "EL PACIENTE NO HA SIDO ENCONTRADO."})

# RUTA PARA VER LA COLA DE LOS TURNOS
@app.route("/api/cola")
def api_cola():
    copia = sorted(sistema.cola_prioridad)
    acum  = 0
    res   = []
    for p in copia:
        pd = paciente_a_dict(p)
        pd["espera_acumulada"] = acum
        res.append(pd)
        acum += p.tiempo_atencion
    return jsonify(res)


@app.route("/api/turnos/atender", methods=["POST"])
def api_atender():
    if not sistema.cola_prioridad:
        return jsonify({"ok": False, "mensaje": "No hay pacientes en cola."})
    doc_libre = next(
        (d for d in sistema.doctores.values() if d.estado == EstadoDoctor.DISPONIBLE), None
    )
    if not doc_libre:
        return jsonify({"ok": False, "mensaje": "No hay doctores disponibles."})
    pac                      = heapq.heappop(sistema.cola_prioridad)
    pac.estado               = EstadoPaciente.EN_ATENCION
    doc_libre.estado         = EstadoDoctor.EN_TURNO
    doc_libre.paciente_actual= pac
    sistema.pacientes_en_atencion.append(pac)
    return jsonify({"ok": True,
                    "mensaje": f"{pac.nombre} asignado a Dr. {doc_libre.nombre}.",
                    "paciente": pac.nombre, "doctor": doc_libre.nombre,
                    "turno": pac.numero_turno, "tiempo": pac.tiempo_atencion})


@app.route("/api/turnos/finalizar", methods=["POST"])
def api_finalizar():
    cedula = request.json.get("cedula", "").strip()
    for p in sistema.pacientes_en_atencion:
        if p.cedula == cedula:
            p.estado = EstadoPaciente.FINALIZADO
            sistema.pacientes_en_atencion.remove(p)
            sistema.pacientes_finalizados.append(p)
            for doc in sistema.doctores.values():
                if doc.paciente_actual == p:
                    doc.estado          = EstadoDoctor.DISPONIBLE
                    doc.paciente_actual = None
                    break
            return jsonify({"ok": True, "mensaje": f"Atención de {p.nombre} finalizada."})
    return jsonify({"ok": False, "mensaje": "Paciente no encontrado en atención."})


# ── API: Estadísticas ──────────────────────────────────────────

@app.route("/api/estadisticas")
def api_estadisticas():
    total       = len(sistema.pacientes)
    reg         = sum(1 for p in sistema.pacientes if p.estado == EstadoPaciente.REGISTRADO)
    espera      = sum(1 for p in sistema.pacientes if p.estado == EstadoPaciente.EN_ESPERA)
    atencion    = len(sistema.pacientes_en_atencion)
    finalizados = len(sistema.pacientes_finalizados)
    docs_disp   = sum(1 for d in sistema.doctores.values() if d.estado == EstadoDoctor.DISPONIBLE)
    docs_turno  = len(sistema.doctores) - docs_disp
    tiempo_cola = sum(p.tiempo_atencion for p in sistema.cola_prioridad)
    return jsonify({
        "total": total, "registrados": reg, "en_espera": espera,
        "en_atencion": atencion, "finalizados": finalizados,
        "docs_disp": docs_disp, "docs_turno": docs_turno,
        "tiempo_cola": tiempo_cola,
    })


if __name__ == "__main__":
    print("\n" + "═" * 55)
    print("  🏥  HOSPITAL DEL TUNAL — Sistema de Urgencias")
    print("  Abre tu navegador en → http://127.0.0.1:5000")
    print("═" * 55 + "\n")
    app.run(debug=True, port=5000)