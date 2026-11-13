# EcoReporte_Grupo04

EcoReporte Comunitario

#### Descripción:

EcoReporte Comunitario es un proyecto de proyección social orientado al desarrollo de una aplicación web para registrar,organizar, consultar y dar seguimiento a problemáticas ambientales identificadas en una comunidad.
Actualmente, situaciones como la proliferación de botaderos de basura a cielo abierto, el vertido clandestino
de aguas residuales o contaminantes, la quema de desechos a cielo abierto y la tala no autorizada de árboles se
gestionan de forma fragmentada o quedan invisibilizadas por la falta de un canal directo entre los ciudadanos y
los dirigentes responsables. Estas problemáticas pueden ocasionar contaminación del suelo y del agua, deterioro
de las áreas verdes, malos olores y riesgos para la salud de los habitantes, afectando su calidad de vida y el entorno natural.
Ante esta situación, EcoReporte Comunitario busca ofrecer una alternativa tecnológica que permita a los usuarios registrar los
problemas ambientales mediante formularios que incluyan información como la categoría del incidente, su ubicación, fecha, descripción,
nivel de gravedad y fotografías como evidencia. De esta manera, se pretende contribuir a una gestión más organizada de las
problemáticas ambientales.

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
| Fase 4 | Creación del proyecto en Django, configuración de SQL Server y desarrollo | Finalizada |

## ¿En qué consiste el problema?

El problema consiste en la falta de un registro organizado de los problemas ambientales que ocurren en la comunidad.
Situaciones como la acumulación de basura, los botaderos clandestinos, la contaminación de ríos y quebradas, la quema
de desechos y el deterioro de zonas verdes pueden presentarse sin que exista una herramienta que permita registrarlas,
clasificarlas y darles seguimiento de manera ordenada.
Para solucionarlo, la plataforma implementará reportes geolocalizados con fotos y categorías para registrar
cada incidente.
Asimismo, permitirá ásignar estados de atención (Pendientes, en proceso, resuelto) para dar un seguimiento
transparente de los reportes.

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
- Una **Institucion** recibe muchas **Asignaciones**, y un **Reporte** tiene como máximo una asignación activa a la vez (al reasignarlo, la anterior queda inactiva en el historial).
- Cada **Usuario** Responsable pertenece obligatoriamente a una **Institucion**, y cada institución tiene **un único responsable**. El responsable atiende solo los reportes asignados a su institución.

### Estados y niveles de gravedad

