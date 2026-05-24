import heapq
from datetime import datetime
from enum import Enum

class EstadoPaciente(Enum):
    REGISTRADO  = "REGISTRADO"
    EN_ESPERA   = "EN ESPERA"
    EN_ATENCION = "EN ATENCION"
    FINALIZADO  = "FINALIZADO"

class EstadoDoctor(Enum):
    DISPONIBLE  = "DISPONIBLE"
    EN_TURNO    = "OCUPADO"

TIPOS_EMERGENCIA = {
    # TRIAGE I 
    "PARO CARDIORESPIRATORIO": (1, 60),
    "POLITRAUMATISMO GRAVE": (1, 90),
    # TRIAGE II 
    "DIFICULTAD RESPIRATORIA SEVERA": (2, 45),
    "ACV / DERRAME CEREBRAL": (2, 50),
    # TRIAGE III 
    "FRACTURA CON COMPROMISO VASCULAR": (3, 35),
    "DOLOR ABDOMINAL AGUDO": (3, 30),
    # TRIAGE IV
    "FIEBRE ALTA CON CONVULSIONES": (4, 25),
    "HERIDA CON SANGRADO MODERADO": (4, 20),
    # TRIAGE V
    "DOLOR LEVE / MALESTAR GENERAL": (5, 15),
    "CONSULTA MENOR (GRIPE, TOS)": (5, 10),
}

DESCRIPCIONES_TRIAGE = {
    1: "TRIAGE I  - ROJO      (RESUCITACIÓN) → ATENCIÓN INMEDIATA",
    2: "TRIAGE II - NARANJA   (EMERGENCIA)   → ATENCIÓN MENOR A 10 min",
    3: "TRIAGE III- AMARILLO  (URGENCIA)      → ATENCIÓN MENOR A 30 min",
    4: "TRIAGE IV - VERDE     (MENOS URGENTE)→ ATENCIÓN MENOR A 2 horas",
    5: "TRIAGE V  - AZUL      (NO URGENTE)   → ATENCIÓN MENOR A 4 horas",
}

class Doctor:
    def __init__(self, doctor_id: str, nombre: str, especialidad: str):
        self.doctor_id   = doctor_id
        self.nombre      = nombre
        self.especialidad= especialidad
        self.estado      = EstadoDoctor.DISPONIBLE
        self.paciente_actual = None  
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
        self.tiempo_atencion     = None   
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
        # COMPARACIÓN DE PACIENTES (TRIAGE Y HORA) PARA EL HEAP DE PRIORIDAD
        # EL HEAP ES UN MIN-HEAP, POR LO QUE UN PACIENTE CON MENOR NIVEL DE TRIAGE (MAYOR PRIORIDAD) DEBE SER "MENOR" QUE OTRO CON NIVEL MAYOR
        return self._prioridad < other._prioridad

    def resumen(self):
        linea = "─" * 55
        print(linea)
        print(f"  TURNO N°   : {self.numero_turno}")
        print(f"  NOMBRE     : {self.nombre}")
        print(f"  CÉDULA     : {self.cedula}")
        print(f"  EMERGENCIA : {self.tipo_emergencia}")
        print(f"  {DESCRIPCIONES_TRIAGE[self.nivel_triage]}")
        print(f"  TIEMPO ESTIMADO: {self.tiempo_atencion} min")
        print(f"  ESTADO     : {self.estado.value}")
        print(linea)

