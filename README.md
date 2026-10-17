# EcoReporte_Grupo04

EcoReporte Comunitario

#### Descripción:

EcoReporte Comunitario es un proyecto de proyección social orientado al desarrollo de una aplicación web para registrar,
organizar, consultar y dar seguimiento a problemáticas ambientales identificadas en una comunidad.
Actualmente, situaciones como la proliferación de botaderos de basura a cielo abierto, el vertido clandestino
de aguas residuales o contaminantes, la quema de desechos a cielo abierto y la tala no autorizada de árboles se
gestionan de forma fragmentada o quedan invisibilizadas por la falta de un canal directo entre los ciudadanos y
los dirigentes responsables; nuestra meta será reducir estas carencias.

## Integrantes

- Cristopher David Salmeron Tejada (tejadacristopher20-a11y)
- Oscar Javier Portillo Tejada (oscarportillo707-ccpt)
- William Javier Chacon Calderon (cc0470032026-dev)
- Diego Alexander Hernández Núñez (Diego-Hernandez-qw)
- Brandon Edenilson Alas Tobias (brandonalas074-maker)

## Proyecto

EcoReporte Comunitario.

## Estado de Proyecto

Fase 4: Desarrollo de la aplicación en Django con SQL Server (aplicación funcional).

| Fase   | Descripción                                                               | Estado     |
| ------ | ------------------------------------------------------------------------- | ---------- |
| Fase 1 | Organización y selección del proyecto                                     | Finalizada |
| Fase 2 | Diagnóstico de la problemática y definición de requisitos                 | Finalizada |
| Fase 3 | Diseño de clases y modelado de la base de datos                           | Finalizada |
| Fase 4 | Creación del proyecto en Django, configuración de SQL Server y desarrollo | En curso   |

## ¿En qué consiste el problema?

El problema consiste en la falta de un registro organizado de los problemas ambientales que ocurren en la comunidad.
Situaciones como la acumulación de basura, los botaderos clandestinos, la contaminación de ríos y quebradas, la quema
de desechos y el deterioro de zonas verdes pueden presentarse sin que exista una herramienta que permita registrarlas,
clasificarlas y darles seguimiento de manera ordenada.

## Identificación General de los Beneficiarios

Los principales beneficiarios serán los residentes de la zona y de sus alrededores, comercios y centros educativos, ya que nos empeñaremos en
encontrar la manera de solucionar las diversas problemáticas ambientales presentes en la comunidad. A través de la encuesta
realizada pudimos evidenciar la falta de un sistema tecnológico que nos permita llevar un registro y hacer una mejora en el entorno ambiental y educativo, por lo que nos esforzaremos por atender la problemática de la Comunidad Las Toreras, distrito de San Ignacio, departamento de Chalatenango.

También se benefician las alcaldías y organizaciones ambientales, que contarán con un registro ordenado de los casos para atenderlos.

---

Fase 2: Diagnóstico de la problemática y definición de requisitos

## Lista de Requisitos Funcionales:

- RF01 — Registrar usuarios
- RF02 — Registrar reportes ambientales
- RF03 — Clasificar reportes
- RF04 — Registrar ubicación
- RF05 — Registrar evidencia
- RF06 — Consultar reportes
- RF07 — Modificar reportes
- RF08 — Eliminar reportes
- RF09 — Actualizar estado
- RF10 — Registrar seguimiento
- RF11 — Filtrar reportes

## Lista de Requisitos No Funcionales:

- RNF01 — La aplicación deberá contar con una interfaz que pueda visualizarse correctamente en computadoras, tablets y dispositivos móviles.
- RNF02 — El sistema deberá validar los datos ingresados en los formularios antes de almacenarlos.
- RNF03 — El sistema deberá utilizar SQL Server para almacenar la información de la aplicación.
- RNF04 — El sistema deberá ser desarrollado utilizando Django, Python y HTML.
- RNF05 — El sistema deberá evitar exponer información personal innecesaria de los usuarios.
- RNF06 — La interfaz deberá presentar la información de manera clara y organizada para facilitar su utilización.

---

Fase 3: Diseño de clases y modelado de la Base de Datos

## Entidades del sistema (12)

El sistema se organiza en **4 aplicaciones de Django** y **12 entidades**, cada una con su tabla en SQL Server.

