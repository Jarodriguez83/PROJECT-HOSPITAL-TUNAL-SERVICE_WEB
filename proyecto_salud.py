"""
╔══════════════════════════════════════════════════════════════╗
║         SISTEMA DE GESTIÓN DE URGENCIAS                      ║
║         Hospital del Tunal - Bogotá, Colombia                ║
║         Asignación Óptima de Turnos y Triage                 ║
╚══════════════════════════════════════════════════════════════╝
"""

import heapq
from datetime import datetime, timedelta
from enum import Enum


# ─────────────────────────────────────────────
#  ENUMERACIONES Y CONSTANTES
# ─────────────────────────────────────────────

class EstadoPaciente(Enum):
    REGISTRADO  = "Registrado (sin triage)"
    EN_ESPERA   = "En espera (cola)"
    EN_ATENCION = "En atención"
    FINALIZADO  = "Finalizado"


class EstadoDoctor(Enum):
    DISPONIBLE  = "Disponible"
    EN_TURNO    = "En turno"
    EN_DESCANSO = "En descanso"
    EN_ALMUERZO = "En almuerzo"


class TipoDescanso(Enum):
    BREAK      = "Break (15 min)"
    ALMUERZO   = "Almuerzo (60 min)"
    DESCANSO   = "Descanso (30 min)"

    @property
    def duracion_minutos(self):
        if self == TipoDescanso.BREAK:
            return 15
        elif self == TipoDescanso.ALMUERZO:
            return 60
        elif self == TipoDescanso.DESCANSO:
            return 30


# ─────────────────────────────────────────────
#  TABLA GENERAL DE DOCTORES DEL HOSPITAL
#  (catálogo maestro — todos los que trabajan aquí)
# ─────────────────────────────────────────────
TABLA_DOCTORES_HOSPITAL = {
    "MED001": {"nombre": "Carlos Ramírez",     "especialidad": "Medicina de Emergencias"},
    "MED002": {"nombre": "Laura Gómez",        "especialidad": "Cirugía General"},
    "MED003": {"nombre": "Andrés Martínez",    "especialidad": "Cardiología"},
    "MED004": {"nombre": "Sofía Torres",       "especialidad": "Neurología"},
    "MED005": {"nombre": "Felipe Herrera",     "especialidad": "Traumatología"},
    "MED006": {"nombre": "Valentina Ríos",     "especialidad": "Pediatría"},
    "MED007": {"nombre": "Jorge Medina",       "especialidad": "Medicina Interna"},
    "MED008": {"nombre": "Camila Vargas",      "especialidad": "Anestesiología"},
    "MED009": {"nombre": "Sebastián Pardo",    "especialidad": "Medicina de Emergencias"},
    "MED010": {"nombre": "Natalia Ospina",     "especialidad": "Ginecología"},
}


# ─────────────────────────────────────────────
#  TIPOS DE EMERGENCIA
#  Formato: "Nombre": (nivel_triage, tiempo_atencion_minutos)
# ─────────────────────────────────────────────
TIPOS_EMERGENCIA = {
    # TRIAGE I - Resucitación
    "Paro cardiorrespiratorio":         (1, 60),
    "Politraumatismo grave":            (1, 90),

    # TRIAGE II - Emergencia
    "Dificultad respiratoria severa":   (2, 45),
    "ACV / Derrame cerebral":           (2, 50),

    # TRIAGE III - Urgencia
    "Fractura con compromiso vascular": (3, 35),
    "Dolor abdominal agudo":            (3, 30),

    # TRIAGE IV - Menos urgente
    "Fiebre alta con convulsión":       (4, 25),
    "Herida con sangrado moderado":     (4, 20),

    # TRIAGE V - No urgente
    "Dolor leve / Malestar general":    (5, 15),
    "Consulta menor (gripe, tos)":      (5, 10),
}

DESCRIPCIONES_TRIAGE = {
    1: "TRIAGE I  - ROJO      (Resucitación) → Atención INMEDIATA",
    2: "TRIAGE II - NARANJA   (Emergencia)   → Atención < 10 min",
    3: "TRIAGE III- AMARILLO  (Urgente)      → Atención < 30 min",
    4: "TRIAGE IV - VERDE     (Menos urgente)→ Atención < 2 horas",
    5: "TRIAGE V  - AZUL      (No urgente)   → Atención < 4 horas",
}