class SistemaUrgencias:
    def __init__(self):
        self.doctores: dict[str, Doctor]  = {}
        self.pacientes: list[Paciente]    = []
        self.cola_prioridad: list         = []   
        self.pacientes_en_atencion: list[Paciente] = []
        self.pacientes_finalizados: list[Paciente] = []

    def ver_doctores(self):
        titulo("DOCTORES REGISTRADOS")
        if not self.doctores:
            print(" NO HAY DOCTORES REGISTRADOS.")
            return
        for doc in self.doctores.values():
            print(f"  {doc}")

    def agregar_doctor(self):
        titulo("AGREGAR DOCTOR")
        doctor_id   = input("  ID DEL DOCTOR: ").strip()
        if doctor_id in self.doctores:
            print("  YA EXISTE UN DOCTOR CON ESE ID.")
            return
        nombre      = input(" NOMBRE COMPLETO: ").strip()
        especialidad= input("  ESPECIALIDAD: ").strip()
        doc = Doctor(doctor_id, nombre, especialidad)
        self.doctores[doctor_id] = doc
        print(f"\n DOCTOR {nombre} HA SIDO AGREGADO CON ÉXITO.")

    def eliminar_doctor(self):
        titulo("ELIMINAR DOCTOR")
        self.ver_doctores()
        doctor_id = input("\n ID DEL DOCTOR A ELIMINAR: ").strip()
        if doctor_id not in self.doctores:
            print(" DOCTOR NO ENCONTRADO.")
            return
        doc = self.doctores[doctor_id]
        if doc.estado == EstadoDoctor.EN_TURNO:
            print(f" EL DOCTOR {doc.nombre} SE ENCUENTRA EN TURNO. NO SE PUEDE ELIMINAR.")
            return
        del self.doctores[doctor_id]
        print(f" DOCTOR {doc.nombre} HA SIDO ELIMINADO CON ÉXITO.")

    def registrar_paciente(self):
        titulo("REGISTRAR PACIENTE")
        nombre   = input(" NOMBRE COMPLETO: ").strip()
        cedula   = input(" CÉDULA: ").strip()
        # VERIFICACIÓN DE CÉDULA DUPLICADA
        for p in self.pacientes:
            if p.cedula == cedula:
                print(" ESTÁ CÉDULA YA HA SIDO REGISTRADA POR UN PACIENTE ANTERIOR.")
                return
        telefono = input(" TELÉFONO: ").strip()
        sexo     = input("  SEXO (M/F): ").strip().upper()
        eps      = input("  EPS: ").strip()
        fnac     = input("  FECHA NACIMIENTO: ").strip()
        tel_emer = input("  TEL. DE EMERGENCIA: ").strip()

        pac = Paciente(nombre, cedula, telefono, sexo, eps, fnac, tel_emer)
        self.pacientes.append(pac)
        print(f"\n PACIENTE {nombre} REGISTRADO CON ÉXITO. ESTADO: {pac.estado.value}")
        print(" REALIZAR EL TRIAGE PARA ASIGNACIÓN DE TURNO.")

    def realizar_triage(self):
        titulo("REALIZAR TRIAGE")
        # Buscar paciente registrado sin triage
        sin_triage = [p for p in self.pacientes
                      if p.estado == EstadoPaciente.REGISTRADO]
        if not sin_triage:
            print(" NO HAY PACIENTES PENDIENTES POR TRIAGE.")
            return

        print(" PACIENTES SIN TRIAGE:")
        for i, p in enumerate(sin_triage, 1):
            print(f"    {i}. {p.nombre} (CÉDULA: {p.cedula})")

        try:
            idx = int(input("\n  SELECCIONE NÚMERO DEL PACIENTE: ")) - 1
            if idx < 0 or idx >= len(sin_triage):
                print(" OPCIÓN INVÁLIDA.")
                return
        except ValueError:
            print("  INGRESE UN NÚMERO VÁLIDO.")
            return

        pac = sin_triage[idx]
        print(f"\n  PACIENTE: {pac.nombre}")
        print("\n  TIPOS DE EMERGENCIA DISPONIBLES:")
        tipos = list(TIPOS_EMERGENCIA.keys())
        for i, t in enumerate(tipos, 1):
            nivel, tiempo = TIPOS_EMERGENCIA[t]
            print(f"    {i:>2}. {t:<40} | {DESCRIPCIONES_TRIAGE[nivel][:30]}")

        try:
            elec = int(input("\n  SELECCIONE EL TIPO DE EMERGENCIA: ")) - 1
            if elec < 0 or elec >= len(tipos):
                print("  OPCIÓN INVÁLIDA.")
                return
        except ValueError:
            print("  INGRESE UN NÚMERO VÁLIDO.")
            return

        tipo_seleccionado = tipos[elec]
        pac.asignar_triage(tipo_seleccionado)
        heapq.heappush(self.cola_prioridad, pac)

        print(f"\n  TRIAGE ASIGNADO CON ÉXITO")
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
                turno = f"TURNO #{p.numero_turno}" if p.numero_turno else "SIN TURNO"
                print(f"  [{turno}] {p.nombre} {extra}")

        listar(registrados,  "📋 REGISTRADOS (SIN TRIAGE)")
        listar(en_espera,    "⏳ EN ESPERA (EN COLA)")
        listar(en_atencion,  "🩺 EN ATENCIÓN")
        listar(finalizados,  "✅ FINALIZADOS")
