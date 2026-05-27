# INICIAR CON: python app.py
# EJECUTAR EN: http://127.0.0.1:5000
# app.py -> IMPLEMENTACIÓN DE LA CAPA FLASK
# INICIAR CON: python app.py
"""
app.py  –  Capa Flask del Sistema de Urgencias
Importa la lógica desde proyecto_salud.py sin modificarla.
Ejecutar:  python app.py   → abrir http://127.0.0.1:5000
"""

import heapq
from datetime import datetime
from flask import Flask, render_template, request, jsonify

from proyecto_salud import (
    SistemaUrgencias, Doctor, Paciente,
    EstadoDoctor, EstadoPaciente, TipoDescanso,
    TIPOS_EMERGENCIA, DESCRIPCIONES_TRIAGE,
    TABLA_DOCTORES_HOSPITAL,
)

app = Flask(__name__)
sistema = SistemaUrgencias()

TRIAGE_BADGE = {
    1: {"color": "#e53e3e", "label": "T1 · ROJO",     "tiempo": "Inmediato"},
    2: {"color": "#dd6b20", "label": "T2 · NARANJA",  "tiempo": "< 10 min"},
    3: {"color": "#d69e2", "label": "T3 · AMARILLO", "tiempo": "< 30 min"},
    4: {"color": "#38a169", "label": "T4 · VERDE",    "tiempo": "< 2 h"},
    5: {"color": "#3182ce", "label": "T5 · AZUL",     "tiempo": "< 4 h"},
}

DESCANSO_MAP = {
    "break":    TipoDescanso.BREAK,
    "almuerzo": TipoDescanso.ALMUERZO,
    "descanso": TipoDescanso.DESCANSO,
}

def doctor_a_dict(doc: Doctor) -> dict:
    return {
        "id":                doc.doctor_id,
        "nombre":            doc.nombre,
        "especialidad":      doc.especialidad,
        "estado":            doc.estado.value,
        "disponible":        doc.estado == EstadoDoctor.DISPONIBLE,
        "en_descanso":       doc.en_descanso,
        "en_turno":          doc.estado == EstadoDoctor.EN_TURNO,
        "paciente":          doc.paciente_actual.nombre if doc.paciente_actual else None,
        "hora_fin_descanso": doc.hora_fin_descanso.strftime("%H:%M") if doc.hora_fin_descanso else None,
        "descansos":         doc.descansos,
    }

def paciente_a_dict(p: Paciente) -> dict:
    return {
        "nombre":             p.nombre,
        "cedula":             p.cedula,
        "telefono":           p.telefono,
        "sexo":               p.sexo,
        "edad":               p.edad,
        "fecha_nacimiento":   p.fecha_nacimiento,
        "tel_emergencia":     p.telefono_emergencia,
        "estado":             p.estado.value,
        "hora_registro":      p.hora_registro.strftime("%H:%M:%S"),
        "tipo_emergencia":    p.tipo_emergencia,
        "nivel_triage":       p.nivel_triage,
        "tiempo_atencion":    p.tiempo_atencion,
        "numero_turno":       p.numero_turno,
        "triage_badge":       TRIAGE_BADGE.get(p.nivel_triage) if p.nivel_triage else None,
        "doctor_asignado":    next(
            (d.nombre for d in sistema.doctores.values() if d.paciente_actual == p), None
        ),
        "hora_inicio_atencion": p.hora_inicio_atencion.strftime("%H:%M:%S") if p.hora_inicio_atencion else None,
        "hora_fin_atencion":    p.hora_fin_atencion.strftime("%H:%M:%S") if p.hora_fin_atencion else None,
        "minutos_espera_real":  p.minutos_espera_real,
        "minutos_atencion_real":p.minutos_atencion_real,
        "minutos_total_real":   p.minutos_total_real,
    }

# PÁGINA PRINCIPAL
@app.route("/")
def index():
    tipos = [
        {
            "nombre": nombre,
            "nivel":  nivel,
            "tiempo": tiempo,
            "badge":  TRIAGE_BADGE[nivel],
        }
        for nombre, (nivel, tiempo) in TIPOS_EMERGENCIA.items()
    ]
    tabla_hospital = [
        {"id": did, "nombre": info["nombre"], "especialidad": info["especialidad"]}
        for did, info in TABLA_DOCTORES_HOSPITAL.items()
    ]
    return render_template("index.html",
                           tipos_emergencia=tipos,
                           tabla_hospital=tabla_hospital)


# DOCTORES 
@app.route("/api/doctores")
def api_doctores():
    return jsonify([doctor_a_dict(d) for d in sistema.doctores.values()])