# Rangos de edad que modifican la prioridad
# (edad_min, edad_max, descripcion, peso_prioridad)
# Menor peso = mayor prioridad
PRIORIDAD_EDAD = [
    (0,   1,  "Neonato",      0),   # máxima prioridad
    (1,   5,  "Infante",      1),
    (60,  74, "Adulto mayor", 2),
    (75,  199,"Anciano",      0),   # igual a neonato
]


# ─────────────────────────────────────────────
#  CLASE DOCTOR
# ─────────────────────────────────────────────

class Doctor:
    def __init__(self, doctor_id: str, nombre: str, especialidad: str):
        self.doctor_id    = doctor_id
        self.nombre       = nombre
        self.especialidad = especialidad
        self.estado       = EstadoDoctor.DISPONIBLE
        self.paciente_actual  = None
        # Registro de descansos
        self.descansos: list[dict] = []   # {tipo, inicio, fin}
        self.hora_fin_descanso: datetime | None = None

    # ── Descansos ──────────────────────────────
    def iniciar_descanso(self, tipo: TipoDescanso) -> str:
        if self.estado == EstadoDoctor.EN_TURNO:
            return f"⚠ {self.nombre} está EN TURNO. Finalice la atención primero."
        ahora = datetime.now()
        fin   = ahora + timedelta(minutes=tipo.duracion_minutos)
        self.estado             = (EstadoDoctor.EN_ALMUERZO
                                   if tipo == TipoDescanso.ALMUERZO
                                   else EstadoDoctor.EN_DESCANSO)
        self.hora_fin_descanso  = fin
        self.descansos.append({
            "tipo":   tipo.value,
            "inicio": ahora.strftime("%H:%M:%S"),
            "fin":    fin.strftime("%H:%M:%S"),
        })
        return (f"✔ {self.nombre} inicia {tipo.value}. "
                f"Regresa a las {fin.strftime('%H:%M:%S')}.")

    def terminar_descanso(self) -> str:
        if self.estado not in (EstadoDoctor.EN_DESCANSO, EstadoDoctor.EN_ALMUERZO):
            return f"⚠ {self.nombre} no está en descanso."
        self.estado            = EstadoDoctor.DISPONIBLE
        self.hora_fin_descanso = None
        return f"✔ {self.nombre} regresó al turno. Estado: DISPONIBLE."

    @property
    def disponible(self):
        return self.estado == EstadoDoctor.DISPONIBLE

    @property
    def en_descanso(self):
        return self.estado in (EstadoDoctor.EN_DESCANSO, EstadoDoctor.EN_ALMUERZO)

    def __str__(self):
        estado_str = self.estado.value
        if self.paciente_actual:
            estado_str += f" → atendiendo a {self.paciente_actual.nombre}"
        if self.hora_fin_descanso:
            estado_str += f" (regresa {self.hora_fin_descanso.strftime('%H:%M')})"
        return (f"[{self.doctor_id}] Dr(a). {self.nombre} | "
                f"{self.especialidad} | {estado_str}")


# ─────────────────────────────────────────────
#  CLASE PACIENTE
# ─────────────────────────────────────────────

def _peso_edad(edad: int) -> int:
    """Retorna el peso de prioridad por edad. Menor = más urgente."""
    for emin, emax, _, peso in PRIORIDAD_EDAD:
        if emin <= edad <= emax:
            return peso
    return 3   # adulto normal (menor prioridad en este criterio)