# FUNCIÓN PARA VER LA COLA DE TURNOS ORDENADA POR PRIORIDAD (TRIAGE Y HORA DE REGISTRO)
    def ver_cola_turnos(self):
        titulo("COLA DE TURNOS (POR PRIORIDAD)")
        if not self.cola_prioridad:
            print("  LA COLA ESTÁ VACÍA.")
            return
# TODO: MOSTRAR LA COLA DE PRIORIDAD ORDENADA POR NIVEL DE TRIAGE Y HORA DE REGISTRO, CON TIEMPO ESTIMADO DE ESPERA ACUMULADO
# COPIA DE LA COLA DE PRIORIDAD PARA MOSTRARLA ORDENADA SIN MODIFICAR EL HEAP ORIGINAL
# EL HEAP ES UN MIN-HEAP, POR LO QUE LOS PACIENTES CON MAYOR PRIORIDAD (MENOR NIVEL DE TRIAGE) APARECERÁN PRIMERO
        copia = sorted(self.cola_prioridad)
        print(f"  {'#':<5} {'TURNO':<8} {'NOMBRE':<25} {'EMERGENCIA':<35} {'TRIAGE'}")
        print(f"  {'─'*90}")
        for pos, p in enumerate(copia, 1):
            print(f"  {pos:<5} #{p.numero_turno:<7} {p.nombre:<25} "
                  f"{p.tipo_emergencia:<35} T{p.nivel_triage} - "
                  f"{DESCRIPCIONES_TRIAGE[p.nivel_triage].split('→')[1].strip()}")

        # CALCULAR EL TIEMPO DE ESPERA ACUMULADO PARA CADA PACIENTE EN LA COLA
        print(f"\n  {'─'*50}")
        acumulado = 0
        for p in copia:
            print(f"  TURNO #{p.numero_turno} | {p.nombre:<20} | "
                  f"ESPERA ESTIMADA: {acumulado} MIN | ATENCIÓN: {p.tiempo_atencion} MIN")
            acumulado += p.tiempo_atencion

    def atender_siguiente(self):
        titulo(" | ATENDER SIGUIENTE PACIENTE |")

        if not self.cola_prioridad:
            print(" NO HAY PACIENTES EN COLA.")
            return

        # Buscar doctor disponible
        doctor_libre = None
        for doc in self.doctores.values():
            if doc.estado == EstadoDoctor.DISPONIBLE:
                doctor_libre = doc
                break

        if not doctor_libre:
            print("  NO HAY DOCTORES DISPONIBLES EN ESTE MOMENTO.")
            return
        # TODO: SE ASIGNA AL PACIENTE MÁS PRIORITARIO DE LA COLA EL DOCTOR DISPONIBLE, SE ACTUALIZA EL ESTADO DEL PACIENTE Y DEL DOCTOR, Y SE MUEVE EL PACIENTE A LA LISTA DE ATENCIÓN
        # SACAR AL PACIENTE MÁS PRIORITARIO DE LA COLA
        pac = heapq.heappop(self.cola_prioridad)

        # ASIGNACIÓN DE DOCTOR Y ACTUALIZACIÓN DE ESTADOS
        pac.estado           = EstadoPaciente.EN_ATENCION
        doctor_libre.estado  = EstadoDoctor.EN_TURNO
        doctor_libre.paciente_actual = pac
        self.pacientes_en_atencion.append(pac)

        print(f"\n  LA ASIGNACIÓN DE DOCTOR ES EXITOSA:")
        print(f"  PACIENTE : {pac.nombre} (TURNO #{pac.numero_turno})")
        print(f"  EMERGENCIA: {pac.tipo_emergencia}")
        print(f"  {DESCRIPCIONES_TRIAGE[pac.nivel_triage]}")
        print(f"  MÉDICO: DR(A). {doctor_libre.nombre} [{doctor_libre.doctor_id}]")
        print(f"  TIEM. ESTIMADO DE ATENCIÓN: {pac.tiempo_atencion} MIN")

    def finalizar_atencion(self):
        titulo("FINALIZAR ATENCIÓN")
        if not self.pacientes_en_atencion:
            print(" NO HAY PACIENTES EN ATENCIÓN")
            return

        print(" PACIENTES EN ATENCIÓN:")
        for i, p in enumerate(self.pacientes_en_atencion, 1):
            print(f"    {i}. {p.nombre} (TURNO #{p.numero_turno})")

        try:
            idx = int(input("\n SELECCIONE EL NÚMERO DE PACIENTE A FINALIZAR: ")) - 1
            if idx < 0 or idx >= len(self.pacientes_en_atencion):
                print("  OPCIÓN INVÁLIDA.")
                return
        except ValueError:
            print("  INGRESE UN NÚMERO VÁLIDO.")
            return

        pac = self.pacientes_en_atencion.pop(idx)
        pac.estado = EstadoPaciente.FINALIZADO
        self.pacientes_finalizados.append(pac)

        # LIBERAR AL DOCTOR QUE ATENDÍA A X PACIENTE
        for doc in self.doctores.values():
            if doc.paciente_actual == pac:
                doc.estado           = EstadoDoctor.DISPONIBLE
                doc.paciente_actual  = None
                print(f"\n------------------------")
                print(f"\n  ATENCIÓN FINALIZADA.")
                print(f"  PACIENTE {pac.nombre} | ESTADO: FINALIZADO")
                print(f"  MÉDICO {doc.nombre} | ESTADO: DISPONIBLE.")
                return

    # ESTADISTICAS DEL SISTEMA SIGU - SEGÚN ATENCIÓN DE URGENCIAS
    def ver_estadisticas(self):
        titulo("ESTADÍSTICAS DEL SISTEMA")
        total      = len(self.pacientes)
        reg        = sum(1 for p in self.pacientes if p.estado == EstadoPaciente.REGISTRADO)
        espera     = sum(1 for p in self.pacientes if p.estado == EstadoPaciente.EN_ESPERA)
        atencion   = len(self.pacientes_en_atencion)
        finalizados= len(self.pacientes_finalizados)
        docs_disp  = sum(1 for d in self.doctores.values() if d.estado == EstadoDoctor.DISPONIBLE)
        docs_turno = sum(1 for d in self.doctores.values() if d.estado == EstadoDoctor.EN_TURNO)

        print(f"  TOTAL PACIENTES REGISTRADOS: {total}")
        print(f"  PACIENTES SIN TRIAGE: {reg}")
        print(f"  PACIENTES EN COLA DE ESPERA: {espera}")
        print(f"  PACIENTES EN ATENCIÓN: {atencion}")
        print(f"  PACIENTES FINALIZADOS: {finalizados}")
        print(f"  {'─'*40}")
        print(f"  DOCTORES DISPONIBLES: {docs_disp}")
        print(f"  DOCTORES EN TURNO: {docs_turno}")

        if self.cola_prioridad:
            tiempo_total = sum(p.tiempo_atencion for p in self.cola_prioridad)
            print(f"  {'─'*40}")
            print(f"  TIEMPO TOTAL ESTIMADO EN COLA: {tiempo_total} min")
            if len(self.cola_prioridad) > 0 and docs_disp > 0:
                tiempo_opt = tiempo_total // docs_disp if docs_disp else tiempo_total
                print(f"  CON CAPACIDAD DE {docs_disp} DOCTOR(ES) DISPONIBLE(S): ~{tiempo_opt} MIN PROMEDIO")