- **Nivel de gravedad:** Bajo, Medio, Alto.
- **Estado:** Pendiente → En proceso → Resuelto (un caso resuelto puede reabrirse a En proceso).
- **Descartado:** un reporte Pendiente o En proceso puede descartarse si es falso, duplicado o está fuera de la comunidad. El motivo es obligatorio y un reporte descartado puede reabrirse a Pendiente.
- No se permite pasar de Pendiente a Resuelto directamente, y para marcar un reporte como Resuelto debe tener al menos un seguimiento registrado por el responsable (los aportes del ciudadano no cuentan).
- **Fecha del incidente:** no puede ser futura ni de hace **más de 5 años** (ver [Fecha del incidente](#fecha-del-incidente)).

## Aplicación de la Programación Orientada a Objetos

| Concepto                             | Aplicación en el proyecto                                                                                                                                                                                                                                       |
| ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Clases y objetos**                 | Cada entidad es una clase de Python (modelo de Django); cada reporte registrado es un objeto de `ReporteAmbiental`.                                                                                                                                             |
| **Herencia**                         | `Usuario` hereda de `AbstractUser` de Django (inicio de sesión y contraseñas cifradas). Todas las entidades heredan de la clase abstracta `ModeloBase` (fechas de creación y actualización). `Ciudadano`, `Responsable` y `Administrador` heredan de `Usuario`. |
| **Polimorfismo**                     | `Ciudadano`, `Responsable` y `Administrador` responden de forma distinta a los mismos métodos: `obtener_permisos()`, `reportes_de_panel()` y `titulo_panel()`. Una sola pantalla, "Mi panel", muestra a cada rol los reportes que le corresponden.              |
| **Encapsulamiento**                  | El estado de un reporte solo puede cambiarse con `cambiar_estado()`, que valida la transición y el permiso del usuario y registra el cambio en `HistorialEstado`. Si se intenta modificar el estado directamente, el sistema lo rechaza.                        |
| **Abstracción**                      | Las vistas solo preguntan al reporte qué se puede hacer (`puede_modificar()`, `puede_gestionar()`, `es_critico()`, `marcar_como_resuelto()`), sin conocer los detalles internos.                                                                                |
| **Herencia en vistas y formularios** | Las acciones sobre un reporte (cambiar estado, registrar seguimiento, asignar, tomar el caso, agregar foto) heredan de la clase base `AccionSobreReporteView`. Todos los formularios heredan el estilo visual de `EstiloBootstrapMixin`.                        |

---

Fase 4: Desarrollo de la aplicación

## Instrucciones basicas para instalación

### Creación del entorno virtual

| Paso | Descripción                                   | Comando                       |
| ---- | --------------------------------------------- | ----------------------------- |
| 1    | Crear un entorno virtual de Python            | py -m venv venv               |
| 2    | Activar el entorno                            | venv\Scripts\activate         |
| 3    | Instalar Django y las dependencias necesarias | pip install django            |
| 4    | Generar el archivo requirements.txt           | pip freeze > requirements.txt |

### Ejecución de la aplicación

| Paso | Descripción                                            | Comando                                                          |
| ---- | ------------------------------------------------------ | ---------------------------------------------------------------- |
| 1    | Crear el proyecto                                      | django-admin startproject EcoReporte                             |
| 2    | Iniciar el servidor local para probar las aplicaciones | py manage.py runserver                                           |
| 3    | Crear una nueva aplicación                             | python manage.py startapp nombre_app                             |
| 4    | Conectar Django con una base de datos SQL Server       | python -m pip install "mssql-django==1.8.0" pyodbc python-dotenv |

---

## Tecnologías utilizadas

- Python 3.13
- Django 6.1
- SQL Server (conexión con `mssql-django` y ODBC Driver 17/18 for SQL Server)
- HTML y Bootstrap 5 (diseño adaptable a computadoras, tablets y celulares)
- Pillow (manejo de fotografías)

  ## Herramientas de comunicación utilizadas.
  - WhatsApp
  - Meet
  - Gmail

## Tipos de usuario y permisos

El sistema funciona con un flujo de responsabilidades claro: **el ciudadano reporta, el administrador asigna cada caso a una institución (o el responsable de la institución lo toma), ese responsable le da seguimiento hasta resolverlo y el administrador mantiene el sistema funcionando**.

| Usuario                                             | Función                                                                                                                                                                                                                                                                                        |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Visitante** (sin cuenta)                          | Consulta la información pública: página de inicio, lista de reportes con filtros y detalle de cada reporte. Puede crear una cuenta de ciudadano.                                                                                                                                               |
| **Ciudadano**                                       | Reporta los problemas ambientales de su comunidad y da seguimiento a sus propios reportes.                                                                                                                                                                                                     |
| **Responsable institucional** (uno por institución) | Atiende los casos de **su institución** (alcaldía, MARN, ONG, centro educativo): toma los casos abiertos que nadie ha tomado, actualiza su estado, registra las acciones de seguimiento y sube fotografías del avance. Puede consultar los casos de otras instituciones, pero no modificarlos. |
| **Administrador** (único)                           | Mantiene el sistema: crea las instituciones y las cuentas de los responsables, **asigna y reasigna** los casos a las instituciones, administra categorías y comunidades, y elimina reportes falsos, duplicados o inapropiados. Puede atender cualquier caso si un responsable falta.           |

### Matriz de permisos

| Acción                                                     | Visitante |                     Ciudadano                      |        Responsable         |       Administrador       |
| ---------------------------------------------------------- | :-------: | :------------------------------------------------: | :------------------------: | :-----------------------: |
| Ver el inicio, la lista de reportes y su detalle           |    ✅     |                         ✅                         |             ✅             |            ✅             |
| Crear una cuenta desde la web                              |    ✅     |                         —                          |             —              |             —             |
| Crear reportes                                             |    ❌     |                         ✅                         |             ❌             |            ✅             |
| Editar su propio reporte                                   |    ❌     |        ✅ solo mientras está **Pendiente**         |             ❌             |   ✅ cualquier reporte    |
| Eliminar su propio reporte                                 |    ❌     |        ✅ solo mientras está **Pendiente**         |             ❌             |   ✅ cualquier reporte    |
| Editar o eliminar reportes de otras personas               |    ❌     |                         ❌                         |             ❌             |            ✅             |
| Agregar fotografías                                        |    ❌     | ✅ a sus reportes, si están Pendiente o En proceso | ✅ casos de su institución |  ✅ a cualquier reporte   |
| Agregar información adicional (aporte del ciudadano)       |    ❌     | ✅ a sus reportes, si están Pendiente o En proceso |             ❌             | ✅ a sus propios reportes |
| Asignar o reasignar un reporte a una institución           |    ❌     |                         ❌                         |             ❌             |     ✅ casos abiertos     |
| Tomar un caso abierto sin asignar, para su institución     |    ❌     |                         ❌                         |     ✅ casos abiertos      |             —             |
| Cambiar el estado (incluido Descartado, con motivo)        |    ❌     |                         ❌                         | ✅ casos de su institución |     ✅ cualquier caso     |
| Registrar acciones de seguimiento                          |    ❌     |                         ❌                         | ✅ casos de su institución |     ✅ cualquier caso     |
| Gestionar usuarios, instituciones y catálogos en `/admin/` |    ❌     |                         ❌                         |             ❌             |            ✅             |

En **"Mi panel"**, cada rol ve los reportes que le corresponden: el ciudadano ve **"Mis reportes"**, el responsable ve **"Casos de mi institución"** (los asignados a su institución y los casos abiertos que nadie ha tomado todavía) y el administrador ve **"Todos los reportes"**.

Los permisos se validan en el servidor, no solo ocultando botones: si un usuario intenta una acción que su rol nunca puede hacer (por ejemplo, escribiendo la dirección a mano), el sistema responde con una página de acceso denegado (403). Si su rol sí puede, pero el caso cambió mientras tenía la página abierta (por ejemplo, el administrador lo reasignó a otra institución), vuelve al detalle del reporte con un aviso que explica el motivo.

### Qué puede hacer el ciudadano con su propio reporte según su estado

| Estado del reporte        | Editar | Eliminar | Agregar fotografías | Agregar información adicional |
| ------------------------- | :----: | :------: | :-----------------: | :---------------------------: |
| **Pendiente**             |   ✅   |    ✅    |         ✅          |              ✅               |
| **En proceso**            |   ❌   |    ❌    |         ✅          |              ✅               |
| **Resuelto / Descartado** |   ❌   |    ❌    |         ❌          |              ❌               |

Una vez que el caso está **En proceso**, el ciudadano ya no puede modificar los datos originales para evitar inconsistencias con lo que la institución está atendiendo (por ejemplo, un cambio de ubicación). En su lugar, puede **agregar** fotografías e información adicional, que quedan registradas con su fecha como **"Aporte del ciudadano"** sin alterar lo reportado originalmente.

### Estados del reporte

- **Pendiente → En proceso → Resuelto.** Un caso resuelto puede reabrirse a En proceso.
- **Descartado:** el responsable de la institución asignada (o el administrador) puede descartar un reporte Pendiente o En proceso (falso, duplicado o fuera de la comunidad). El **motivo es obligatorio** y queda visible en el detalle. Un reporte descartado puede reabrirse a Pendiente.
- No se permite pasar de Pendiente a Resuelto directamente, y para marcar un caso como Resuelto debe existir al menos un seguimiento registrado por el responsable; los aportes del ciudadano no cuentan.
- Cada cambio de estado queda registrado automáticamente en el **historial**.
- Si el responsable y el administrador cambian el estado del mismo caso al mismo tiempo, **se guarda el primero**; el segundo vuelve al detalle con el aviso "otro usuario ya lo cambió…" y ve el estado actual.
- **Los reportes resueltos no se eliminan:** se conservan como evidencia de la atención brindada, para consultar el historial, reabrir el caso si el problema vuelve y obtener estadísticas. Solo el administrador elimina reportes, y únicamente en casos excepcionales (falsos, duplicados o inapropiados).

### Fecha del incidente

- La fecha del incidente puede ser de **hasta 5 años atrás** y **nunca futura**.
- Los 5 años se cuentan desde la **fecha en que se registró el reporte**, no desde hoy. Así, un reporte se puede seguir editando años después sin que la regla lo rechace.
- La regla se aplica en tres niveles que usan el mismo valor (`ANIOS_MAXIMOS_INCIDENTE = 5` en `restricciones.py`):
  - **Calendario del formulario:** solo deja elegir desde hace 5 años hasta hoy, y muestra la ayuda "Puede ser de hasta 5 años atrás".
  - **Validación en Python:** si la fecha es más antigua, el formulario muestra "La fecha del incidente no puede ser de hace más de 5 años" junto con la fecha más antigua permitida.
  - **Restricción CHECK en SQL Server** (`ck_reporte_fecha_antiguedad_maxima` y `ck_reporte_fecha_no_futura`): rechaza el dato aunque se guarde directamente con SQL, sin pasar por la aplicación.
- El 29 de febrero se calcula igual en Python y en SQL Server (pasa al 28 de febrero), por lo que el calendario y la base de datos siempre coinciden, también en años futuros (2030, 2040…).

### Administrador único

- El sistema permite **un solo administrador**. Si ya existe uno, no se puede crear ni asignar otro, ni desde `/admin/` ni con `createsuperuser`.
- Solo el administrador puede tener acceso al panel de administración (`/admin/`).
- En el panel, los registros se eliminan desde la ficha de cada uno (botón **"Eliminar"**); el borrado de varios registros a la vez está desactivado.

### Un responsable por institución

- **Todo responsable pertenece a una institución**, y **cada institución tiene un único responsable**. Si el administrador intenta dejar a un responsable sin institución o poner a dos responsables en la misma, el panel muestra el motivo y no guarda. SQL Server también lo impide (`ck_usuario_responsable_con_institucion` y `uq_usuario_un_responsable_por_institucion`).
- **Cada responsable atiende solo los casos asignados a su institución:** cambia su estado, registra seguimientos y sube fotografías del avance. Los casos de otras instituciones los puede consultar, pero ve el aviso "Este caso lo atiende…; solo su responsable puede actualizarlo".
- **Cómo llega un caso a una institución:**
  - El **administrador** lo asigna o lo reasigna a cualquier institución.
  - El **responsable** puede **tomar** un caso abierto que nadie ha tomado, con el botón **"Tomar este caso"** del detalle. Si dos responsables lo toman al mismo tiempo, **se queda el primero**; el segundo ve "No se pudo tomar el caso: ya lo atiende…".
- **Si el responsable se enferma o deja el puesto:** el administrador le cambia la institución o los datos en `/admin/`, o reasigna los casos. Los casos pertenecen a la institución, así que el nuevo responsable los recibe automáticamente.
- **No se puede eliminar una institución que tiene responsable:** primero se le cambia la institución al responsable.

### Creación de cuentas y contraseñas

| Usuario           | Cómo se crea la cuenta                                                                                                                                                                                                                                                                                                                                        |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Administrador** | Desde la terminal, una sola vez: `python manage.py createsuperuser`. Puede iniciar sesión con su nombre de usuario o con su correo.                                                                                                                                                                                                                           |
| **Responsable**   | Lo crea el administrador. Primero registra la institución en `/admin/` → Instituciones y luego, en `/admin/` → Usuarios → **Añadir usuario**, crea la cuenta con el rol **Responsable institucional**, **esa institución** (obligatoria; una institución no puede tener dos responsables) y una contraseña temporal que el responsable cambia en "Mi perfil". |
| **Ciudadano**     | Se registra por su cuenta en la página con la opción **"Registrarse"**. El formulario de registro siempre crea cuentas de ciudadano; nadie puede elegir otro rol desde ahí.                                                                                                                                                                                   |

**Requisitos al crear la cuenta de ciudadano:**

- **Teléfono obligatorio:** exactamente 8 números, solo dígitos y, si se desea, un único guion medio entre ellos (ejemplo: `7000-0000` o `70000000`).
- **Contraseña:** al menos 8 caracteres, **al menos un número** y **al menos un símbolo** (por ejemplo `- _ . @ # $ % & * !`); no puede ser completamente numérica, ni una contraseña común, ni parecerse a los datos personales del usuario.

Las contraseñas se guardan **cifradas** en SQL Server: ni siquiera el administrador puede verlas, solo restablecerlas.

En las páginas públicas no se muestran el nombre, el correo ni el teléfono de quien reporta (RNF05).

## Funcionalidades implementadas

- Registro e inicio de sesión con correo y contraseña (RF01).
- Registro de reportes con categoría, gravedad, ubicación, fecha, descripción y fotografía (RF02, RF03, RF04, RF05).
- Consulta pública de reportes y de su detalle (RF06).
- Edición y eliminación de reportes según permisos (RF07, RF08).
- Cambio de estado con historial automático (RF09).
- Registro de acciones de seguimiento (RF10).
- Filtros por texto, categoría, estado, gravedad y comunidad (RF11).
- Asignación de reportes a instituciones por el administrador, y opción para que el responsable tome un caso sin asignar para su institución.
- Un responsable por institución: cada uno atiende solo los casos de su institución.
- Fecha del incidente de hasta 5 años atrás, nunca futura.
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
2. El caso se asigna a la institución que debe atenderlo (alcaldía, MARN, ONG o centro educativo): lo **asigna el administrador**, o el **responsable de esa institución lo toma** desde "Mi panel" con el botón **"Tomar este caso"**.
3. Desde ese momento, **solo el responsable de esa institución** lo atiende. Si el reporte es falso o duplicado, lo marca como **Descartado** indicando el motivo. Cuando la institución empieza a trabajar, lo pasa a **En proceso** y registra las acciones de seguimiento.
4. Mientras el caso está abierto, el ciudadano puede agregar fotografías e información adicional a su reporte.
5. Cuando el problema se soluciona, el responsable lo marca como **Resuelto**. Si el problema vuelve, puede reabrir el caso.
6. Cualquier persona puede consultar el estado, la institución asignada y el historial del caso.

El **administrador** mantiene el sistema (instituciones, cuentas de responsables, categorías y comunidades), asigna o reasigna los casos cuando hace falta, puede atender cualquier caso si un responsable falta y elimina reportes solo en casos excepcionales.

## Documentación de datos de prueba

Luego de crear y entrar a: Abrir http://127.0.0.1:8000/ (aplicación) o http://127.0.0.1:8000/admin/ (administración).

Realizamos 3 registros de reportes necesarios para verificar la funcionalidad del codigo, los registros fueron:

- Basura Acumuladada
- Tala de Arboles a los alrededores
- Basura

En cada reporte se represento su :

- Categoria
- Descripción
- Fecha del incidente
- Fecha de reporte
- Ubicación

Ejemplos:

## Basura Acumuladada

| Categoria            | Descripción                                                        | Fecha incidente | Fecha reporte | Ubicación                                    |
| -------------------- | ------------------------------------------------------------------ | --------------- | ------------- | -------------------------------------------- |
| Botadero clandestino | Personas vistas tirando basura en lugares no apropiados para esto. | 20/10/2026      | 23/10/2026    | Parque Las Toreras, San Ignacio Chalatenango |

## Tala de Arboles a los alrededores

| Categoria            | Descripción                                             | Fecha incidente | Fecha reporte | Ubicación                                    |
| -------------------- | ------------------------------------------------------- | --------------- | ------------- | -------------------------------------------- |
| Daño en zonas verdes | Se evidencia una tala masiva de arboles en la comunidad | 21/10/2026      | 23/10/2026    | Parque Las Toreras, San Ignacio Chalatenango |

## Basura

| Categoria             | Descripción                                    | Fecha incidente | Fecha reporte | Ubicación                                      |
| --------------------- | ---------------------------------------------- | --------------- | ------------- | ---------------------------------------------- |
| Acumulación de basura | Acumulación de basura en lugares no permitidos | 05/10/2026      | 23/10/2026    | Escuela Las Toreras, San Ignacio, Chalatenango |

# Semana 6: Vistas, URLs, plantillas, interfaz gráfica, integración y pruebas

## Vistas de Django

Las vistas del proyecto se desarrollaron como vistas basadas en clases, aplicando los principios de la Programación Orientada a Objetos: herencia, polimorfismo y reutilización de código. Se encuentran en los archivos appreportes/views.py y appusuarios/views.py.

## Operaciones CRUD sobre la entidad principal (ReporteAmbiental)

- Consultar lista: ReporteListView (ListView) — muestra todos los reportes con filtros y paginación (RF06, RF11).
- Consultar detalle: ReporteDetailView (DetailView) — muestra un reporte con sus evidencias, seguimiento, historial y asignación.
- Registrar: ReporteCreateView (CreateView) — registra un reporte con su categoría, ubicación, gravedad y fotografía (RF02 a RF05).
- Modificar: ReporteUpdateView (UpdateView) — edita un reporte mientras está Pendiente (RF07).
- Eliminar: ReporteDeleteView (DeleteView) — elimina un reporte, previa confirmación (RF08).

## Vistas de gestión del reporte

Estas vistas heredan de una clase base propia, AccionSobreReporteView. Esa clase concentra el procedimiento común: buscar el reporte, validar el permiso, validar el formulario y mostrar el resultado. Cada vista hija solo define su permiso y la acción que ejecuta.

- AgregarEvidenciaView — agrega fotografías a un reporte (RF05).
- CambiarEstadoView — cambia el estado: Pendiente, En proceso, Resuelto o Descartado (RF09).
- RegistrarSeguimientoView — registra las acciones de seguimiento (RF10).
- AportarInformacionView — permite al ciudadano agregar información adicional a su reporte.
- AsignarReporteView — el administrador asigna o reasigna el reporte a una institución.
- TomarCasoView — el responsable toma un caso abierto sin asignar para su institución.

## Otras vistas

- InicioView — página principal con contadores por estado y los últimos reportes.
- PanelView — panel personal: cada rol ve los reportes que le corresponden (polimorfismo).
- RegistroView, IngresoView y SalidaView — registro, inicio y cierre de sesión (RF01).
- PerfilView y CambiarClaveView — modificación de los datos personales y de la contraseña.

## Control de acceso

Se implementaron dos mixins reutilizables:

- PermisoRequeridoMixin — exige iniciar sesión y que el rol tenga el permiso necesario.
- FiltroReportesMixin — aplica los filtros a cualquier lista de reportes.

Si un usuario intenta una acción no autorizada, el sistema responde con una página de acceso denegado (403). Las entidades de catálogo (Departamento, Distrito, Comunidad, Institución y CategoriaProblema) y los usuarios se gestionan con el panel de administración de Django (/admin/), que ofrece el CRUD completo y solo es accesible para el administrador del sistema.

## 2. Configuración de URLs

Las rutas se organizaron por aplicación. El archivo principal Eco_Reporte_Comunitario/urls.py incluye las rutas de cada app con include(). Cada ruta tiene un nombre descriptivo (name) y un espacio de nombres (app_name), de modo que las plantillas las llaman por su nombre y no escriben la dirección a mano,
por ejemplo:
{% url 'appreportes:detalle' reporte.pk %}

## Rutas principales del proyecto

- admin/ — panel de administración de Django.
- cuenta/ — rutas de la aplicación appusuarios.
- (raíz) — rutas de la aplicación appreportes.

## Rutas de appreportes (app_name = "appreportes")

/ (inicio) — página de inicio.
/reportes/ (lista) — lista de reportes con filtros.
/reportes/nuevo/ (crear) — registrar un reporte.
/reportes/<id>/ (detalle) — detalle de un reporte.
/reportes/<id>/editar/ (editar) — modificar un reporte.
/reportes/<id>/eliminar/ (eliminar) — eliminar un reporte.
/reportes/<id>/evidencia/ (agregar_evidencia) — agregar fotografía.
/reportes/<id>/estado/ (cambiar_estado) — cambiar el estado.
/reportes/<id>/seguimiento/ (registrar_seguimiento) — registrar seguimiento.
/reportes/<id>/aporte/ (aportar_informacion) — aporte del ciudadano.
/reportes/<id>/asignar/ (asignar) — asignar a una institución (administrador).
/reportes/<id>/tomar/ (tomar) — tomar el caso para la institución del responsable.
/mi-panel/ (panel) — panel personal según el rol.

## Rutas de appusuarios (app_name = "appusuarios")

/cuenta/registro/ (registro) — crear cuenta.
/cuenta/ingresar/ (ingresar) — iniciar sesión.
/cuenta/salir/ (salir) — cerrar sesión.
/cuenta/perfil/ (perfil) — mi perfil.

## Plantillas HTML

Se creó una plantilla base reutilizable, templates/base.html, que heredan todas las páginas mediante {% extends "base.html" %}. Contiene:

- Encabezado y menú de navegación — cambia según el usuario. Los visitantes ven Iniciar sesión y Registrarse; con la sesión iniciada aparecen Mi panel, Nuevo reporte y un menú con el nombre del usuario (Perfil, Cambiar contraseña y Cerrar sesión). El enlace al Panel de administración solo lo ve el administrador.
- Mensajes del sistema — confirmaciones como "Tu reporte fue registrado", mostradas como alertas.
- Bloque de contenido — {% block contenido %}, que cada página llena con lo suyo.
- Pie de página — datos del grupo y de la universidad.

## Plantillas parciales reutilizables (templates/includes/)

- formulario.html — dibuja cualquier formulario con sus etiquetas, ayudas y errores.
- campo.html — dibuja un campo individual, incluido el selector de fotografías en español.
- tarjeta_reporte.html — tarjeta resumida de un reporte, usada en el inicio, la lista y el panel.

## Plantillas por aplicación

- appreportes/ — inicio.html, reporte_lista.html, reporte_detalle.html, reporte_form.html (sirve para registrar y para modificar) y reporte_confirmar_eliminar.html.
- appusuarios/ — registro.html, ingresar.html, perfil.html y cambiar_clave.html.

## Interfaz gráfica

La interfaz se desarrolló con Bootstrap 5 y Bootstrap Icons, complementados con una hoja de estilos propia, static/css/estilos.css, que define la identidad visual del proyecto en tonos verdes.

- Diseño adaptable (RNF01) — la cuadrícula de Bootstrap reorganiza el contenido según el tamaño de la pantalla. En celulares, el menú se convierte en un botón desplegable y las tarjetas se apilan en una columna.
- Organización clara (RNF06) — contadores de reportes por estado en la página de inicio; tarjetas de reportes con su fotografía, categoría, comunidad, fecha y gravedad; y el detalle del reporte dividido en secciones (descripción, evidencias, seguimiento e historial).
- Colores por estado y gravedad — Pendiente en amarillo, En proceso en azul, Resuelto en verde y Descartado en gris. Los casos de gravedad alta se marcan con un ícono de alerta.
- Formularios intuitivos — todos reciben el estilo de Bootstrap automáticamente gracias a la clase EstiloBootstrapMixin; marcan los campos obligatorios y muestran los errores debajo de cada campo. El formulario de reporte está dividido en secciones ("¿Qué está pasando?", "¿Dónde?" y "Evidencia") e incluye un botón para obtener la ubicación actual del dispositivo.
- Interfaz en español — etiquetas, mensajes, listas de selección y selector de fotografías.

## Integración funcional

Las vistas, las plantillas y los modelos funcionan conectados entre sí. Toda la información se guarda en la base de datos EcoReporteComunitario de SQL Server, mediante el conector mssql-django y el ODBC Driver for SQL Server. Los datos de conexión se leen desde un archivo .env, que no se sube al repositorio.

## Flujo de la información

1. El usuario envía un formulario desde una plantilla.
2. La vista valida los datos con el formulario de Django (RNF02).
3. Las reglas de negocio están en los métodos de los modelos. Por ejemplo, ReporteAmbiental.cambiar_estado() valida la transición, el permiso y el seguimiento antes de guardar.
4. El modelo guarda la información en SQL Server, que además aplica sus propias restricciones (llaves primarias y foráneas, campos únicos y restricciones CHECK).
5. La vista consulta los datos actualizados y los envía a la plantilla para mostrarlos.

## Ejemplos de la integración

- Registro de un reporte — se guardan, en una sola transacción, la Ubicación, el ReporteAmbiental y su Evidencia.
- Cambio de estado — crea automáticamente un registro en HistorialEstado.
- Página de inicio — calcula en tiempo real los contadores por estado.
- Panel de usuario — consulta los reportes según el rol de quien inició sesión.
- Fotografías — se almacenan en la carpeta media/ y en la base de datos se guarda la ruta del archivo.

## Roles integrados en las pantallas

- Visitante — consultar el inicio, la lista y el detalle de los reportes.
- Ciudadano — registrar reportes; editar y eliminar el suyo mientras está Pendiente; agregar fotos e información mientras el caso está abierto.
- Responsable (uno por institución) — tomar casos sin asignar para su institución y, en los casos de su institución, cambiar el estado, registrar seguimiento y subir fotografías.
- Administrador (único) — asignar y reasignar casos a las instituciones, atender cualquier caso, y gestionar usuarios y catálogos en /admin/.

### Beneficios sociales:

El proyecto EcoReporte Comunitario busca fortalecer la participación ciudadana mediante una plataforma digital que facilite la identificación, el registro y el seguimiento de los problemas ambientales que afectan a las comunidades. Asimismo, promueve la comunicación y colaboración entre los habitantes, las alcaldías y las organizaciones ambientales, permitiendo una mejor organización y atención de las situaciones reportadas. También fomenta la educación ambiental, la responsabilidad colectiva y el compromiso con la protección de los recursos naturales, contribuyendo a mejorar la salud pública, la calidad de vida y el bienestar de la población, así como a construir comunidades más limpias, seguras y sostenibles.
