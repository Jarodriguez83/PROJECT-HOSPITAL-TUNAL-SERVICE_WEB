"""
╔══════════════════════════════════════════════════════════════╗
║            SISTEMA DE GESTIÓN DE URGENCIAS                   ║
║         HOSPITAL DEL TUNAL - BOGOTÁ, COLOMBIA                ║
║                         SIGU                                 ║
╚══════════════════════════════════════════════════════════════╝
"""

import heapq
from datetime import datetime, timedelta
from enum import Enum

#  ENUMERACIONES Y CONSTANTES
class EstadoPaciente(Enum):
    REGISTRADO  = "REGISTRADO (SIN TRIAGE)"
    EN_ESPERA   = "EN ESPERA (cola)"
    EN_ATENCION = "EN ATENCIÓN"
    FINALIZADO  = "FINALIZADO"

class EstadoDoctor(Enum):
    DISPONIBLE  = "DISPONIBLE"
    EN_TURNO    = "EN TURNO"
    EN_DESCANSO = "EN DESCANSO"
    EN_ALMUERZO = "EN ALMUERZO"


class TipoDescanso(Enum):
    BREAK      = "BREAK (15 MIN)"
    ALMUERZO   = "ALMUERZO (60 MIN)"
    DESCANSO   = "DESCANSO (30 MIN)"

    @property
    def duracion_minutos(self):
        if self == TipoDescanso.BREAK:
            return 15
        elif self == TipoDescanso.ALMUERZO:
            return 60
        elif self == TipoDescanso.DESCANSO:
            return 30

#  TABLA GENERAL DE DOCTORES DEL HOSPITAL
TABLA_DOCTORES_HOSPITAL = {
    "MED001": {"nombre": "CARLOS RAMIREZ",     "especialidad": "MEDICINA DE EMERGENCIAS"},
    "MED002": {"nombre": "LAURA GÓMEZ",        "especialidad": "CIRUGÍA GENERAL"},
    "MED003": {"nombre": "ANDRÉS MARTÍNEZ",    "especialidad": "CARDIOLOGÍA"},
    "MED004": {"nombre": "SOFÍA TORRES",       "especialidad": "NEUROLOGÍA"},
    "MED005": {"nombre": "FELIPE HERRERA",     "especialidad": "TRAUMATOLOGÍA"},
    "MED006": {"nombre": "VALENTINA RÍOS",     "especialidad": "PEDIATRÍA"},
    "MED007": {"nombre": "JORGE MEDINA",       "especialidad": "MEDICINA INTERNA"},
    "MED008": {"nombre": "CAMILA VARGAS",      "especialidad": "ANESTESIOLOGÍA"},
    "MED009": {"nombre": "SEBASTIAN PARDO",    "especialidad": "MEDICINA DE EMERGENCIAS"},
    "MED010": {"nombre": "NATALIA OSPINA",     "especialidad": "GINECOLOGÍA"},
}

#  TIPOS DE EMERGENCIA
#  FORMATO: "NOMBRE": (NIVEL DE TRIAGE, TIEMPO DE ATENCIÓN) (TIEM. ATE. SE MANEJA EN MINUTOS)
TIPOS_EMERGENCIA = {
    # TRIAGE I - RESUCITACIÓN
    "PARO CARDIORESPIRATORIO":         (1, 60),
    "POLITRAUMATISMO GRAVE":            (1, 90),
    # TRIAGE II - EMERGENCIA
    "DIFICULTAD RESPIRATORIA SEVERA":   (2, 45),
    "ACV / DERRAME CEREBRAL":           (2, 50),
    # TRIAGE III - URGENCIA
    "FRACTURA CON COMPROMISO VASCULAR": (3, 35),
    "DOLOR ABDOMINAL AGUDO":            (3, 30),
    # TRIAGE IV - MENOS URGENTE
    "FIEBRE ALTA CON CONVULSIÓN":       (4, 25),
    "HERIDA CON SANGRADO MODERADO":     (4, 20),
    # TRIAGE V - NO URGENTE
    "DOLOR LEVE / MALESTAR GENERAL":    (5, 15),
    "CONSULTA MENOR (GRIPE | TOS)":      (5, 10),
}