# FUNCIONES DE INTERFAZ DE USUARIO (MENÚS)
def titulo(texto: str):
    ancho = 60
    print(f"\n{'═'*ancho}")
    print(f"  {texto.upper()}")
    print(f"{'═'*ancho}")

# FUNCIÓN PARA MOSTRAR EL MENÚ DE DOCTORES, PACIENTES Y TURNOS, CON OPCIONES PARA CADA SECCIÓN
def menu_doctores(sistema: SistemaUrgencias):
    while True:
        titulo("MENÚ - DOCTORES")
        print("  A) VER DOCTORES DISPONIBLES")
        print("  B) AGREGAR UN DOCTOR(A)")
        print("  C) ELIMINAR DOCTOR(A)")
        print("  0) RETORNAR")
        op = input("\n  SELECCIONA UNA OPCIÓN: ").strip().upper()
        if op == "A":
            sistema.ver_doctores()
        elif op == "B":
            sistema.agregar_doctor()
        elif op == "C":
            sistema.eliminar_doctor()
        elif op == "0":
            break
        else:
            print(" OPCIÓN INVÁLIDA.")
        input("\n PRESIONE ENTER PARA CONTINUAR...")


def menu_pacientes(sistema: SistemaUrgencias):
    while True:
        titulo("MENÚ - PACIENTES")
        print("  A) REGISTRAR UN PACIENTE")
        print("  B) ASIGNAR TRIAGE A UN PACIENTE")
        print("  C) VER PACIENTES POR ESTADO")
        print("  0) RETORNAR")
        op = input("\n  SELECCIONA UNA OPCIÓN: ").strip().upper()
        if op == "A":
            sistema.registrar_paciente()
        elif op == "B":
            sistema.realizar_triage()
        elif op == "C":
            sistema.ver_pacientes()
        elif op == "0":
            break
        else:
            print(" OPCIÓN INVÁLIDA.")
        input("\n  PRESIONE ENTER PARA CONTINUAR...")