class Paciente:
    _contador = 1   # número de turno único

    def __init__(self, nombre: str, cedula: str, telefono: str,
                 sexo: str, edad: int, fecha_nacimiento: str,
                 telefono_emergencia: str):
        self.nombre              = nombre
        self.cedula              = cedula
        self.telefono            = telefono
        self.sexo                = sexo
        self.edad                = edad
        self.fecha_nacimiento    = fecha_nacimiento
        self.telefono_emergencia = telefono_emergencia
        self.estado              = EstadoPaciente.REGISTRADO
        self.hora_registro       = datetime.now()

        # Datos de triage
        self.tipo_emergencia  = None
        self.nivel_triage     = None
        self.tiempo_atencion  = None   # minutos estimados de atención
        self.numero_turno     = None

        # Tiempos reales
        self.hora_inicio_atencion: datetime | None = None
        self.hora_fin_atencion:    datetime | None = None

        # Para el heap de prioridad
        self._prioridad = None

    # ── Prioridad compuesta ─────────────────────
    # Criterios (menor tupla = mayor urgencia):
    #   1. nivel_triage (1=más urgente … 5=menos)
    #   2. peso_edad    (0=neonato/anciano … 3=adulto)
    #   3. hora_registro (llegó antes → atiende antes)
    def _calcular_prioridad(self):
        return (
            self.nivel_triage,
            _peso_edad(self.edad),
            self.hora_registro,
        )

    def asignar_triage(self, tipo_emergencia: str):
        nivel, tiempo = TIPOS_EMERGENCIA[tipo_emergencia]
        self.tipo_emergencia = tipo_emergencia
        self.nivel_triage    = nivel
        self.tiempo_atencion = tiempo
        self.numero_turno    = Paciente._contador
        Paciente._contador  += 1
        self.estado          = EstadoPaciente.EN_ESPERA
        self._prioridad      = self._calcular_prioridad()

    def iniciar_atencion(self):
        self.hora_inicio_atencion = datetime.now()
        self.estado = EstadoPaciente.EN_ATENCION

    def finalizar_atencion(self):
        self.hora_fin_atencion = datetime.now()
        self.estado = EstadoPaciente.FINALIZADO

    # ── Tiempos calculados ──────────────────────
    @property
    def minutos_espera_real(self) -> int | None:
        """Minutos desde registro hasta inicio de atención."""
        if self.hora_inicio_atencion:
            delta = self.hora_inicio_atencion - self.hora_registro
            return int(delta.total_seconds() // 60)
        return None

    @property
    def minutos_atencion_real(self) -> int | None:
        """Minutos reales de atención (si ya finalizó)."""
        if self.hora_inicio_atencion and self.hora_fin_atencion:
            delta = self.hora_fin_atencion - self.hora_inicio_atencion
            return int(delta.total_seconds() // 60)
        return None

    @property
    def minutos_total_real(self) -> int | None:
        """Tiempo total desde registro hasta alta."""
        if self.hora_fin_atencion:
            delta = self.hora_fin_atencion - self.hora_registro
            return int(delta.total_seconds() // 60)
        return None

    def __lt__(self, other):
        return self._prioridad < other._prioridad

    def resumen(self):
        linea = "─" * 60
        print(linea)
        print(f"  Turno N°         : {self.numero_turno}")
        print(f"  Nombre           : {self.nombre}")
        print(f"  Cédula           : {self.cedula}")
        print(f"  Edad             : {self.edad} años")
        print(f"  Hora de registro : {self.hora_registro.strftime('%H:%M:%S')}")
        print(f"  Emergencia       : {self.tipo_emergencia}")
        print(f"  {DESCRIPCIONES_TRIAGE[self.nivel_triage]}")
        print(f"  T. atención est. : {self.tiempo_atencion} min")
        if self.minutos_espera_real is not None:
            print(f"  T. espera real   : {self.minutos_espera_real} min")
        if self.minutos_atencion_real is not None:
            print(f"  T. atención real : {self.minutos_atencion_real} min")
        if self.minutos_total_real is not None:
            print(f"  T. TOTAL HOSPITAL: {self.minutos_total_real} min")
        print(f"  Estado           : {self.estado.value}")
        print(linea)


# ─────────────────────────────────────────────
#  SISTEMA PRINCIPAL
# ─────────────────────────────────────────────

class SistemaUrgencias:
    def __init__(self):
        self.doctores: dict[str, Doctor]           = {}
        self.pacientes: list[Paciente]             = []
        self.cola_prioridad: list                  = []   # min-heap
        self.pacientes_en_atencion: list[Paciente] = []
        self.pacientes_finalizados: list[Paciente] = []

    # ══════════════════════════════
    #  GESTIÓN DE DOCTORES
    # ══════════════════════════════

    def ver_doctores(self):
        titulo("DOCTORES REGISTRADOS")
        if not self.doctores:
            print("  No hay doctores en turno actualmente.")
            return
        for doc in self.doctores.values():
            print(f"  {doc}")

    def ver_tabla_hospital(self):
        """Muestra el catálogo completo del hospital."""
        titulo("TABLA GENERAL — DOCTORES DEL HOSPITAL")
        print(f"  {'ID':<10} {'Nombre':<28} {'Especialidad'}")
        print(f"  {'─'*65}")
        for doc_id, info in TABLA_DOCTORES_HOSPITAL.items():
            print(f"  {doc_id:<10} {info['nombre']:<28} {info['especialidad']}")

    def agregar_doctor_desde_tabla(self, doc_id: str) -> bool:
        """Agrega un doctor al sistema buscándolo en el catálogo."""
        doc_id = doc_id.strip().upper()
        if doc_id in self.doctores:
            print(f"  ⚠ El doctor {doc_id} ya está en el turno activo.")
            return False
        if doc_id not in TABLA_DOCTORES_HOSPITAL:
            print(f"  ⚠ ID '{doc_id}' no encontrado en la tabla del hospital.")
            return False
        info = TABLA_DOCTORES_HOSPITAL[doc_id]
        self.doctores[doc_id] = Doctor(doc_id, info["nombre"], info["especialidad"])
        print(f"  ✔ Dr(a). {info['nombre']} ({info['especialidad']}) añadido al turno.")
        return True

    def agregar_doctor(self):
        """Agrega un doctor nuevo (puede ser de la tabla o uno nuevo)."""
        titulo("AGREGAR DOCTOR")
        print("  A) Buscar en tabla del hospital (por ID)")
        print("  B) Registrar doctor nuevo")
        op = input("\n  Opción: ").strip().upper()

        if op == "A":
            self.ver_tabla_hospital()
            doc_id = input("\n  Ingrese el ID del doctor: ").strip().upper()
            self.agregar_doctor_desde_tabla(doc_id)

        elif op == "B":
            doctor_id    = input("  ID del doctor    : ").strip()
            if doctor_id in self.doctores:
                print("  ⚠ Ya existe un doctor con ese ID en el turno.")
                return
            nombre       = input("  Nombre completo  : ").strip()
            especialidad = input("  Especialidad     : ").strip()
            doc = Doctor(doctor_id, nombre, especialidad)
            self.doctores[doctor_id] = doc
            # Si no está en el catálogo lo añadimos también
            if doctor_id not in TABLA_DOCTORES_HOSPITAL:
                TABLA_DOCTORES_HOSPITAL[doctor_id] = {
                    "nombre": nombre, "especialidad": especialidad
                }
                print(f"  ✔ Doctor {nombre} agregado al sistema y a la tabla del hospital.")
            else:
                print(f"  ✔ Doctor {nombre} agregado al turno.")
        else:
            print("  ⚠ Opción no válida.")

    def eliminar_doctor(self):
        titulo("ELIMINAR DOCTOR")
        self.ver_doctores()
        doctor_id = input("\n  ID del doctor a eliminar: ").strip()
        if doctor_id not in self.doctores:
            print("  ⚠ Doctor no encontrado en el turno.")
            return
        doc = self.doctores[doctor_id]
        if doc.estado == EstadoDoctor.EN_TURNO:
            print(f"  ⚠ El doctor {doc.nombre} está EN TURNO. No se puede eliminar.")
            return
        del self.doctores[doctor_id]
        print(f"  ✔ Doctor {doc.nombre} retirado del turno.")

    # ══════════════════════════════
    #  GESTIÓN DE DESCANSOS
    # ══════════════════════════════

    def gestionar_descansos(self):
        titulo("GESTIONAR DESCANSOS DE DOCTORES")
        disp = [d for d in self.doctores.values()
                if d.estado != EstadoDoctor.EN_TURNO]
        if not disp:
            print("  Todos los doctores están en turno. Finalice alguna atención primero.")
            return

        print("  Doctores disponibles para descanso:")
        for i, doc in enumerate(disp, 1):
            estado_extra = ""
            if doc.hora_fin_descanso:
                estado_extra = f" — regresa {doc.hora_fin_descanso.strftime('%H:%M')}"
            print(f"    {i}. [{doc.doctor_id}] Dr(a). {doc.nombre} "
                  f"({doc.estado.value}{estado_extra})")

        try:
            idx = int(input("\n  Seleccione doctor: ")) - 1
            doc = disp[idx]
        except (ValueError, IndexError):
            print("  ⚠ Opción inválida.")
            return

        if doc.en_descanso:
            print(f"\n  Dr(a). {doc.nombre} está en descanso.")
            print("  A) Registrar regreso del descanso")
            print("  0) Cancelar")
            op = input("  Opción: ").strip().upper()
            if op == "A":
                print(f"  {doc.terminar_descanso()}")
            return

        print(f"\n  Tipo de descanso para Dr(a). {doc.nombre}:")
        print("  1) Break         (15 min)")
        print("  2) Almuerzo      (60 min)")
        print("  3) Descanso      (30 min)")
        try:
            t = int(input("  Opción: "))
            tipo = {1: TipoDescanso.BREAK, 2: TipoDescanso.ALMUERZO,
                    3: TipoDescanso.DESCANSO}[t]
        except (ValueError, KeyError):
            print("  ⚠ Opción inválida.")
            return
        print(f"\n  {doc.iniciar_descanso(tipo)}")

    # ══════════════════════════════
    #  GESTIÓN DE PACIENTES
    # ══════════════════════════════

    def registrar_paciente(self):
        titulo("REGISTRAR PACIENTE")
        nombre   = input("  Nombre completo        : ").strip()
        cedula   = input("  Cédula                 : ").strip()
        for p in self.pacientes:
            if p.cedula == cedula:
                print("  ⚠ Ya existe un paciente con esa cédula.")
                return
        telefono = input("  Teléfono               : ").strip()
        sexo     = input("  Sexo (M/F)             : ").strip().upper()
        try:
            edad = int(input("  Edad (años)            : ").strip())
            if edad < 0 or edad > 120:
                raise ValueError
        except ValueError:
            print("  ⚠ Edad inválida.")
            return
        fnac     = input("  Fecha de nacimiento    : ").strip()
        tel_emer = input("  Teléfono de emergencia : ").strip()

        pac = Paciente(nombre, cedula, telefono, sexo, edad, fnac, tel_emer)
        self.pacientes.append(pac)
        print(f"\n  ✔ Paciente {nombre} ({edad} años) registrado — "
              f"{self._grupo_edad(edad)}.")
        print("  → Realice el TRIAGE para asignar turno.")

    @staticmethod
    def _grupo_edad(edad: int) -> str:
        for emin, emax, desc, _ in PRIORIDAD_EDAD:
            if emin <= edad <= emax:
                return desc
        return "Adulto"

    def realizar_triage(self):
        titulo("REALIZAR TRIAGE")
        sin_triage = [p for p in self.pacientes
                      if p.estado == EstadoPaciente.REGISTRADO]
        if not sin_triage:
            print("  No hay pacientes pendientes de triage.")
            return

        print("  Pacientes sin triage:")
        for i, p in enumerate(sin_triage, 1):
            print(f"    {i}. {p.nombre} ({p.edad} años) — CC: {p.cedula}")

        try:
            idx = int(input("\n  Seleccione número de paciente: ")) - 1
            if idx < 0 or idx >= len(sin_triage):
                raise ValueError
        except ValueError:
            print("  ⚠ Opción inválida.")
            return

        pac = sin_triage[idx]
        print(f"\n  Paciente: {pac.nombre} | {pac.edad} años | "
              f"{self._grupo_edad(pac.edad)}")
        print("\n  TIPOS DE EMERGENCIA:")
        tipos = list(TIPOS_EMERGENCIA.keys())
        for i, t in enumerate(tipos, 1):
            nivel, tiempo = TIPOS_EMERGENCIA[t]
            print(f"    {i:>2}. {t:<42} | T{nivel} — {tiempo} min atención")

        try:
            elec = int(input("\n  Seleccione tipo de emergencia: ")) - 1
            if elec < 0 or elec >= len(tipos):
                raise ValueError
        except ValueError:
            print("  ⚠ Opción inválida.")
            return

        pac.asignar_triage(tipos[elec])
        heapq.heappush(self.cola_prioridad, pac)
        print(f"\n  ✔ Triage asignado correctamente:")
        pac.resumen()

    def ver_pacientes(self):
        titulo("VISTA DE PACIENTES POR ESTADO")

        def listar(lista, titulo_sec):
            print(f"\n  {'─'*55}")
            print(f"  {titulo_sec} ({len(lista)})")
            print(f"  {'─'*55}")
            if not lista:
                print("  (ninguno)")
            for p in lista:
                extra = ""
                if p.tipo_emergencia:
                    extra = f"| T{p.nivel_triage} - {p.tipo_emergencia[:28]}"
                turno = f"Turno #{p.numero_turno}" if p.numero_turno else "Sin turno"
                print(f"  [{turno}] {p.nombre} ({p.edad}a) {extra}")

        listar([p for p in self.pacientes if p.estado == EstadoPaciente.REGISTRADO],
               "📋 REGISTRADOS (sin triage)")
        listar([p for p in self.pacientes if p.estado == EstadoPaciente.EN_ESPERA],
               "⏳ EN ESPERA (cola)")
        listar(self.pacientes_en_atencion, "🩺 EN ATENCIÓN")
        listar(self.pacientes_finalizados, "✅ FINALIZADOS")

    # ══════════════════════════════
    #  GESTIÓN DE TURNOS
    # ══════════════════════════════

    def ver_cola_turnos(self):
        titulo("COLA DE TURNOS (por prioridad)")
        if not self.cola_prioridad:
            print("  La cola está vacía.")
            return

        copia = sorted(self.cola_prioridad)
        print(f"  {'#':<4} {'T°':<6} {'Nombre':<22} "
              f"{'Edad':<6} {'Emergencia':<35} {'Triage'}")
        print(f"  {'─'*92}")
        acumulado = 0
        for pos, p in enumerate(copia, 1):
            print(f"  {pos:<4} #{p.numero_turno:<5} {p.nombre:<22} "
                  f"{p.edad:<6} {p.tipo_emergencia:<35} "
                  f"T{p.nivel_triage}")
        print(f"\n  {'─'*55}")
        print("  Tiempos estimados de espera acumulados:")
        for p in copia:
            print(f"  Turno #{p.numero_turno} | {p.nombre:<20} | "
                  f"Espera: {acumulado} min | Atención: {p.tiempo_atencion} min")
            acumulado += p.tiempo_atencion

    def atender_siguiente(self):
        titulo("ATENDER SIGUIENTE PACIENTE")
        if not self.cola_prioridad:
            print("  ⚠ No hay pacientes en cola.")
            return

        doctor_libre = next(
            (d for d in self.doctores.values() if d.estado == EstadoDoctor.DISPONIBLE),
            None
        )
        if not doctor_libre:
            print("  ⚠ No hay doctores disponibles en este momento.")
            return

        pac = heapq.heappop(self.cola_prioridad)
        pac.iniciar_atencion()
        doctor_libre.estado          = EstadoDoctor.EN_TURNO
        doctor_libre.paciente_actual = pac
        self.pacientes_en_atencion.append(pac)

        print(f"\n  ✔ ASIGNACIÓN EXITOSA:")
        print(f"  Paciente  : {pac.nombre} ({pac.edad} años) — Turno #{pac.numero_turno}")
        print(f"  Emergencia: {pac.tipo_emergencia}")
        print(f"  {DESCRIPCIONES_TRIAGE[pac.nivel_triage]}")
        print(f"  Doctor    : Dr(a). {doctor_libre.nombre} [{doctor_libre.doctor_id}]")
        print(f"  Hora inicio: {pac.hora_inicio_atencion.strftime('%H:%M:%S')}")
        print(f"  T. est.   : {pac.tiempo_atencion} min")

    def finalizar_atencion(self):
        titulo("FINALIZAR ATENCIÓN")
        if not self.pacientes_en_atencion:
            print("  No hay pacientes en atención actualmente.")
            return

        print("  Pacientes en atención:")
        for i, p in enumerate(self.pacientes_en_atencion, 1):
            print(f"    {i}. {p.nombre} (Turno #{p.numero_turno})")

        try:
            idx = int(input("\n  Seleccione número de paciente a finalizar: ")) - 1
            if idx < 0 or idx >= len(self.pacientes_en_atencion):
                raise ValueError
        except ValueError:
            print("  ⚠ Opción inválida.")
            return

        pac = self.pacientes_en_atencion.pop(idx)
        pac.finalizar_atencion()
        self.pacientes_finalizados.append(pac)

        for doc in self.doctores.values():
            if doc.paciente_actual == pac:
                doc.estado          = EstadoDoctor.DISPONIBLE
                doc.paciente_actual = None
                print(f"\n  ✔ Atención finalizada para {pac.nombre}.")
                print(f"  Doctor {doc.nombre} → DISPONIBLE.")
                break

        # Resumen final con tiempos
        print(f"\n  ─── Resumen de atención ────────────────────")
        print(f"  Hora de registro  : {pac.hora_registro.strftime('%H:%M:%S')}")
        if pac.hora_inicio_atencion:
            print(f"  Inicio atención   : {pac.hora_inicio_atencion.strftime('%H:%M:%S')}")
        if pac.hora_fin_atencion:
            print(f"  Fin atención      : {pac.hora_fin_atencion.strftime('%H:%M:%S')}")
        if pac.minutos_espera_real is not None:
            print(f"  Tiempo de espera  : {pac.minutos_espera_real} min")
        if pac.minutos_atencion_real is not None:
            print(f"  Tiempo de atención: {pac.minutos_atencion_real} min")
        if pac.minutos_total_real is not None:
            print(f"  ★ TIEMPO TOTAL    : {pac.minutos_total_real} min")
        print(f"  ─────────────────────────────────────────────")

    # ══════════════════════════════
    #  ESTADÍSTICAS
    # ══════════════════════════════

    def ver_estadisticas(self):
        titulo("ESTADÍSTICAS DEL SISTEMA")
        total      = len(self.pacientes)
        reg        = sum(1 for p in self.pacientes if p.estado == EstadoPaciente.REGISTRADO)
        espera     = sum(1 for p in self.pacientes if p.estado == EstadoPaciente.EN_ESPERA)
        atencion   = len(self.pacientes_en_atencion)
        finalizados= len(self.pacientes_finalizados)
        docs_disp  = sum(1 for d in self.doctores.values() if d.estado == EstadoDoctor.DISPONIBLE)
        docs_turno = sum(1 for d in self.doctores.values() if d.estado == EstadoDoctor.EN_TURNO)
        docs_desc  = sum(1 for d in self.doctores.values() if d.en_descanso)

        print(f"  ─── Pacientes ─────────────────────────────")
        print(f"  Total registrados : {total}")
        print(f"  Sin triage        : {reg}")
        print(f"  En cola           : {espera}")
        print(f"  En atención       : {atencion}")
        print(f"  Finalizados       : {finalizados}")
        print(f"  ─── Doctores ──────────────────────────────")
        print(f"  Disponibles       : {docs_disp}")
        print(f"  En turno          : {docs_turno}")
        print(f"  En descanso       : {docs_desc}")

        if self.cola_prioridad:
            t_cola = sum(p.tiempo_atencion for p in self.cola_prioridad)
            print(f"  ─── Cola ──────────────────────────────────")
            print(f"  T. total en cola  : {t_cola} min")
            if docs_disp > 0:
                print(f"  T. óptimo ({docs_disp} doc): ~{t_cola // docs_disp} min promedio")

        if self.pacientes_finalizados:
            tiempos = [p.minutos_total_real for p in self.pacientes_finalizados
                       if p.minutos_total_real is not None]
            if tiempos:
                print(f"  ─── Promedios (pacientes finalizados) ─────")
                print(f"  T. total promedio : {sum(tiempos)//len(tiempos)} min")
                print(f"  T. total mínimo   : {min(tiempos)} min")
                print(f"  T. total máximo   : {max(tiempos)} min")

        print(f"  ─── Hora del sistema ──────────────────────")
        print(f"  Ahora             : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


# ─────────────────────────────────────────────
#  FUNCIONES DE UTILIDAD (UI)
# ─────────────────────────────────────────────

def titulo(texto: str):
    ancho = 62
    print(f"\n{'═'*ancho}")
    print(f"  {texto.upper()}")
    print(f"{'═'*ancho}")


def menu_doctores(sistema: SistemaUrgencias):
    while True:
        titulo("MENÚ — DOCTORES")
        print("  A) Ver doctores en turno")
        print("  B) Ver tabla general del hospital")
        print("  C) Agregar doctor al turno")
        print("  D) Eliminar doctor del turno")
        print("  E) Gestionar descansos")
        print("  0) Volver")
        op = input("\n  Seleccione opción: ").strip().upper()
        if op == "A":
            sistema.ver_doctores()
        elif op == "B":
            sistema.ver_tabla_hospital()
        elif op == "C":
            sistema.agregar_doctor()
        elif op == "D":
            sistema.eliminar_doctor()
        elif op == "E":
            sistema.gestionar_descansos()
        elif op == "0":
            break
        else:
            print("  ⚠ Opción no válida.")
        input("\n  Presione ENTER para continuar...")


def menu_pacientes(sistema: SistemaUrgencias):
    while True:
        titulo("MENÚ — PACIENTES")
        print("  A) Registrar paciente")
        print("  B) Realizar Triage")
        print("  C) Ver pacientes")
        print("  0) Volver")
        op = input("\n  Seleccione opción: ").strip().upper()
        if op == "A":
            sistema.registrar_paciente()
        elif op == "B":
            sistema.realizar_triage()
        elif op == "C":
            sistema.ver_pacientes()
        elif op == "0":
            break
        else:
            print("  ⚠ Opción no válida.")
        input("\n  Presione ENTER para continuar...")


def menu_turnos(sistema: SistemaUrgencias):
    while True:
        titulo("MENÚ — TURNOS")
        print("  A) Ver cola de turnos")
        print("  B) Atender al siguiente paciente")
        print("  C) Finalizar atención")
        print("  0) Volver")
        op = input("\n  Seleccione opción: ").strip().upper()
        if op == "A":
            sistema.ver_cola_turnos()
        elif op == "B":
            sistema.atender_siguiente()
        elif op == "C":
            sistema.finalizar_atencion()
        elif op == "0":
            break
        else:
            print("  ⚠ Opción no válida.")
        input("\n  Presione ENTER para continuar...")


# ─────────────────────────────────────────────
#  MENÚ PRINCIPAL
# ─────────────────────────────────────────────

def main():
    sistema = SistemaUrgencias()

    print("\n" + "╔" + "═"*60 + "╗")
    print("║" + "  SISTEMA DE GESTIÓN DE URGENCIAS".center(60) + "║")
    print("║" + "  Hospital del Tunal - Bogotá, Colombia".center(60) + "║")
    print("╚" + "═"*60 + "╝")
    print(f"\n  Fecha y hora: {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}")

    # ── Selección de doctores en turno desde la tabla del hospital ──
    print("\n" + "─"*62)
    print("  INICIO DE TURNO — Selección de doctores")
    print("─"*62)
    sistema.ver_tabla_hospital()

    print("\n  Ingrese los IDs de los doctores que están en turno hoy.")
    print("  (Deje en blanco y presione ENTER para terminar)\n")
    while True:
        doc_id = input("  ID del doctor en turno: ").strip().upper()
        if not doc_id:
            break
        sistema.agregar_doctor_desde_tabla(doc_id)

    if not sistema.doctores:
        print("\n  ⚠ No se registraron doctores. Puede agregarlos desde el menú.")

    # ── Menú principal ──────────────────────────────────────────────
    while True:
        titulo("MENÚ PRINCIPAL")
        print(f"  🕐 {datetime.now().strftime('%H:%M:%S')}  |  "
              f"Doctores en turno: {len(sistema.doctores)}  |  "
              f"En cola: {len(sistema.cola_prioridad)}")
        print()
        print("  1) Doctores")
        print("  2) Pacientes")
        print("  3) Turnos")
        print("  4) Estadísticas")
        print("  0) Salir")
        op = input("\n  Seleccione opción: ").strip()

        if op == "1":
            menu_doctores(sistema)
        elif op == "2":
            menu_pacientes(sistema)
        elif op == "3":
            menu_turnos(sistema)
        elif op == "4":
            sistema.ver_estadisticas()
            input("\n  Presione ENTER para continuar...")
        elif op == "0":
            print("\n  Sistema cerrado. ¡Hasta luego!\n")
            break
        else:
            print("  ⚠ Opción no válida.")


if __name__ == "__main__":
    main()
# RÚBRICA: 
# EN QUE ME BASE PARA LAS DISTRIBUCIONES  
# QUE MEJORAS TUVIMOS 
# VARIABLES