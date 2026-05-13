import heapq
from datetime import datetime
from enum import Enum

class EstadoPaciente(Enum):
    REGISTRADO  = "Registrado"
    EN_ESPERA   = "En espera"
    EN_ATENCION = "En atención"
    FINALIZADO  = "Finalizado"

class EstadoDoctor(Enum):
    DISPONIBLE  = "Disponible"
    EN_TURNO    = "En turno"

TIPOS_EMERGENCIA = {
    # TRIAGE I - Resucitación (inmediato, vida en riesgo extremo)
    "Paro cardiorrespiratorio":      (1, 60),
    "Politraumatismo grave":         (1, 90),
    # TRIAGE II - Emergencia (muy urgente)
    "Dificultad respiratoria severa":(2, 45),
    "ACV / Derrame cerebral":        (2, 50),
    # TRIAGE III - Urgencia (urgente)
    "Fractura con compromiso vascular": (3, 35),
    "Dolor abdominal agudo":         (3, 30),
    # TRIAGE IV - Menos urgente
    "Fiebre alta con convulsión":    (4, 25),
    "Herida con sangrado moderado":  (4, 20),
    # TRIAGE V - No urgente
    "Dolor leve / Malestar general": (5, 15),
    "Consulta menor (gripe, tos)":   (5, 10),
}

DESCRIPCIONES_TRIAGE = {
    1: "TRIAGE I  - ROJO      (Resucitación) → Atención INMEDIATA",
    2: "TRIAGE II - NARANJA   (Emergencia)   → Atención < 10 min",
    3: "TRIAGE III- AMARILLO  (Urgente)      → Atención < 30 min",
    4: "TRIAGE IV - VERDE     (Menos urgente)→ Atención < 2 horas",
    5: "TRIAGE V  - AZUL      (No urgente)   → Atención < 4 horas",
}

class Doctor:
    def __init__(self, doctor_id: str, nombre: str, especialidad: str):
        self.doctor_id   = doctor_id
        self.nombre      = nombre
        self.especialidad= especialidad
        self.estado      = EstadoDoctor.DISPONIBLE
        self.paciente_actual = None   # Paciente que atiende ahora
    def __str__(self):
        estado_str = self.estado.value
        if self.paciente_actual:
            estado_str += f" → atendiendo a {self.paciente_actual.nombre}"
        return (f"[{self.doctor_id}] Dr(a). {self.nombre} | "
                f"{self.especialidad} | {estado_str}")

class Paciente:
    _contador = 1   
    def __init__(self, nombre: str, cedula: str, telefono: str,
                 sexo: str, eps: str, fecha_nacimiento: str,
                 telefono_emergencia: str):
        self.nombre              = nombre
        self.cedula              = cedula
        self.telefono            = telefono
        self.sexo                = sexo
        self.eps                 = eps
        self.fecha_nacimiento    = fecha_nacimiento
        self.telefono_emergencia = telefono_emergencia
        self.estado              = EstadoPaciente.REGISTRADO
        self.hora_registro       = datetime.now()

        self.tipo_emergencia     = None
        self.nivel_triage        = None
        self.tiempo_atencion     = None   # minutos estimados
        self.numero_turno        = None

        self._prioridad          = None

    def asignar_triage(self, tipo_emergencia: str):
        nivel, tiempo = TIPOS_EMERGENCIA[tipo_emergencia]
        self.tipo_emergencia = tipo_emergencia
        self.nivel_triage    = nivel
        self.tiempo_atencion = tiempo
        self.numero_turno    = Paciente._contador
        Paciente._contador  += 1
        self.estado          = EstadoPaciente.EN_ESPERA
        # Prioridad: menor nivel triage = mayor urgencia
        self._prioridad      = (self.nivel_triage, self.hora_registro)

    def __lt__(self, other):
        """Permite comparar pacientes en el heap (por triage y hora)."""
        return self._prioridad < other._prioridad

    def resumen(self):
        linea = "─" * 55
        print(linea)
        print(f"  Turno N°   : {self.numero_turno}")
        print(f"  Nombre     : {self.nombre}")
        print(f"  Cédula     : {self.cedula}")
        print(f"  Emergencia : {self.tipo_emergencia}")
        print(f"  {DESCRIPCIONES_TRIAGE[self.nivel_triage]}")
        print(f"  Tiempo est.: {self.tiempo_atencion} min")
        print(f"  Estado     : {self.estado.value}")
        print(linea)