DESCRIPCIONES_TRIAGE = {
    1: "TRIAGE I  - ROJO      (RESUCITACIÓN) → ATENCIÓN INMEDIATA",
    2: "TRIAGE II - NARANJA   (EMERGENCIA)   → ATENCIÓN < 10 min",
    3: "TRIAGE III- AMARILLO  (URGENTE)      → ATENCIÓN < 30 min",
    4: "TRIAGE IV - VERDE     (MENOS URGENTE)→ ATENCIÓN < 2 horas",
    5: "TRIAGE V  - AZUL      (NO URGENTE)   → ATENCIÓN < 4 horas",
}

# RANGOS DE EDAD (SE TIENE EN CUENTA PARA PRIORIZAR EN CASO DE EMPATE DE TRIAGE)
# (edad_min, edad_max, descripcion, peso_prioridad)
# Menor peso = mayor prioridad
PRIORIDAD_EDAD = [
    (0,   1,  "NEONATO",      0),   # MÁXIMA PRIORIDAD I
    (1,   5,  "INFANTE",      1),
    (60,  74, "ADULTO MAYOR", 2),
    (75,  199,"ANCIANO",      0),   # MÁXIMA PRIORIDAD II
]

#  CLASE DOCTOR
class Doctor:
    def __init__(self, doctor_id: str, nombre: str, especialidad: str):
        self.doctor_id    = doctor_id
        self.nombre       = nombre
        self.especialidad = especialidad
        self.estado       = EstadoDoctor.DISPONIBLE
        self.paciente_actual  = None
        # REGISTRO DE DESCANSO DE LOS DOCTORES
        self.descansos: list[dict] = []   # {tipo, inicio, fin}
        self.hora_fin_descanso: datetime | None = None

    # DESCANSOS DE LOS DOCTORES
    def iniciar_descanso(self, tipo: TipoDescanso) -> str:
        if self.estado == EstadoDoctor.EN_TURNO:
            return f" {self.nombre} SE ENCUENTRA EN TURNO. DEBE FINALIZAR LA ATENCIÓN PRIMERO."
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
        return (f"✔ {self.nombre} INICIA {tipo.value}. "
                f"REGREASA A LAS {fin.strftime('%H:%M:%S')}.")

    def terminar_descanso(self) -> str:
        if self.estado not in (EstadoDoctor.EN_DESCANSO, EstadoDoctor.EN_ALMUERZO):
            return f" {self.nombre} NO ESTÁ EN DESCANSO."
        self.estado            = EstadoDoctor.DISPONIBLE
        self.hora_fin_descanso = None
        return f"✔ {self.nombre} REGRESÓ. | ESTADO: DISPONIBLE. |"

    @property
    def disponible(self):
        return self.estado == EstadoDoctor.DISPONIBLE

    @property
    def en_descanso(self):
        return self.estado in (EstadoDoctor.EN_DESCANSO, EstadoDoctor.EN_ALMUERZO)

    def __str__(self):
        estado_str = self.estado.value
        if self.paciente_actual:
            estado_str += f" → ATENDIENDO A: {self.paciente_actual.nombre}"
        if self.hora_fin_descanso:
            estado_str += f" (REGRESA A: {self.hora_fin_descanso.strftime('%H:%M')})"
        return (f"[{self.doctor_id}] Dr(a). {self.nombre} | "
                f"{self.especialidad} | {estado_str}")

#  CLASE PACIENTE
#       PRIORIDAD DE LA EDAD
def _peso_edad(edad: int) -> int:
    """Retorna el peso de prioridad por edad. Menor = más urgente."""
    for emin, emax, _, peso in PRIORIDAD_EDAD:
        if emin <= edad <= emax:
            return peso
    return 3   # SI ES ADULTO NORMAL TIENE MENOR PRIORIDAD


