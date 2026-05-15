<div align="center">

# SIGU - HOSPITAL DEL TUNAL, BOGOTÁ
## SISTEMA INTELIGENTE DE GESTIÓN DE URGENCIAS

</div>
<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

**SISTEMA WEB DE ASIGNACIÓN ÓPTIMA DE TURNOS Y CLASIFICACIÓN DE PACIENTES POR TRIAGE**
para el servicio de urgencias del Hospital del Tunal, Bogotá.

[Descripción](#-descripción) · [Arquitectura](#-arquitectura) · [Instalación](#-instalación) · [Uso](#-uso-del-sistema) · [API](#-referencia-de-la-api-rest) · [Estructura](#-estructura-del-proyecto)

</div>

---

## 📋 DESCRIPCIÓN

El **Sistema de Gestión de Urgencias** es una aplicación web diseñada para el Hospital del Tunal (Nivel III, localidad de Tunjuelito), cuyo objetivo principal es **minimizar el tiempo de espera** entre la llegada del paciente y su atención por un profesional de salud, mediante la asignación óptima de turnos basada en prioridad médica.

El sistema implementa el **protocolo de Triage de Manchester** en 5 niveles de criticidad, utilizando una cola de prioridad tipo *min-heap* para garantizar que siempre sea atendido primero el paciente con mayor urgencia médica, independientemente de su hora de llegada.

> **ALCANCE:** Solo cubre URGENCIAS clasificadas por TRIAGE. NO INCLUYE consultas generales, citas médicas programadas ni hospitalización.

---

## ✨ FUNCIONALIDADES

| MÓDULO | DESCRIPCIÓN |
|---|---|
| 🔐 **AUTENTICACIÓN** | Pantalla de inicio de sesión con validación de credenciales contra el servidor |
| 📊 **DASHBOARD** | Panel en tiempo real con estadísticas del servicio y vista rápida de cola y atención activa |
| 👨‍⚕️ **GESTIÓN DE DOCTORES** | Registro, visualización y eliminación del personal médico con control de disponibilidad |
| 📋 **REGISTRO DE PACIENTES** | Ingreso completo de datos del paciente con validación de cédula única |
| 🩺 **ASIGNACIÓN DE TRIAGE** | Clasificación por tipo de emergencia con vista previa del nivel y tiempo estimado |
| 👥 **VISUALIZACIÓN DE PACIENTES** | Listado filtrable por estado: en espera, registrados y finalizados |
| ⏳ **COLA DE TURNOS** | Vista ordenada por prioridad con barra de espera acumulada estimada |
| 🔔 **ATENCIÓN ACTIVA** | Control de pacientes en atención con asignación de doctor y cierre de turno |

---

## 🏗 ARQUITECTURA

El proyecto está organizado en **TRES CAPAS** que se comunican a través de una API REST:

```
┌─────────────────────────────────────────────────────────┐
│  CAPA 3 — INTERFAZ WEB (HTML · CSS · JavaScript)        │
│  login.html / index.html + main.css / login.css         │
│  app.js / login.js                                      │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP / JSON
┌────────────────────────▼────────────────────────────────┐
│  CAPA 2 — API REST (Flask · Python)                     │
│  app.py                                                 │
│  Endpoints JSON · Manejo de sesión · Renderizado Jinja2 │
└────────────────────────┬────────────────────────────────┘
                         │ Importación directa
┌────────────────────────▼────────────────────────────────┐
│  CAPA 1 — LÓGICA DE SIGU (Python puro)                  │
│  proyecto_salud.py                                      │
│  Clases · Algoritmo de cola · Sin dependencias web      │
└─────────────────────────────────────────────────────────┘
```

### ALGORITMO CENTRAL — COLA DE PRIORIDAD (MIN-HEAP)

La asignación de turnos utiliza el módulo `heapq` de Python. Cada paciente es comparable mediante el método `__lt__` que evalúa la tupla `(nivel_triage, hora_registro)`:

- **MENOR NIVEL DE TRIAGE** → Mayor urgencia → Primero en el heap.
- A **IGUAL NIVEL DE TRIAGE**, se atiende al que llegó antes (`hora_registro`).
- Al llamar `atender_siguiente`, se extrae el paciente con `heapq.heappop()` en **O(log n)**.

```python
# PRIORIDAD: (nivel_triage, hora_registro)
# NIVEL 1 (Rojo) siempre sale antes que NIVEL 5 (Azul)
self._prioridad = (self.nivel_triage, self.hora_registro)

def __lt__(self, other):
    return self._prioridad < other._prioridad
```

---

## 🩺 CLASIFICACIÓN DE TRIAGE

El sistema implementa los **5 NIVELES del TRIAGE de MANCHESTER**, cada uno con sus tipos de emergencia, tiempo de atención estimado y código de color:

| NIVEL | COLOR | CLASIFICACIÓN  | EMERGENCIAS INCLUIDAS | TIEMPO DE ESPERA |
|:---:|:---:|---|---|:---:|
| **I** | 🔴 ROJO | RESUCITACIÓN | Paro cardiorrespiratorio, Politraumatismo grave | Inmediato |
| **II** | 🟠 NARANJA | EMERGENCIA | Dificultad respiratoria severa, ACV / Derrame cerebral | < 10 min |
| **III** | 🟡 AMARILLO | URGENTE | Fractura con compromiso vascular, Dolor abdominal agudo | < 30 min |
| **IV** | 🟢 VERDE | MENOS URGENTE | Fiebre alta con convulsión, Herida con sangrado moderado | < 2 horas |
| **V** | 🔵 AZUL | NO URGENTE | Dolor leve / Malestar general, Consulta menor (gripe, tos) | < 4 horas |

---

## 📁 ESTRUCTURA DEL PROYECTO

```
hospital/
│
├── app.py                      # SERVIDOR FLASK — API REST y Rutas
├── proyecto_salud.py           # Lógica (Clases y Algoritmo)
├── README.md                   
│
├── templates/
│   ├── login.html              # Pantalla de Inicio de Sesión (Administrador)
│   └── index.html              # Aplicación principal (SIGU)
│
└── static/
    ├── css/
    │   ├── main.css            # Estilos del sistema (variables, componentes)
    │   └── login.css           # Estilos de la pantalla de login
    └── js/
        ├── app.js              # Lógica del sistema (API, Renderizado)
        └── login.js            # Lógica del formulario de autenticación
```

### Descripción de archivos clave

| ARCHIVO | RESPONSABILIDAD |
|---|---|
| `proyecto_salud.py` | Define las clases `Paciente`, `Doctor`, `SistemaUrgencias`. Contiene el algoritmo de cola, los 10 tipos de emergencia y los enums de estado. Sin dependencias externas. |
| `app.py` | Instancia Flask, importa la lógica, expone 11 endpoints REST y gestiona la sesión del usuario. Nunca modifica `proyecto_salud.py`. |
| `main.css` | Variables CSS globales, sistema de grid, sidebar, topbar, tarjetas, tablas, badges, botones y responsive. |
| `login.css` | Layout dividido (imagen + formulario), animaciones `shake` y `fadeOut`, responsive mobile. |
| `app.js` | Toda la interacción del dashboard: navegación SPA, llamadas a la API, renderizado dinámico de tablas y estadísticas, reloj, toast. |
| `login.js` | Validación de campos, llamada `POST /login`, manejo de errores y redirección al dashboard. |

---

## ⚙️ INSTALACIÓN

### Requisitos previos

- Python **3.10** o superior
- pip (gestor de paquetes de Python)

### Pasos

**1. Clonar o descargar el repositorio**

```bash
git clone https://github.com/tu-usuario/hospital-tunal-urgencias.git
cd hospital-tunal-urgencias
```

**2. Crear y activar un entorno virtual** *(recomendado)*

```bash
# Crear entorno virtual
python -m venv venv

# Activar en Windows
venv\Scripts\activate

# Activar en macOS / Linux
source venv/bin/activate
```

**3. Instalar dependencias**

```bash
pip install flask
```

> El resto del proyecto usa únicamente la biblioteca estándar de Python (`heapq`, `datetime`, `enum`).

**4. Verificar la estructura de archivos**

Asegúrate de que la carpeta tenga exactamente esta disposición antes de ejecutar:

```
hospital/
├── app.py
├── proyecto_salud.py
├── templates/
│   ├── login.html
│   └── index.html
└── static/
    ├── css/
    │   ├── main.css
    │   └── login.css
    └── js/
        ├── app.js
        └── login.js
```

**5. Ejecutar el servidor**

```bash
python app.py
```

**6. Abrir en el navegador**

```
http://127.0.0.1:5000
```

EL SISTEMA REDIRIGIRÁ AUTOMATICAMENTE A LA API REST DE SIGU. 

---

## 🔐 CREDENCIALES DE ACCESO

| CAMPO | VALOR |
|---|---|
| **Usuario** | `ADMINISTRADOR` |
| **Contraseña** | `HospitalTunal` |

> Las credenciales se validan en el servidor (`app.py`). Una sesión Flask protege el acceso a `/dashboard` y a todos los endpoints de la API, quien no esté autenticado es redirigido al login automáticamente.

---

## 🚀 USO DEL SISTEMA

El flujo normal de operación sigue estos pasos:

```
1. Iniciar sesión
       ↓
2. Registrar doctores disponibles en el turno
       ↓
3. Registrar paciente (datos personales)
       ↓
4. Asignar triage al paciente (seleccionar tipo de emergencia)
       → El sistema le asigna automáticamente un número de turno
       → El paciente entra a la cola ordenada por prioridad
       ↓
5. Atender siguiente (desde Dashboard o Cola de Turnos)
       → El sistema asigna el paciente al doctor disponible
       ↓
6. Finalizar atención
       → El doctor queda libre para el siguiente paciente
```

### FLUJO DE ESTADOS DE UN PACIENTE 

```
REGISTRADO  ──(CUANDO SE ASIGNA TRIAGE)──►  EN_ESPERA  ──(DOCTOR DISPONIBLE)──►  EN_ATENCIÓN  ──(TERMINAR ATENCIÓN)──►  FINALIZADO
```

---

## 🔌 REFERENCIA DE LA API REST

Todos los endpoints devuelven `Content-Type: application/json`.

### AUTENTICACIÓN

| MÉTODO | RUTA | DESCRIPCIÓN | BODY |
|---|---|---|---|
| `GET` | `/login` | Renderiza la pantalla de login | — |
| `POST` | `/login` | Valida credenciales y abre sesión | `{ "usuario": "...", "password": "..." }` |
| `GET` | `/logout` | Cierra la sesión activa | — |
| `GET` | `/dashboard` | Renderiza la aplicación principal | — |

### DOCTORES

| MÉTODO | RUTA | DESCRIPCIÓN | BODY |
|---|---|---|---|
| `GET` | `/api/doctores` | Lista todos los doctores | — |
| `POST` | `/api/doctores/agregar` | Registra un nuevo doctor | `{ "id", "nombre", "especialidad" }` |
| `POST` | `/api/doctores/eliminar` | Elimina un doctor disponible | `{ "id" }` |

### PACIENTES

| Método | Ruta | Descripción | Body |
|---|---|---|---|
| `GET` | `/api/pacientes` | Devuelve todos los pacientes agrupados por estado | — |
| `POST` | `/api/pacientes/registrar` | Registra un nuevo paciente | `{ "nombre", "cedula", "telefono", "sexo", "eps", "fecha_nacimiento", "telefono_emergencia" }` |
| `POST` | `/api/pacientes/triage` | Asigna triage y turno a un paciente registrado | `{ "cedula", "tipo_emergencia" }` |

### Turnos y cola

| Método | Ruta | Descripción | Body |
|---|---|---|---|
| `GET` | `/api/cola` | Retorna la cola ordenada con espera acumulada | — |
| `POST` | `/api/turnos/atender` | Extrae al paciente más prioritario y lo asigna a un doctor | `{}` |
| `POST` | `/api/turnos/finalizar` | Finaliza la atención y libera al doctor | `{ "cedula" }` |

### Estadísticas

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/estadisticas` | Devuelve conteos del sistema en tiempo real |

#### Ejemplo de respuesta — `/api/estadisticas`

```json
{
  "total": 12,
  "registrados": 2,
  "en_espera": 5,
  "en_atencion": 3,
  "finalizados": 2,
  "docs_disp": 1,
  "docs_turno": 2,
  "tiempo_cola": 145
}
```

#### Ejemplo de respuesta — `/api/cola`

```json
[
  {
    "nombre": "Ana Torres",
    "cedula": "1020304050",
    "nivel_triage": 1,
    "tipo_emergencia": "Paro cardiorrespiratorio",
    "tiempo_atencion": 60,
    "numero_turno": 3,
    "espera_acumulada": 0
  },
  {
    "nombre": "Carlos Roa",
    "cedula": "9988776655",
    "nivel_triage": 2,
    "tipo_emergencia": "ACV / Derrame cerebral",
    "tiempo_atencion": 50,
    "numero_turno": 1,
    "espera_acumulada": 60
  }
]
```

---

## 🧩 MODELO DE DATOS

### Clase `Paciente`

| Atributo | Tipo | Descripción |
|---|---|---|
| `nombre` | `str` | Nombre completo |
| `cedula` | `str` | Número de documento (único) |
| `telefono` | `str` | Teléfono de contacto |
| `sexo` | `str` | `M` / `F` |
| `eps` | `str` | Entidad promotora de salud |
| `fecha_nacimiento` | `str` | Fecha en formato `YYYY-MM-DD` |
| `telefono_emergencia` | `str` | Contacto de emergencia |
| `estado` | `EstadoPaciente` | `REGISTRADO` / `EN_ESPERA` / `EN_ATENCION` / `FINALIZADO` |
| `nivel_triage` | `int` | 1 al 5 (asignado al hacer triage) |
| `tipo_emergencia` | `str` | Nombre del tipo de emergencia |
| `tiempo_atencion` | `int` | Minutos estimados de atención |
| `numero_turno` | `int` | Asignado secuencialmente al hacer triage |
| `hora_registro` | `datetime` | Timestamp de creación |

### Clase `Doctor`

| Atributo | Tipo | Descripción |
|---|---|---|
| `doctor_id` | `str` | Identificador único (ej: `MED001`) |
| `nombre` | `str` | Nombre completo |
| `especialidad` | `str` | Área médica |
| `estado` | `EstadoDoctor` | `DISPONIBLE` / `EN_TURNO` |
| `paciente_actual` | `Paciente \| None` | Paciente que está atendiendo |

---

## 🖥 INTERFAZ DE USUARIO

La interfaz es una **Single Page Application (SPA)** que no recarga la página al navegar. Toda la comunicación con el servidor se realiza mediante `fetch()` asíncrono.

**Componentes visuales:**

- **Sidebar fijo** con navegación por secciones
- **Topbar** con título dinámico, reloj en tiempo real y botón de actualización manual
- **Tarjetas de estadísticas** con valores en tiempo real
- **Tablas dinámicas** con estados vacíos informativos
- **Badges de triage** con código de color por nivel
- **Barras de espera acumulada** en la cola de turnos
- **Toast de notificaciones** para confirmaciones y errores
- **Vista previa de triage** al seleccionar el tipo de emergencia
- **Auto-refresh** cada 15 segundos en la sección activa

**Paleta de colores del sistema:**

| Variable | Color | Uso |
|---|---|---|
| `--bg` | `#0d1117` | Fondo principal |
| `--bg2` | `#161b22` | Sidebar y tarjetas |
| `--bg3` | `#1c2333` | Cabeceras y fondos de input |
| `--accent2` | `#388bfd` | Elementos activos y foco |
| `--t1` | `#f85149` | Triage I — Rojo |
| `--t2` | `#e8914a` | Triage II — Naranja |
| `--t3` | `#d29922` | Triage III — Amarillo |
| `--t4` | `#3fb950` | Triage IV — Verde |
| `--t5` | `#58a6ff` | Triage V — Azul |

---

## 🔒 SEGURIDAD Y CONSIDERACIONES

- La autenticación usa **Flask sessions** con `secret_key`. Para producción se recomienda configurar la clave desde variables de entorno.
- Todos los endpoints del dashboard están protegidos: sin sesión activa, Flask redirige al login.
- El sistema **no usa base de datos** — los datos viven en memoria mientras el servidor esté activo. Al reiniciar `app.py`, el estado se reinicia.
- Para un entorno de producción real se recomienda agregar persistencia (SQLite / PostgreSQL) y usar un servidor WSGI como **Gunicorn**.

---

## 🛠 MEJORAS FUTURAS

- [ ] Persistencia de datos con base de datos (SQLAlchemy + PostgreSQL)
- [ ] Historial de atenciones por paciente y doctor
- [ ] Autenticación por roles (administrador, enfermera, médico)
- [ ] Notificaciones en tiempo real con WebSockets
- [ ] Reportes y exportación a PDF / Excel
- [ ] Módulo de citas programadas complementario al servicio de urgencias
- [ ] Integración con sistema de EPS para verificación automática
- [ ] Despliegue en contenedor Docker

---

## 👥 AUTORES

Desarrollado como proyecto académico para la asignatura de **Estructuras de Datos y Algoritmos**, aplicado al contexto hospitalario del **Hospital del Tunal**, localidad de Tunjuelito, Bogotá D.C., Colombia.

---

## 📄 LICENCIA

Este proyecto es de uso académico e institucional. Todos los derechos reservados al equipo de desarrollo y al Hospital del Tunal.

---

<div align="center">
  <sub>🏥 Hospital del Tunal · Localidad de Tunjuelito · Bogotá, Colombia · Sistema de Urgencias 24h</sub>
</div>