class SistemaUrgencias:
    def __init__(self):
        self.doctores: dict[str, Doctor]  = {}
        self.pacientes: list[Paciente]    = []
        self.cola_prioridad: list         = []   # min-heap
        self.pacientes_en_atencion: list[Paciente] = []
        self.pacientes_finalizados: list[Paciente] = []

    # ── SECCIÓN DOCTORES ──────────────────────────────────────

    def ver_doctores(self):
        titulo("DOCTORES REGISTRADOS")
        if not self.doctores:
            print("  No hay doctores registrados.")
            return
        for doc in self.doctores.values():
            print(f"  {doc}")

    def agregar_doctor(self):
        titulo("AGREGAR DOCTOR")
        doctor_id   = input("  ID del doctor    : ").strip()
        if doctor_id in self.doctores:
            print("  ⚠ Ya existe un doctor con ese ID.")
            return
        nombre      = input("  Nombre completo  : ").strip()
        especialidad= input("  Especialidad     : ").strip()
        doc = Doctor(doctor_id, nombre, especialidad)
        self.doctores[doctor_id] = doc
        print(f"\n  ✔ Doctor {nombre} agregado correctamente.")

    def eliminar_doctor(self):
        titulo("ELIMINAR DOCTOR")
        self.ver_doctores()
        doctor_id = input("\n  ID del doctor a eliminar: ").strip()
        if doctor_id not in self.doctores:
            print("  ⚠ Doctor no encontrado.")
            return
        doc = self.doctores[doctor_id]
        if doc.estado == EstadoDoctor.EN_TURNO:
            print(f"  ⚠ El doctor {doc.nombre} está EN TURNO. No se puede eliminar.")
            return
        del self.doctores[doctor_id]
        print(f"  ✔ Doctor {doc.nombre} eliminado.")

    # ── SECCIÓN PACIENTES ─────────────────────────────────────

    def registrar_paciente(self):
        titulo("REGISTRAR PACIENTE")
        nombre   = input("  Nombre completo        : ").strip()
        cedula   = input("  Cédula                 : ").strip()
        # Verificar cédula duplicada
        for p in self.pacientes:
            if p.cedula == cedula:
                print("  ⚠ Ya existe un paciente con esa cédula.")
                return
        telefono = input("  Teléfono               : ").strip()
        sexo     = input("  Sexo (M/F)             : ").strip().upper()
        eps      = input("  EPS                    : ").strip()
        fnac     = input("  Fecha de nacimiento    : ").strip()
        tel_emer = input("  Teléfono de emergencia : ").strip()

        pac = Paciente(nombre, cedula, telefono, sexo, eps, fnac, tel_emer)
        self.pacientes.append(pac)
        print(f"\n  ✔ Paciente {nombre} registrado. Estado: {pac.estado.value}")
        print("  → Recuerde realizar el TRIAGE para asignar turno.")

    def realizar_triage(self):
        titulo("REALIZAR TRIAGE")
        # Buscar paciente registrado sin triage
        sin_triage = [p for p in self.pacientes
                      if p.estado == EstadoPaciente.REGISTRADO]
        if not sin_triage:
            print("  No hay pacientes pendientes de triage.")
            return

        print("  Pacientes sin triage:")
        for i, p in enumerate(sin_triage, 1):
            print(f"    {i}. {p.nombre} (Cédula: {p.cedula})")

        try:
            idx = int(input("\n  Seleccione número de paciente: ")) - 1
            if idx < 0 or idx >= len(sin_triage):
                print("  ⚠ Opción inválida.")
                return
        except ValueError:
            print("  ⚠ Ingrese un número válido.")
            return

        pac = sin_triage[idx]
        print(f"\n  Paciente: {pac.nombre}")
        print("\n  TIPOS DE EMERGENCIA DISPONIBLES:")
        tipos = list(TIPOS_EMERGENCIA.keys())
        for i, t in enumerate(tipos, 1):
            nivel, tiempo = TIPOS_EMERGENCIA[t]
            print(f"    {i:>2}. {t:<40} | {DESCRIPCIONES_TRIAGE[nivel][:30]}")

        try:
            elec = int(input("\n  Seleccione tipo de emergencia: ")) - 1
            if elec < 0 or elec >= len(tipos):
                print("  ⚠ Opción inválida.")
                return
        except ValueError:
            print("  ⚠ Ingrese un número válido.")
            return

        tipo_seleccionado = tipos[elec]
        pac.asignar_triage(tipo_seleccionado)
        heapq.heappush(self.cola_prioridad, pac)

        print(f"\n  ✔ Triage asignado correctamente:")
        pac.resumen()

    def ver_pacientes(self):
        titulo("VISTA DE PACIENTES POR ESTADO")

        registrados = [p for p in self.pacientes
                       if p.estado == EstadoPaciente.REGISTRADO]
        en_espera   = [p for p in self.pacientes
                       if p.estado == EstadoPaciente.EN_ESPERA]
        en_atencion = self.pacientes_en_atencion
        finalizados = self.pacientes_finalizados

        def listar(lista, titulo_sec):
            print(f"\n  {'─'*50}")
            print(f"  {titulo_sec} ({len(lista)})")
            print(f"  {'─'*50}")
            if not lista:
                print("  (ninguno)")
            for p in lista:
                extra = ""
                if p.tipo_emergencia:
                    extra = f"| T{p.nivel_triage} - {p.tipo_emergencia[:30]}"
                turno = f"Turno #{p.numero_turno}" if p.numero_turno else "Sin turno"
                print(f"  [{turno}] {p.nombre} {extra}")

        listar(registrados,  "📋 REGISTRADOS (sin triage)")
        listar(en_espera,    "⏳ EN ESPERA (cola)")
        listar(en_atencion,  "🩺 EN ATENCIÓN")
        listar(finalizados,  "✅ FINALIZADOS")

    # ── SECCIÓN TURNOS ────────────────────────────────────────

    def ver_cola_turnos(self):
        titulo("COLA DE TURNOS (por prioridad)")
        if not self.cola_prioridad:
            print("  La cola está vacía.")
            return

        # Crear copia ordenada sin modificar el heap
        copia = sorted(self.cola_prioridad)
        print(f"  {'#':<5} {'Turno':<8} {'Nombre':<25} {'Emergencia':<35} {'Triage'}")
        print(f"  {'─'*90}")
        for pos, p in enumerate(copia, 1):
            print(f"  {pos:<5} #{p.numero_turno:<7} {p.nombre:<25} "
                  f"{p.tipo_emergencia:<35} T{p.nivel_triage} - "
                  f"{DESCRIPCIONES_TRIAGE[p.nivel_triage].split('→')[1].strip()}")

        # Calcular tiempo estimado de espera acumulado
        print(f"\n  {'─'*50}")
        acumulado = 0
        for p in copia:
            print(f"  Turno #{p.numero_turno} | {p.nombre:<20} | "
                  f"Espera estimada: {acumulado} min | Atención: {p.tiempo_atencion} min")
            acumulado += p.tiempo_atencion

    def atender_siguiente(self):
        titulo("ATENDER SIGUIENTE PACIENTE")

        if not self.cola_prioridad:
            print("  ⚠ No hay pacientes en cola.")
            return

        # Buscar doctor disponible
        doctor_libre = None
        for doc in self.doctores.values():
            if doc.estado == EstadoDoctor.DISPONIBLE:
                doctor_libre = doc
                break

        if not doctor_libre:
            print("  ⚠ No hay doctores disponibles en este momento.")
            return

        # Sacar al paciente más prioritario del heap
        pac = heapq.heappop(self.cola_prioridad)

        # Asignar
        pac.estado           = EstadoPaciente.EN_ATENCION
        doctor_libre.estado  = EstadoDoctor.EN_TURNO
        doctor_libre.paciente_actual = pac
        self.pacientes_en_atencion.append(pac)

        print(f"\n  ✔ ASIGNACIÓN EXITOSA:")
        print(f"  Paciente : {pac.nombre} (Turno #{pac.numero_turno})")
        print(f"  Emergencia: {pac.tipo_emergencia}")
        print(f"  {DESCRIPCIONES_TRIAGE[pac.nivel_triage]}")
        print(f"  Doctor   : Dr(a). {doctor_libre.nombre} [{doctor_libre.doctor_id}]")
        print(f"  Tiempo estimado de atención: {pac.tiempo_atencion} min")

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
                print("  ⚠ Opción inválida.")
                return
        except ValueError:
            print("  ⚠ Ingrese un número válido.")
            return

        pac = self.pacientes_en_atencion.pop(idx)
        pac.estado = EstadoPaciente.FINALIZADO
        self.pacientes_finalizados.append(pac)

        # Liberar al doctor
        for doc in self.doctores.values():
            if doc.paciente_actual == pac:
                doc.estado           = EstadoDoctor.DISPONIBLE
                doc.paciente_actual  = None
                print(f"\n  ✔ Atención finalizada.")
                print(f"  Paciente {pac.nombre} marcado como FINALIZADO.")
                print(f"  Doctor {doc.nombre} ahora está DISPONIBLE.")
                return

    # ── ESTADÍSTICAS ──────────────────────────────────────────

    def ver_estadisticas(self):
        titulo("ESTADÍSTICAS DEL SISTEMA")
        total      = len(self.pacientes)
        reg        = sum(1 for p in self.pacientes if p.estado == EstadoPaciente.REGISTRADO)
        espera     = sum(1 for p in self.pacientes if p.estado == EstadoPaciente.EN_ESPERA)
        atencion   = len(self.pacientes_en_atencion)
        finalizados= len(self.pacientes_finalizados)
        docs_disp  = sum(1 for d in self.doctores.values() if d.estado == EstadoDoctor.DISPONIBLE)
        docs_turno = sum(1 for d in self.doctores.values() if d.estado == EstadoDoctor.EN_TURNO)

        print(f"  Total pacientes registrados : {total}")
        print(f"  Sin triage                  : {reg}")
        print(f"  En cola de espera           : {espera}")
        print(f"  En atención                 : {atencion}")
        print(f"  Finalizados                 : {finalizados}")
        print(f"  {'─'*40}")
        print(f"  Doctores disponibles        : {docs_disp}")
        print(f"  Doctores en turno           : {docs_turno}")

        if self.cola_prioridad:
            tiempo_total = sum(p.tiempo_atencion for p in self.cola_prioridad)
            print(f"  {'─'*40}")
            print(f"  Tiempo total estimado en cola: {tiempo_total} min")
            if len(self.cola_prioridad) > 0 and docs_disp > 0:
                tiempo_opt = tiempo_total // docs_disp if docs_disp else tiempo_total
                print(f"  Con {docs_disp} doctor(es) disponible(s): ~{tiempo_opt} min promedio")