class Paciente:
    _contador = 1   # NÚMERO DE TURNO
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

        self.tipo_emergencia  = None
        self.nivel_triage     = None
        self.tiempo_atencion  = None   # minutos estimados de atención
        self.numero_turno     = None

        self.hora_inicio_atencion: datetime | None = None
        self.hora_fin_atencion:    datetime | None = None

        self._prioridad = None

    # TODO: PRIORIDAD COMPUESTA
    # CRITERIOS (MENOR TUPLA = MAYOR URGENCIA):
    #   1. NIVEL DE TRIAGE (1 = MÁS URGENTE | 5 = MENOS URGENTE)
    #   2. PESO DE LA EDAD ( 0 = NEONATO/ANCIANO | 3 = ADULTO NORMAL)
    #   3. HORA DE REGISTRO (LLEGÓ ANTES → ATIENDE ANTES)
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

    # TIEMPOS CÁLCULOS DE TIEMPOS REALES
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
        print(f"  TURNO N°         : {self.numero_turno}")
        print(f"  NOMBRE           : {self.nombre}")
        print(f"  CÉDULA           : {self.cedula}")
        print(f"  EDAD             : {self.edad} años")
        print(f"  HORA DE REGISTRO : {self.hora_registro.strftime('%H:%M:%S')}")
        print(f"  EMERGENCIA       : {self.tipo_emergencia}")
        print(f"  {DESCRIPCIONES_TRIAGE[self.nivel_triage]}")
        print(f"  TIEMP. ATENCIÓN ESTIMADA : {self.tiempo_atencion} min")
        if self.minutos_espera_real is not None:
            print(f"  TIEMP. ESPERA REAL   : {self.minutos_espera_real} min")
        if self.minutos_atencion_real is not None:
            print(f"  TIEMP. ATENCIÓN REAL : {self.minutos_atencion_real} min")
        if self.minutos_total_real is not None:
            print(f"  TIEMP. TOTAL HOSPITAL: {self.minutos_total_real} min")
        print(f"  ESTADO           : {self.estado.value}")
        print(linea)