| App                | Entidad               | Descripción                                                                                                                              |
| ------------------ | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `appusuarios`      | **Usuario**           | Persona que utiliza el sistema. Según su rol puede ser Ciudadano, Responsable institucional o Administrador.                             |
| `appterritorio`    | **Departamento**      | Departamento del país (Chalatenango).                                                                                                    |
| `appterritorio`    | **Distrito**          | Distrito dentro de un departamento (San Ignacio).                                                                                        |
| `appterritorio`    | **Comunidad**         | Comunidad dentro de un distrito (Las Toreras).                                                                                           |
| `appterritorio`    | **Ubicacion**         | Lugar exacto del problema: referencia, dirección y coordenadas opcionales.                                                               |
| `appreportes`      | **CategoriaProblema** | Tipo de problema: acumulación de basura, botadero clandestino, contaminación de río o quebrada, quema de desechos, daño en zonas verdes. |
| `appreportes`      | **ReporteAmbiental**  | Entidad central: título, descripción, fecha, nivel de gravedad y estado del problema reportado.                                          |
| `appreportes`      | **Evidencia**         | Fotografías que documentan un reporte.                                                                                                   |
| `appreportes`      | **Seguimiento**       | Acciones realizadas para atender un reporte (inspección, limpieza, etc.).                                                                |
| `appreportes`      | **HistorialEstado**   | Registro automático de cada cambio de estado: estado anterior, estado nuevo, quién y cuándo.                                             |
| `appinstituciones` | **Institucion**       | Alcaldías, instituciones de gobierno, ONG o centros educativos que atienden los casos.                                                   |
| `appinstituciones` | **AsignacionReporte** | Asignación de un reporte a la institución que debe atenderlo.                                                                            |

### Relaciones principales

- Un **Usuario** registra muchos **Reportes** (asociación 1:N).
- Una **CategoriaProblema** agrupa muchos **Reportes** (agregación: no se puede eliminar una categoría que tenga reportes).
- **Departamento → Distrito → Comunidad → Ubicacion → Reporte** (cada nivel 1:N).
- Un **Reporte** contiene muchas **Evidencias**, **Seguimientos** y registros de **HistorialEstado** (composición: si se elimina el reporte, se eliminan con él).
- Una **Institucion** recibe muchas **Asignaciones**; un **Usuario** Responsable pertenece a una Institución.

### Estados y niveles de gravedad

- **Nivel de gravedad:** Bajo, Medio, Alto.
- **Estado:** Pendiente → En proceso → Resuelto (un caso resuelto puede reabrirse a En proceso).
- No se permite pasar de Pendiente a Resuelto directamente, y para marcar un reporte como Resuelto debe tener al menos un seguimiento registrado.

## Aplicación de la Programación Orientada a Objetos

| Concepto                             | Aplicación en el proyecto                                                                                                                                                                                                                                       |
| ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Clases y objetos**                 | Cada entidad es una clase de Python (modelo de Django); cada reporte registrado es un objeto de `ReporteAmbiental`.                                                                                                                                             |
| **Herencia**                         | `Usuario` hereda de `AbstractUser` de Django (inicio de sesión y contraseñas cifradas). Todas las entidades heredan de la clase abstracta `ModeloBase` (fechas de creación y actualización). `Ciudadano`, `Responsable` y `Administrador` heredan de `Usuario`. |
| **Polimorfismo**                     | `Ciudadano`, `Responsable` y `Administrador` responden de forma distinta a los mismos métodos: `obtener_permisos()`, `reportes_de_panel()` y `titulo_panel()`. Una sola pantalla, "Mi panel", muestra a cada rol los reportes que le corresponden.              |
| **Encapsulamiento**                  | El estado de un reporte solo puede cambiarse con `cambiar_estado()`, que valida la transición y el permiso del usuario y registra el cambio en `HistorialEstado`. Si se intenta modificar el estado directamente, el sistema lo rechaza.                        |
| **Abstracción**                      | Las vistas solo preguntan al reporte qué se puede hacer (`puede_modificar()`, `puede_gestionar()`, `es_critico()`, `marcar_como_resuelto()`), sin conocer los detalles internos.                                                                                |
| **Herencia en vistas y formularios** | Las acciones sobre un reporte (cambiar estado, registrar seguimiento, asignar, agregar foto) heredan de la clase base `AccionSobreReporteView`. Todos los formularios heredan el estilo visual de `EstiloBootstrapMixin`.                                       |

---

Fase 4: Desarrollo de la aplicación

## Tecnologías utilizadas

- Python 3.13
- Django 6.1
- SQL Server (conexión con `mssql-django` y ODBC Driver 17/18 for SQL Server)
- HTML y Bootstrap 5 (diseño adaptable a computadoras, tablets y celulares)
- Pillow (manejo de fotografías)

## Tipos de usuario

| Usuario                       | Qué puede hacer                                                                                                                           |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **Visitante** (sin cuenta)    | Ver la página de inicio, la lista de reportes con filtros y el detalle de cada reporte.                                                   |
| **Ciudadano**                 | Registrarse con su correo, crear reportes con ubicación y fotografía, y editar o eliminar sus propios reportes mientras estén pendientes. |
| **Responsable institucional** | Atender los casos asignados a su institución: cambiar el estado, registrar seguimientos y agregar fotografías.                            |
| **Administrador**             | Asignar reportes a instituciones, gestionar cualquier reporte y administrar usuarios, instituciones y catálogos desde `/admin/`.          |

