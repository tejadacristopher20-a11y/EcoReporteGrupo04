# EcoReporte_Grupo04

EcoReporte Comunitario

#### Descripción:

EcoReporte Comunitario es un proyecto de proyección social orientada al desarrollo de una aplicación web para registrar,
organizar, consultar y dar seguimiento a problemáticas ambientales identificadas en una comunidad.
Actualmente, situaciones como la proliferación de botaderos de basura a cielo abierto, el vertido clandestino
de aguas residuales o contaminantes, la quema de desechos a cielo abierto y la tala no autorizada de árboles se
gestionan de forma fragmentada o quedan invisibilizadas por la falta de un canal directo entre los ciudadanos y
los dirigentes responsables, nuestra metas sera reducir estas carencias.

## Integrantes

- Cristopher David Salmeron Tejada (tejadacristopher20-a11y)
- Oscar Javier Portillo Tejada (oscarportillo707-ccpt)
- William Javier Chacon Calderon (cc0470032026-dev)
- Diego Alexander Hernández Núñez (Diego-Hernandez-qw)
- Brandon Edenilson Alas Tobias (brandonalas074-maker)

## Proyecto

EcoReporte Comunitario.

## Estado de Proyecto

Fase 1: Organización y selección del proyecto.

## ¿En qué consiste el problema?

El problema consiste en la falta de un registro organizado de los problemas ambientales que ocurre en la comunidad.
Situaciones como la acumulación de basura, los botaderos clandestinos, la contaminación de ríos y quebradas, la quema
de desechos y el deterioro de zonas verdes pueden presentarse sin que exista una herramienta que permite registrarlas,
clasificarlas y darles seguimiento de manera ordenada.

## Identificación General de los Beneficiarios

Los principales beneficiarios seran los recidentes de la zona y también de sus alrededores, comercios y centros educativos ya que nos emplearemos en
encontrar la manera de poder solucionar las diversas problematicas ambientales presentes en la comunidad que a travez de la encuesta
realizada pudimos evidenciar la falta de un sistema tecnologico que nos permita llevar un registro y hacer una mejora en el entorno ambiental y educativo, por lo que nos esforzaremos por atender la problematica de la comunidad de Las Toreras departamento de Chalatenango.

Fase 2: Diagnostico de la problematica y definición de requisitos

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
- RF11 — Filtrar reportes.

## Lista de Requisitos No Funcionales:

- La aplicación deberá contar con una interfaz que pueda visualizarse correctamente en computadoras, tablets y dispositivos móviles.
- El sistema deberá validar los datos ingresados en los formularios antes de almacenarlos.
- El sistema deberá utilizar SQL Server para almacenar la información de la aplicación.
- El sistema deberá ser desarrollado utilizando Django, Python y HTML.
- El sistema deberá evitar exponer información personal innecesaria de los usuarios.
- La interfaz deberá presentar la información de manera clara y organizada para facilitar su utilización.

Fase 3: Diseño de clases y modelado de la Base de Datos

## Descripción de las clases principales

#### Clase Usuario

- Representa a las personas que utilizan la aplicación para registrar, consultar y dar seguimiento a problemas ambientales de acuerdo con su rol dentro del sistema.

#### Clase ReporteAmbiental

- Representa un problema ambiental registrado en el sistema, almacenando la información necesaria para identificarlo, describirlo, clasificarlo y conocer su estado.

#### Clase CategoriaProblema

- Permite clasificar los reportes ambientales según el tipo de problema identificado, como acumulación de basura, contaminación de ríos, quema de desechos o daños en zonas verdes.

#### Clase Ubicacion

- Representa el lugar donde se presenta un problema ambiental y permite almacenar la información necesaria para identificar dicha ubicación.

#### Clase Evidencia

- Representa las fotografías o archivos que sirven como evidencia de un problema ambiental registrado.

#### Clase Seguimiento

- Representa las acciones realizadas sobre un reporte ambiental y permite mantener un registro de su evolución y cambios de estado.