def menu_turnos(sistema: SistemaUrgencias):
    while True:
        titulo("MENÚ - TURNOS")
        print("  A) VER COLA DE TURNOS")
        print("  B) ATENDER AL SIGUIENTE PACIENTE")
        print("  C) FINALIZAR ATENCIÓN DE UN PACIENTE")
        print("  0) RETORNAR")
        op = input("\n  SELECCIONA UNA OPCIÓN: ").strip().upper()
        if op == "A":
            sistema.ver_cola_turnos()
        elif op == "B":
            sistema.atender_siguiente()
        elif op == "C":
            sistema.finalizar_atencion()
        elif op == "0":
            break
        else:
            print(" OPCIÓN INVÁLIDA.")
        input("\n  PRESIONE ENTER PARA CONTINUAR...")

# FUNCIÓN PRINCIPAL PARA INICIAR EL SISTEMA DE GESTIÓN DE URGENCIAS
def main():
    sistema = SistemaUrgencias()
    print("\n" + "╔" + "═"*58 + "╗")
    print("║" + "  SISTEMA DE GESTIÓN DE URGENCIAS".center(58) + "║")
    print("║" + "  HOSPITAL DEL TUNAL - BOGOTÁ".center(58) + "║")
    print("║" + "  CON EL APOYO DE: UNIVERSIDAD CATÓLICA DE COLOMBIA".center(58) + "║")
    print("╚" + "═"*58 + "╝")
    n_doctores = 0
    while True:
        try:
            n_doctores = int(input("\n  ¿CUÁNTOS DOCTORES HAY DISPONIBLES? "))
            if n_doctores < 0:
                raise ValueError
            break
        except ValueError:
            print("  INGRESE UN NÚMERO DE DOCTORES VÁLIDO.")

    if n_doctores > 0:
        print(f"\n REGISTRO DE LOS {n_doctores} DOCTOR(ES) DISPONIBLES.\n")
        for i in range(1, n_doctores + 1):
            print(f"\n  - DOCTOR {i} DE {n_doctores}:")
            sistema.agregar_doctor()

    while True:
        titulo("--- MENÚ PRINCIPAL ---")
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
            input("\n  PRESIONE ENTER PARA CONTINUAR ...")
        elif op == "0":
            print("\n  EL SISTEMA HA SIDO CERRADO!\n")
            break
        else:
            print("  OPCIÓN INVÁLIDA.")


if __name__ == "__main__":
    main()

# RÚBRICA: 
# EN QUE ME BASE PARA LAS DISTRIBUCIONES  
# QUE MEJORAS TUVIMOS 
# VARIABLES