@app.route("/api/doctores/tabla")
def api_tabla_hospital():
    """Devuelve la tabla maestra de todos los doctores del hospital."""
    en_turno = set(sistema.doctores.keys())
    tabla = [
        {
            "id":           did,
            "nombre":       info["nombre"],
            "especialidad": info["especialidad"],
            "en_turno":     did in en_turno,
        }
        for did, info in TABLA_DOCTORES_HOSPITAL.items()
    ]
    return jsonify(tabla)


@app.route("/api/doctores/agregar", methods=["POST"])
def api_agregar_doctor():
    d   = request.json
    did = d.get("id", "").strip().upper()
    nom = d.get("nombre", "").strip()
    esp = d.get("especialidad", "").strip()

    if did in sistema.doctores:
        return jsonify({"ok": False, "mensaje": "Este doctor ya está en el turno activo."})

    # Si viene de la tabla del hospital (sin nombre/esp), buscamos ahí
    if not nom and did in TABLA_DOCTORES_HOSPITAL:
        nom = TABLA_DOCTORES_HOSPITAL[did]["nombre"]
        esp = TABLA_DOCTORES_HOSPITAL[did]["especialidad"]

    if not did or not nom or not esp:
        return jsonify({"ok": False, "mensaje": "Todos los campos son obligatorios."})

    sistema.doctores[did] = Doctor(did, nom, esp)
    if did not in TABLA_DOCTORES_HOSPITAL:
        TABLA_DOCTORES_HOSPITAL[did] = {"nombre": nom, "especialidad": esp}

    return jsonify({"ok": True, "mensaje": f"Dr(a). {nom} agregado al turno."})


@app.route("/api/doctores/eliminar", methods=["POST"])
def api_eliminar_doctor():
    did = request.json.get("id", "").strip()
    if did not in sistema.doctores:
        return jsonify({"ok": False, "mensaje": "Doctor no encontrado."})
    doc = sistema.doctores[did]
    if doc.estado == EstadoDoctor.EN_TURNO:
        return jsonify({"ok": False, "mensaje": f"{doc.nombre} está en turno activo."})
    del sistema.doctores[did]
    return jsonify({"ok": True, "mensaje": f"Dr(a). {doc.nombre} retirado del turno."})


@app.route("/api/doctores/descanso", methods=["POST"])
def api_descanso():
    d      = request.json
    did    = d.get("id", "").strip()
    accion = d.get("accion", "").strip()   # "iniciar" | "terminar"
    tipo   = d.get("tipo", "").strip()     # "break" | "almuerzo" | "descanso"

    if did not in sistema.doctores:
        return jsonify({"ok": False, "mensaje": "Doctor no encontrado."})
    doc = sistema.doctores[did]

    if accion == "terminar":
        msg = doc.terminar_descanso()
        ok  = "⚠" not in msg
        return jsonify({"ok": ok, "mensaje": msg})

    if accion == "iniciar":
        t = DESCANSO_MAP.get(tipo)
        if not t:
            return jsonify({"ok": False, "mensaje": "Tipo de descanso inválido."})
        msg = doc.iniciar_descanso(t)
        ok  = "⚠" not in msg
        return jsonify({"ok": ok, "mensaje": msg})

    return jsonify({"ok": False, "mensaje": "Acción no reconocida."})


# PACIENTES
@app.route("/api/pacientes")
def api_pacientes():
    result = {"registrados": [], "en_espera": [], "en_atencion": [], "finalizados": []}
    for p in sistema.pacientes:
        pd = paciente_a_dict(p)
        if p.estado == EstadoPaciente.REGISTRADO:
            result["registrados"].append(pd)
        elif p.estado == EstadoPaciente.EN_ESPERA:
            result["en_espera"].append(pd)
        elif p.estado == EstadoPaciente.EN_ATENCION:
            result["en_atencion"].append(pd)
        else:
            result["finalizados"].append(pd)
    return jsonify(result)


@app.route("/api/pacientes/registrar", methods=["POST"])
def api_registrar_paciente():
    d      = request.json
    cedula = d.get("cedula", "").strip()
    for p in sistema.pacientes:
        if p.cedula == cedula:
            return jsonify({"ok": False, "mensaje": "Ya existe un paciente con esa cédula."})
    try:
        edad = int(d.get("edad", -1))
        if edad < 0 or edad > 120:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"ok": False, "mensaje": "Edad inválida."})

    pac = Paciente(
        d.get("nombre", "").strip(),
        cedula,
        d.get("telefono", "").strip(),
        d.get("sexo", "").strip().upper(),
        edad,
        d.get("fecha_nacimiento", "").strip(),
        d.get("telefono_emergencia", "").strip(),
    )
    sistema.pacientes.append(pac)
    return jsonify({"ok": True, "mensaje": f"Paciente {pac.nombre} ({edad} años) registrado."})