En las páginas públicas no se muestran el nombre, el correo ni el teléfono de quien reporta (RNF05).

## Funcionalidades implementadas

- Registro e inicio de sesión con correo y contraseña (RF01).
- Registro de reportes con categoría, gravedad, ubicación, fecha, descripción y fotografía (RF02, RF03, RF04, RF05).
- Consulta pública de reportes y de su detalle (RF06).
- Edición y eliminación de reportes según permisos (RF07, RF08).
- Cambio de estado con historial automático (RF09).
- Registro de acciones de seguimiento (RF10).
- Filtros por texto, categoría, estado, gravedad y comunidad (RF11).
- Asignación de reportes a instituciones.
- Panel personal según el rol del usuario.
- Datos iniciales cargados automáticamente: Chalatenango, San Ignacio, Las Toreras y las 5 categorías de problema.

## Estructura del proyecto

```
EcoReporteGrupo04/
├── Documentacion_EcoReporte/      Diagramas de clases y de base de datos
├── requirements.txt               Dependencias del proyecto
└── Eco_Reporte_Comunitario/
    ├── manage.py
    ├── .env.example               Plantilla de configuración local
    ├── Eco_Reporte_Comunitario/   Configuración (settings, urls, ModeloBase)
    ├── appusuarios/               Usuarios, roles, registro e inicio de sesión
    ├── appterritorio/             Departamento, distrito, comunidad y ubicación
    ├── appreportes/               Reportes, evidencias, seguimiento e historial
    ├── appinstituciones/          Instituciones y asignaciones
    ├── templates/                 Plantillas HTML compartidas
    └── static/                    Estilos CSS
```

## Instrucciones básicas para instalar y ejecutar la aplicación

**Requisitos:** Python 3.13, SQL Server, SQL Server Management Studio y ODBC Driver 17 o 18 for SQL Server.

1. Clonar el repositorio:

   ```powershell
   git clone https://github.com/tejadacristopher20-a11y/EcoReporteGrupo04.git
   cd EcoReporteGrupo04
   ```

2. Crear y activar el entorno virtual, e instalar las dependencias:

   ```powershell
   python -m venv Eco_Reporte
   .\Eco_Reporte\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

   Si PowerShell indica que la ejecución de scripts está deshabilitada, ejecutar primero
   `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y volver a activar el entorno.

3. Crear la base de datos vacía `EcoReporteComunitario` en SQL Server Management Studio
   (clic derecho en **Databases** → **New Database...**).

4. Configurar las variables locales. Copiar `Eco_Reporte_Comunitario/.env.example` como `Eco_Reporte_Comunitario/.env` y completar los datos:
   - `SECRET_KEY`: generar una propia con
     `python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"`
   - `DB_HOST`: `localhost` (o el nombre de la instancia, por ejemplo `localhost\SQLEXPRESS`).
   - `DB_DRIVER`: `ODBC Driver 17 for SQL Server` u `ODBC Driver 18 for SQL Server`.
   - `DB_USER` y `DB_PASSWORD`: dejar vacíos si se usa autenticación de Windows.

   El archivo `.env` no se sube a GitHub porque contiene datos privados.

5. Crear las tablas y el usuario administrador:

   ```powershell
   cd Eco_Reporte_Comunitario
   python manage.py migrate
   python manage.py createsuperuser
   ```

   `migrate` crea las tablas en SQL Server y carga los datos iniciales (Chalatenango, San Ignacio, Las Toreras y las categorías de problema).

6. Iniciar el servidor:

   ```powershell
   python manage.py runserver
   ```

   Abrir http://127.0.0.1:8000/ (aplicación) o http://127.0.0.1:8000/admin/ (administración).
   La terminal debe quedar abierta mientras se usa la aplicación.

7. (Opcional) Ejecutar las pruebas automáticas:

   ```powershell
   python manage.py test
   ```

**Para las siguientes veces** solo es necesario activar el entorno e iniciar el servidor:

```powershell
cd EcoReporteGrupo04\Eco_Reporte_Comunitario
..\Eco_Reporte\Scripts\Activate.ps1
python manage.py runserver
```

## Flujo de atención de un caso

1. El **ciudadano** se registra y reporta un problema con su fotografía. El reporte queda **Pendiente**.
2. El **administrador** revisa el reporte y lo asigna a la institución correspondiente.
3. El **responsable** de esa institución lo pasa a **En proceso** y registra las acciones de seguimiento.
4. Cuando el problema se soluciona, el responsable lo marca como **Resuelto**.
5. Cualquier persona puede consultar el estado y el historial del caso.