# ─────────────────────────────────────────────
#  FUNCIONES DE UTILIDAD (UI)
# ─────────────────────────────────────────────

def titulo(texto: str):
    ancho = 60
    print(f"\n{'═'*ancho}")
    print(f"  {texto.upper()}")
    print(f"{'═'*ancho}")


def menu_doctores(sistema: SistemaUrgencias):
    while True:
        titulo("MENÚ - DOCTORES")
        print("  A) Ver doctores disponibles")
        print("  B) Agregar doctor")
        print("  C) Eliminar doctor")
        print("  0) Volver")
        op = input("\n  Seleccione opción: ").strip().upper()
        if op == "A":
            sistema.ver_doctores()
        elif op == "B":
            sistema.agregar_doctor()
        elif op == "C":
            sistema.eliminar_doctor()
        elif op == "0":
            break
        else:
            print("  ⚠ Opción no válida.")
        input("\n  Presione ENTER para continuar...")


def menu_pacientes(sistema: SistemaUrgencias):
    while True:
        titulo("MENÚ - PACIENTES")
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
        titulo("MENÚ - TURNOS")
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

    print("\n" + "╔" + "═"*58 + "╗")
    print("║" + "  SISTEMA DE GESTIÓN DE URGENCIAS".center(58) + "║")
    print("║" + "  Hospital del Tunal - Bogotá, Colombia".center(58) + "║")
    print("╚" + "═"*58 + "╝")

    n_doctores = 0
    while True:
        try:
            n_doctores = int(input("\n  ¿Cuántos doctores hay disponibles hoy? "))
            if n_doctores < 0:
                raise ValueError
            break
        except ValueError:
            print("  ⚠ Ingrese un número entero positivo.")

    if n_doctores > 0:
        print(f"\n  Registre los {n_doctores} doctor(es).\n")
        for i in range(1, n_doctores + 1):
            print(f"  --- Doctor {i} de {n_doctores} ---")
            sistema.agregar_doctor()

    while True:
        titulo("MENÚ PRINCIPAL")
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


# EN QUE ME BASE PARA LAS DISTRIBUCIONES  
# QUE MEJORAS TUVIMOS 
# VARIABLES