@app.route("/api/pacientes/triage", methods=["POST"])
def api_triage():
    d      = request.json
    cedula = d.get("cedula", "").strip()
    tipo   = d.get("tipo_emergencia", "").strip()
    if tipo not in TIPOS_EMERGENCIA:
        return jsonify({"ok": False, "mensaje": "Tipo de emergencia no válido."})
    for p in sistema.pacientes:
        if p.cedula == cedula and p.estado == EstadoPaciente.REGISTRADO:
            p.asignar_triage(tipo)
            heapq.heappush(sistema.cola_prioridad, p)
            return jsonify({
                "ok": True,
                "mensaje": f"Triage asignado. Turno #{p.numero_turno}.",
                "turno": p.numero_turno,
            })
    return jsonify({"ok": False, "mensaje": "Paciente no encontrado o ya tiene triage."})


# COLA Y TURNOS
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
        (d for d in sistema.doctores.values() if d.estado == EstadoDoctor.DISPONIBLE),
        None
    )
    if not doc_libre:
        return jsonify({"ok": False, "mensaje": "No hay doctores disponibles."})

    pac = heapq.heappop(sistema.cola_prioridad)
    pac.iniciar_atencion()
    doc_libre.estado          = EstadoDoctor.EN_TURNO
    doc_libre.paciente_actual = pac
    sistema.pacientes_en_atencion.append(pac)
    return jsonify({
        "ok": True,
        "mensaje": f"{pac.nombre} asignado a Dr(a). {doc_libre.nombre}.",
        "paciente": pac.nombre,
        "doctor":   doc_libre.nombre,
        "turno":    pac.numero_turno,
        "tiempo":   pac.tiempo_atencion,
    })


@app.route("/api/turnos/finalizar", methods=["POST"])
def api_finalizar():
    cedula = request.json.get("cedula", "").strip()
    for p in sistema.pacientes_en_atencion:
        if p.cedula == cedula:
            p.finalizar_atencion()
            sistema.pacientes_en_atencion.remove(p)
            sistema.pacientes_finalizados.append(p)
            for doc in sistema.doctores.values():
                if doc.paciente_actual == p:
                    doc.estado          = EstadoDoctor.DISPONIBLE
                    doc.paciente_actual = None
                    break
            return jsonify({
                "ok": True,
                "mensaje":             f"Atención de {p.nombre} finalizada.",
                "minutos_espera":      p.minutos_espera_real,
                "minutos_atencion":    p.minutos_atencion_real,
                "minutos_total":       p.minutos_total_real,
            })
    return jsonify({"ok": False, "mensaje": "Paciente no encontrado en atención."})


# ESTADÍSTICAS  
@app.route("/api/estadisticas")
def api_estadisticas():
    total       = len(sistema.pacientes)
    reg         = sum(1 for p in sistema.pacientes if p.estado == EstadoPaciente.REGISTRADO)
    espera      = sum(1 for p in sistema.pacientes if p.estado == EstadoPaciente.EN_ESPERA)
    atencion    = len(sistema.pacientes_en_atencion)
    finalizados = len(sistema.pacientes_finalizados)
    docs_disp   = sum(1 for d in sistema.doctores.values() if d.estado == EstadoDoctor.DISPONIBLE)
    docs_turno  = sum(1 for d in sistema.doctores.values() if d.estado == EstadoDoctor.EN_TURNO)
    docs_desc   = sum(1 for d in sistema.doctores.values() if d.en_descanso)
    tiempo_cola = sum(p.tiempo_atencion for p in sistema.cola_prioridad)

    tiempos_tot = [p.minutos_total_real for p in sistema.pacientes_finalizados
                   if p.minutos_total_real is not None]
    promedio_total = (sum(tiempos_tot) // len(tiempos_tot)) if tiempos_tot else None

    return jsonify({
        "total": total, "registrados": reg, "en_espera": espera,
        "en_atencion": atencion, "finalizados": finalizados,
        "docs_disp": docs_disp, "docs_turno": docs_turno, "docs_desc": docs_desc,
        "tiempo_cola": tiempo_cola,
        "promedio_total_min": promedio_total,
        "hora_sistema": datetime.now().strftime("%H:%M:%S"),
    })


if __name__ == "__main__":
    print("\n" + "═"*55)
    print("  HOSPITAL DEL TUNAL — SIGU (SISTEMA INTELIGENTE DE GESTIÓN DE URGENCIAS)")
    print("  ABRIR EN EL NAVEGADOR: → http://127.0.0.1:5000")
    print("═"*55 + "\n")
    app.run(debug=True, port=5000)