#  SISTEMA PRINCIPAL
class SistemaUrgencias:
    def __init__(self):
        self.doctores: dict[str, Doctor]           = {}
        self.pacientes: list[Paciente]             = []
        self.cola_prioridad: list                  = []   # min-heap
        self.pacientes_en_atencion: list[Paciente] = []
        self.pacientes_finalizados: list[Paciente] = []

    #  GESTIÓN DE DOCTORES
    def ver_doctores(self):
        titulo("DOCTORES REGISTRADOS")
        if not self.doctores:
            print("  NO HAY DOCTORES EN TURNO ACTUALMENTE.")
            return
        for doc in self.doctores.values():
            print(f"  {doc}")

    def ver_tabla_hospital(self):
        """Muestra el catálogo completo del hospital."""
        titulo("TABLA GENERAL — DOCTORES DEL HOSPITAL")
        print(f"  {'ID':<10} {'NOMBRE':<28} {'ESPECIALIDAD'}")
        print(f"  {'─'*65}")
        for doc_id, info in TABLA_DOCTORES_HOSPITAL.items():
            print(f"  {doc_id:<10} {info['nombre']:<28} {info['especialidad']}")

    def agregar_doctor_desde_tabla(self, doc_id: str) -> bool:
        """AGREGA UN DOCTOR AL SISTEMA BUSCANDOLO EN LA TABLA DE DOCTORES."""
        doc_id = doc_id.strip().upper()
        if doc_id in self.doctores:
            print(f" EL DOCTOR {doc_id} YA SE ENCUENTRA EN TURNO ACTIVO.")
            return False
        if doc_id not in TABLA_DOCTORES_HOSPITAL:
            print(f" ID '{doc_id}' NO SE ENCUENTRA EN LA TABLA DEL HOSPITAL.")
            return False
        info = TABLA_DOCTORES_HOSPITAL[doc_id]
        self.doctores[doc_id] = Doctor(doc_id, info["nombre"], info["especialidad"])
        print(f"  ✔ DR(A). {info['nombre']} ({info['especialidad']}) AÑADIDO AL TURNO.")
        return True

    def agregar_doctor(self):
        """Agrega un doctor nuevo (puede ser de la tabla o uno nuevo)."""
        titulo("AGREGAR DOCTOR")
        print("  A) BUSCAR EN LA TABLA DE DOCTORES (por ID)")
        print("  B) REGISTRAR UN NUEVO DOCTOR")
        op = input("\n  OPCIÓN: ").strip().upper()

        if op == "A":
            self.ver_tabla_hospital()
            doc_id = input("\n  INGRESE EL ID DEL DOCTOR: ").strip().upper()
            self.agregar_doctor_desde_tabla(doc_id)

        elif op == "B":
            doctor_id    = input("  ID DEL DOCTOR    : ").strip()
            if doctor_id in self.doctores:
                print("  ⚠ YA EXISTE UN ID CON ESE DOCTOR EN TURNO.")
                return
            nombre       = input("  NOMBRE COMPLETO  : ").strip()
            especialidad = input("  ESPECIALIDAD     : ").strip()
            doc = Doctor(doctor_id, nombre, especialidad)
            self.doctores[doctor_id] = doc
            # Si no está en el catálogo lo añadimos también
            if doctor_id not in TABLA_DOCTORES_HOSPITAL:
                TABLA_DOCTORES_HOSPITAL[doctor_id] = {
                    "nombre": nombre, "especialidad": especialidad
                }
                print(f" ✔ DOCTOR {nombre} AGREGADO AL SISTEMA Y A LA TABLA DEL HOSPITAL.")
            else:
                print(f" ✔ DOCTOR {nombre} AGREGADO AL TURNO.")
        else:
            print(" OPCIÓN NO VÁLIDA.")

    def eliminar_doctor(self):
        titulo("ELIMINAR DOCTOR")
        self.ver_doctores()
        doctor_id = input("\n  ID DEL DOCTOR A ELIMINAR: ").strip()
        if doctor_id not in self.doctores:
            print("  DOCTOR NO ENCONTRADO EN EL TURNO.")
            return
        doc = self.doctores[doctor_id]
        if doc.estado == EstadoDoctor.EN_TURNO:
            print(f" EL DOCTOR {doc.nombre} ESTÁ EN TURNO. NO SE PUEDE ELIMINAR.")
            return
        del self.doctores[doctor_id]
        print(f"  ✔ DOCTOR {doc.nombre} RETIRADO DEL TURNO.")

    #  GESTIÓN DE DESCANSOS

    def gestionar_descansos(self):
        titulo("GESTIONAR DESCANSOS DE DOCTORES")
        disp = [d for d in self.doctores.values()
                if d.estado != EstadoDoctor.EN_TURNO]
        if not disp:
            print(" TODOS LOS DOCTORES ESTÁN EN TURNO. FINALICE LA ATENCIÓN PRIMERO.")
            return

        print(" DOCTORES DISPONIBLES PARA DESCANSO:")
        for i, doc in enumerate(disp, 1):
            estado_extra = ""
            if doc.hora_fin_descanso:
                estado_extra = f" — REGRESA {doc.hora_fin_descanso.strftime('%H:%M')}"
            print(f"    {i}. [{doc.doctor_id}] DR(A). {doc.nombre} "
                  f"({doc.estado.value}{estado_extra})")

        try:
            idx = int(input("\n  SELECCIONE AL DOCTOR(A): ")) - 1
            doc = disp[idx]
        except (ValueError, IndexError):
            print(" OPCIÓN INVÁLIDA.")
            return

        if doc.en_descanso:
            print(f"\n  DR(A). {doc.nombre} ESTÁ EN DESCANSO.")
            print("  A) REGISTRAR REGRESO DEL DESCANSO")
            print("  0) CANCELAR")
            op = input("  OPCIÓN: ").strip().upper()
            if op == "A":
                print(f"  {doc.terminar_descanso()}")
            return

        print(f"\n  TIPO DE DESCANSO PARA DR(A). {doc.nombre}:")
        print("  1) BREAK         (15 min)")
        print("  2) ALMUERZO      (60 min)")
        print("  3) DESCANSO      (30 min)")
        try:
            t = int(input("  OPCIÓN: "))
            tipo = {1: TipoDescanso.BREAK, 2: TipoDescanso.ALMUERZO,
                    3: TipoDescanso.DESCANSO}[t]
        except (ValueError, KeyError):
            print(" OPCIÓN INVÁLIDA.")
            return
        print(f"\n  {doc.iniciar_descanso(tipo)}")

    #  GESTIÓN DE PACIENTES
    def registrar_paciente(self):
        titulo("REGISTRAR PACIENTE")
        nombre   = input("  NOMBRE COMPLETO        : ").strip()
        try:
            cedula   = input("  CÉDULA                 : ").strip()
            if len(cedula) < 8 or len(cedula) > 10: 
                raise ValueError
        except ValueError:
            print(" CÉDULA INVÁLIDA. DEBE TENER ENTRE 8 Y 10 DÍGITOS.")
            return
        for p in self.pacientes:
            if p.cedula == cedula:
                print("  YA EXISTE UN PACIENTE CON ESA CÉDULA.")
                return
        try:
            telefono = input("  TELÉFONO               : ").strip()
            if len(telefono) < 10 or len(telefono) > 10:
                raise ValueError
        except ValueError:
            print(" TELÉFONO INVÁLIDO. DEBE TENER 10 DÍGITOS.")
            return
        try:
            sexo     = input("  SEXO BIOLÓGICO (M/F)   : ").strip().upper()
            if sexo != "M" and sexo != "F":
                raise ValueError
        except ValueError:
            print(" SEXO INVÁLIDO. DEBE SER 'M' O 'F'.")
            return
        try:
            edad = int(input("  EDAD (AÑOS)        : ").strip())
            if edad < 0 or edad > 120:
                raise ValueError
        except ValueError:
            print(" EDAD INVÁLIDA.")
            return
        fnac     = input("  FECHA DE NACIMIENTO    : ").strip()
        try:
            tel_emer = input("  TELÉFONO DE EMERGENCIA : ").strip()
            if len(tel_emer) < 10 or len(tel_emer) > 10:
                raise ValueError
        except ValueError:
            print(" TELÉFONO DE EMERGENCIA INVÁLIDO. DEBE TENER 10 DÍGITOS.")
            return
        pac = Paciente(nombre, cedula, telefono, sexo, edad, fnac, tel_emer)
        self.pacientes.append(pac)
        print(f"\n  ✔ EL PACIENTE {nombre} ({edad} AÑOS) HA SIDO REGISTRADO — "
              f"{self._grupo_edad(edad)}.")
        print(" ( NOTA: REALIZAR EL TRIAGE PARA ASIGNAR EL TURNO. )")

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
            print(" NO HAY PACIENTES PENDIENTES DE TRIAGE.")
            return

        print(" PACIENTES SIN TRIAGE:")
        for i, p in enumerate(sin_triage, 1):
            print(f"    {i}. {p.nombre} ({p.edad} AÑOS) — CC: {p.cedula}")

        try:
            idx = int(input("\n  SELECCIONE A UN PACIENTE: ")) - 1
            if idx < 0 or idx >= len(sin_triage):
                raise ValueError
        except ValueError:
            print(" OPCIÓN INVÁLIDA.")
            return

        pac = sin_triage[idx]
        print(f"\n  PACIENTE: {pac.nombre} | {pac.edad} AÑOS | "
              f"{self._grupo_edad(pac.edad)}")
        print("\n  TIPOS DE EMERGENCIA:")
        tipos = list(TIPOS_EMERGENCIA.keys())
        for i, t in enumerate(tipos, 1):
            nivel, tiempo = TIPOS_EMERGENCIA[t]
            print(f"    {i:>2}. {t:<42} | T{nivel} — {tiempo} MIN ATENCIÓN")

        try:
            elec = int(input("\n  SELECCIONE TIPO DE EMERGENCIA: ")) - 1
            if elec < 0 or elec >= len(tipos):
                raise ValueError
        except ValueError:
            print(" OPCIÓN INVÁLIDA.")
            return

        pac.asignar_triage(tipos[elec])
        heapq.heappush(self.cola_prioridad, pac)
        print(f"\n  ✔ TRIAGE ASIGNADO CORRECTAMENTE:")
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
                turno = f"TURNO #{p.numero_turno}" if p.numero_turno else "SIN TURNO"
                print(f"  [{turno}] {p.nombre} ({p.edad}a) {extra}")

        listar([p for p in self.pacientes if p.estado == EstadoPaciente.REGISTRADO],
               "📋 REGISTRADOS (sin triage)")
        listar([p for p in self.pacientes if p.estado == EstadoPaciente.EN_ESPERA],
               "⏳ EN ESPERA (cola)")
        listar(self.pacientes_en_atencion, "🩺 EN ATENCIÓN")
        listar(self.pacientes_finalizados, "✅ FINALIZADOS")

    #  GESTIÓN DE TURNOS
    def ver_cola_turnos(self):
        titulo("COLA DE TURNOS (por prioridad)")
        if not self.cola_prioridad:
            print(" LA COLA ESTÁ VACÍA .")
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
        print(" TIEMPOS DE ESPERA ACUMULADOS:")
        for p in copia:
            print(f"  TURNO #{p.numero_turno} | {p.nombre:<20} | "
                  f" ESPERA: {acumulado} MIN | ATENCIÓN: {p.tiempo_atencion} MIN")
            acumulado += p.tiempo_atencion

    def atender_siguiente(self):
        titulo("ATENDER SIGUIENTE PACIENTE")
        if not self.cola_prioridad:
            print(" NO HAY PACIENTES EN COLA.")
            return

        doctor_libre = next(
            (d for d in self.doctores.values() if d.estado == EstadoDoctor.DISPONIBLE),
            None
        )
        if not doctor_libre:
            print(" NO HAY DOCTORES DISPONIBLES EN ESTE MOMENTO.")
            return

        pac = heapq.heappop(self.cola_prioridad)
        pac.iniciar_atencion()
        doctor_libre.estado          = EstadoDoctor.EN_TURNO
        doctor_libre.paciente_actual = pac
        self.pacientes_en_atencion.append(pac)

        print(f"\n  ✔ ASIGNACIÓN EXITOSA:")
        print(f"  PACIETE  : {pac.nombre} ({pac.edad} AÑOS) — TURNO #{pac.numero_turno}")
        print(f"  EMERGENCIA: {pac.tipo_emergencia}")
        print(f"  {DESCRIPCIONES_TRIAGE[pac.nivel_triage]}")
        print(f"  DOCTOR    : DR(A). {doctor_libre.nombre} [{doctor_libre.doctor_id}]")
        print(f"  HORA DE INICIO: {pac.hora_inicio_atencion.strftime('%H:%M:%S')}")
        print(f"  TIEMPO ESTIMADO   : {pac.tiempo_atencion} MIN")

    def finalizar_atencion(self):
        titulo("FINALIZAR ATENCIÓN")
        if not self.pacientes_en_atencion:
            print("  NO HAY PACIENTES EN ATENCIÓN.")
            return

        print("  PACIENTES EN ATENCIÓN:")
        for i, p in enumerate(self.pacientes_en_atencion, 1):
            print(f"    {i}. {p.nombre} (TURNO #{p.numero_turno})")

        try:
            idx = int(input("\n SELECCIONE EL NÚMERO DEL PACIENTE A FINALIZAR: ")) - 1
            if idx < 0 or idx >= len(self.pacientes_en_atencion):
                raise ValueError
        except ValueError:
            print(" OPCIÓN INVÁLIDA.")
            return

        pac = self.pacientes_en_atencion.pop(idx)
        pac.finalizar_atencion()
        self.pacientes_finalizados.append(pac)

        for doc in self.doctores.values():
            if doc.paciente_actual == pac:
                doc.estado          = EstadoDoctor.DISPONIBLE
                doc.paciente_actual = None
                print(f"\n  ✔ ATENCIÓN FINALIZADA PARA {pac.nombre}.")
                print(f"  DOCTOR {doc.nombre} → DISPONIBLE.")
                break

        # Resumen final con tiempos
        print(f"\n  RESUMEN DE LA ATENCIÓN - SIGU")
        print(f"  HORA DE REGISTRO  : {pac.hora_registro.strftime('%H:%M:%S')}")
        if pac.hora_inicio_atencion:
            print(f"  INICIO ATENCIÓN   : {pac.hora_inicio_atencion.strftime('%H:%M:%S')}")
        if pac.hora_fin_atencion:
            print(f"  FIN ATENCIÓN      : {pac.hora_fin_atencion.strftime('%H:%M:%S')}")
        if pac.minutos_espera_real is not None:
            print(f"  TIEMPO DE ESPERA  : {pac.minutos_espera_real} min")
        if pac.minutos_atencion_real is not None:
            print(f"  TIEMPO DE ATENCIÓN: {pac.minutos_atencion_real} min")
        if pac.minutos_total_real is not None:
            print(f"  ★ TIEMPO TOTAL    : {pac.minutos_total_real} min")
        print(f"  ─────────────────────────────────────────────")

    #  ESTADÍSTICAS
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

        print(f"  PACIENTES - HOSPITAL TUNAL")
        print(f"  TOTAL REGISTRADOS : {total}")
        print(f"  SIN TRIAGE        : {reg}")
        print(f"  EN COLA           : {espera}")
        print(f"  EN ATENCIÓN       : {atencion}")
        print(f"  FINALIZADOS       : {finalizados}")
        print(f"  ────────────────────────────────────")
        print(f"  DOCTORES - HOSPITAL TUNAL")
        print(f"  DISPONIBLES       : {docs_disp}")
        print(f"  EN TURNO          : {docs_turno}")
        print(f"  EN DESCANSO       : {docs_desc}")

        if self.cola_prioridad:
            t_cola = sum(p.tiempo_atencion for p in self.cola_prioridad)
            print(f" COLA - HOSPITAL DEL TUNAL - SIGU")
            print(f"  TIEM. TOTAL EN COLA: {t_cola} MIN")
            if docs_disp > 0:
                print(f"  TIEM. ÓPTIMO ({docs_disp} DOC): ~{t_cola // docs_disp} MIN PROMEDIO")

        if self.pacientes_finalizados:
            tiempos = [p.minutos_total_real for p in self.pacientes_finalizados
                       if p.minutos_total_real is not None]
            if tiempos:
                print(f"  PROMEDIOS - PACIENTES FINALIZADOS")
                print(f"  TIEM. TOTAL PROMEDIO : {sum(tiempos)//len(tiempos)} min")
                print(f"  TIEM. TOTAL MÍNIMO   : {min(tiempos)} min")
                print(f"  TIEM. TOTAL MÁXIMO   : {max(tiempos)} min")

        print(f"  HORA DEL SISTEMA ")
        print(f"  AHORA             : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

#  FUNCIONES DE UTILIDAD (UI)
def titulo(texto: str):
    ancho = 62
    print(f"\n{'═'*ancho}")
    print(f"  {texto.upper()}")
    print(f"{'═'*ancho}")


def menu_doctores(sistema: SistemaUrgencias):
    while True:
        titulo("MENÚ — DOCTORES")
        print("  A) VER DOCTORES EN TURNO")
        print("  B) VER TABLA GENERAL DE LOS DOCTORES")
        print("  C) AGREGAR DOCTOR AL TURNO")
        print("  D) ELIMINAR DOCTOR DEL TURNO")
        print("  E) GESTIONAR DESCANSOS")
        print("  0) VOLVER")
        op = input("\n  SELECCIONE UNA OPCIÓN: ").strip().upper()
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
            print(" OPCIÓN NO VÁLIDA.")
        input("\n  PRESIONE ENTER PARA CONTINUAR...")


def menu_pacientes(sistema: SistemaUrgencias):
    while True:
        titulo("MENÚ — PACIENTES")
        print("  A) REGISTRAR PACIENTE")
        print("  B) REALIZAR TRIAGE")
        print("  C) VER PACIENTES")
        print("  0) VOLVER")
        op = input("\n  SELECCIONE UNA OPCIÓN: ").strip().upper()
        if op == "A":
            sistema.registrar_paciente()
        elif op == "B":
            sistema.realizar_triage()
        elif op == "C":
            sistema.ver_pacientes()
        elif op == "0":
            break
        else:
            print(" OPCIÓN NO VÁLIDA.")
        input("\n  PRESIONE ENTER PARA CONTINUAR...")


def menu_turnos(sistema: SistemaUrgencias):
    while True:
        titulo("MENÚ — TURNOS")
        print("  A) VER COLA DE TURNOS")
        print("  B) ATENDER AL SIGUIENTE PACIENTE")
        print("  C) FINALIZAR ATENCIÓN")
        print("  0) VOLVER")
        op = input("\n  SELECCIONE UNA OPCIÓN: ").strip().upper()
        if op == "A":
            sistema.ver_cola_turnos()
        elif op == "B":
            sistema.atender_siguiente()
        elif op == "C":
            sistema.finalizar_atencion()
        elif op == "0":
            break
        else:
            print(" OPCIÓN NO VÁLIDA.")
        input("\n  PRESIONE ENTER PARA CONTINUAR...")

#  MENÚ PRINCIPAL
def main():
    sistema = SistemaUrgencias()

    print("\n" + "╔" + "═"*60 + "╗")
    print("║" + "  SISTEMA DE GESTIÓN DE URGENCIAS".center(60) + "║")
    print("║" + "  HOSPITAL DEL TUNAL - BOGOTÁ, COLOMBIA".center(60) + "║")
    print("╚" + "═"*60 + "╝")
    print(f"\n  Fecha y hora: {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}")

    # SELECCIÓN DE LOS DOCTORES - TABLA DE LOS DOCTORES
    print("\n" + "─"*62)
    print("  INICIO DE TURNO — SELECCIONE A LOS DOCTORES")
    print("─"*62)
    sistema.ver_tabla_hospital()

    print("\n  INGRESE A LOS ID DE LOS DOCTORES QUE ESTÁN EN TURNO.")
    while True:
        doc_id = input("  ID DEL DOCTOR: ").strip().upper()
        if not doc_id:
            break
        sistema.agregar_doctor_desde_tabla(doc_id)

    if not sistema.doctores:
        print("\n  NO SE REGISTRARON DOCTORES | AGREGUELOS DESDE EL MENÚ.")

    while True:
        titulo("MENÚ PRINCIPAL")
        print(f"  🕐 {datetime.now().strftime('%H:%M:%S')}  |  "
              f"Doctores en turno: {len(sistema.doctores)}  |  "
              f"En cola: {len(sistema.cola_prioridad)}")
        print()
        print("  1) DOCTORES")
        print("  2) PACIENTES")
        print("  3) TURNOS")
        print("  4) ESTADÍSTICAS")
        print("  0) SALIR")
        op = input("\n  SELECCIONE UNA OPCIÓN: ").strip()

        if op == "1":
            menu_doctores(sistema)
        elif op == "2":
            menu_pacientes(sistema)
        elif op == "3":
            menu_turnos(sistema)
        elif op == "4":
            sistema.ver_estadisticas()
            input("\n  PRESIONE ENTER PARA CONTINUAR...")
        elif op == "0":
            print("\n  SISTEMA CERRADO\n")
            break
        else:
            print(" OPCIÓN NO VÁLIDA.")


if __name__ == "__main__":
    main()
