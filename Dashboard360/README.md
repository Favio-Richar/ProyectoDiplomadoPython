# Dashboard 360 de Olist

Proyecto integrador del curso **DPL1046: Programación en Python y Manipulación de Datos**, Diplomado en Ingeniería de Datos con Python, Universidad de las Américas. Profesor: PhD. Juan Manuel Rozas.

**Tema elegido:** 10 · Dashboard 360 del negocio
**Integrantes:** Favio Jimenez B · Roberto Muñoz Velasco

Un pipeline de datos en Python que corre localmente con un solo comando. Lee nueve tablas de Olist, las valida, calcula cinco indicadores ejecutivos, guarda los resultados en SQLite y los muestra en un dashboard de Streamlit.

## Contenido

1. [Caso de estudio](#caso-de-estudio)
2. [Resultados del caso](#resultados-del-caso)
3. [Indicadores y sus definiciones](#indicadores-y-sus-definiciones)
4. [Datos de entrada](#datos-de-entrada)
5. [Arquitectura del pipeline](#arquitectura-del-pipeline)
6. [Requisitos e instalación](#requisitos-e-instalación)
7. [Cómo ejecutar](#cómo-ejecutar)
8. [Salidas](#salidas)
9. [Pruebas con pytest](#pruebas-con-pytest)
10. [Calidad y buenas prácticas](#calidad-y-buenas-prácticas)
11. [Estructura del proyecto](#estructura-del-proyecto)
12. [Cumplimiento de la rúbrica](#cumplimiento-de-la-rúbrica)
13. [Control de versiones con Git](#control-de-versiones-con-git)
14. [Solución de problemas](#solución-de-problemas)
15. [Limitaciones conocidas](#limitaciones-conocidas)
16. [Próximos pasos](#próximos-pasos)
17. [Presentación y uso de IA](#presentación-y-uso-de-ia)

## Caso de estudio

**Contexto.** Olist es un marketplace de comercio electrónico de Brasil. Su conjunto de datos público (Olist Brazilian E-Commerce, el dataset del curso) reúne pedidos históricos de septiembre de 2016 a agosto de 2018 (pedidos entregados), con sus ítems, pagos, reseñas, productos, clientes, vendedores y ubicaciones. Los datos llegan en nueve archivos CSV separados.

**Situación.** Una persona responsable de la gestión comercial u operativa necesita ver el negocio completo: cuánto se vende, cuánto gasta cada pedido, qué tan satisfechos quedan los clientes, si las entregas llegan en la fecha prometida y qué categorías y regiones concentran las ventas. Hoy esa respuesta está repartida en nueve tablas que no se pueden sumar sin cuidado: un pedido tiene varios ítems, varios pagos y a veces varias reseñas, y unirlos sin agregar antes multiplicaría los importes.

**Pregunta de negocio.** ¿Cómo se comportan las ventas, las reseñas y las entregas de los pedidos registrados en Olist, y qué categorías y regiones concentran las ventas?

**Destinatario.** La persona responsable de la gestión comercial u operativa. El dashboard describe datos históricos del conjunto Olist; no representa ventas actuales ni calcula utilidad.

**Solución.** Un pipeline que:

1. lee y valida las nueve tablas (claves nulas o duplicadas, importes, puntuaciones, coordenadas);
2. agrega cada tabla al nivel correcto antes de unirla (ítems, pagos y reseñas se resumen por pedido);
3. calcula los cinco indicadores con definiciones explícitas;
4. comprueba que los totales cuadran (pedidos, GMV por categoría y GMV por vendedor);
5. guarda ocho tablas en SQLite, reemplazándolas en cada ejecución para no duplicar datos;
6. las presenta en un dashboard con resumen ejecutivo, exploración y controles de calidad.

**Decisiones que apoya el caso** (ver resultados abajo): dónde revisar la logística (estados con menos entregas a tiempo) y qué categorías priorizar (las que más concentran el GMV).

## Resultados del caso

Resultados calculados por el pipeline sobre los datos del curso, guardados en `kpis_generales`:

| Indicador | Resultado |
|---|---:|
| Pedidos entregados (población del análisis) | 96.478 de 99.441 (97,02 %) |
| GMV (precios de productos, sin flete) | 13.221.498,11 |
| Flete | 2.198.275,64 |
| Ticket promedio | 137,04 |
| Satisfacción promedio | 4,16 de 5, sobre 95.832 pedidos con reseña |
| Entregas a tiempo | 93,23 % sobre 96.470 pedidos evaluables |

Los importes están en la moneda original de los datos, sin conversión.

**Cinco categorías con mayor GMV:** health_beauty (1,23 M), watches_gifts (1,17 M), bed_bath_table (1,02 M), sports_leisure (0,95 M) y computers_accessories (0,89 M). Juntas suman el 39,8 % del GMV.

**Evolución mensual.** El GMV mensual pasó de 0,11 M en enero de 2017 a entre 0,83 M y 0,98 M al mes en 2018. El valor más alto es noviembre de 2017 (0,99 M). Como los datos incluyen un solo noviembre, no se puede afirmar estacionalidad.

**Entregas por estado.** Entre los ocho estados con más pedidos, RJ (87,9 %) y BA (87,8 %) tienen el menor porcentaje de entregas a tiempo; SP llega a 95,5 %. SP concentra el 38,3 % del GMV.

## Indicadores y sus definiciones

| Indicador | Definición |
|---|---|
| **GMV** | Suma de precios de productos en pedidos entregados. El flete se presenta separado. GMV no representa utilidad. |
| **Ticket promedio** | GMV dividido por pedidos de la misma población. |
| **Satisfacción** | Primero se calcula la media de reseñas de cada pedido; luego se promedian los pedidos con puntuación. Cada pedido tiene el mismo peso en la media final. |
| **Entregas a tiempo** | Fecha real igual o anterior al día estimado, comparando días calendario. Solo se incluyen pedidos con fechas válidas para esa comparación; los demás se informan como no evaluables, no como atrasados. |
| **Categorías principales** | Suma de precios de productos entregados agrupados por categoría. Se conserva el nombre original si falta la traducción y los productos sin categoría se agrupan como `sin_categoria`. |

Por qué estas reglas:

- Las reseñas se promedian primero por pedido porque 551 pedidos tienen más de una reseña.
- Ticket y GMV usan la misma población para que numerador y denominador sean comparables.
- El ticket global no es el promedio simple de los tickets mensuales.
- Los pedidos únicos por categoría no son aditivos (un pedido puede tener varias categorías); el GMV y los ítems sí.

No se declara una moneda porque no se verificó documentalmente en los materiales del curso.

## Datos de entrada

Coloca en `data/raw/` los nueve CSV originales proporcionados para el curso. El pipeline los usa todos y los conserva sin modificar.

| Archivo | Registros | Aporte |
|---|---:|---|
| `olist_orders_dataset.csv` | 99.441 | Estado, compra, fechas de entrega y cliente del pedido |
| `olist_order_items_dataset.csv` | 112.650 | Productos, precios, flete y vendedores |
| `olist_order_payments_dataset.csv` | 103.886 | Total pagado por pedido y conciliación con las ventas |
| `olist_order_reviews_dataset.csv` | 99.224 | Puntuaciones de satisfacción |
| `olist_products_dataset.csv` | 32.951 | Categoría de cada producto |
| `olist_customers_dataset.csv` | 99.441 | Identidad, ciudad, estado y prefijo postal del cliente |
| `olist_sellers_dataset.csv` | 3.095 | Identidad y ubicación del vendedor |
| `olist_geolocation_dataset.csv` | 1.000.163 | Coordenadas asociadas a prefijos postales |
| `product_category_name_translation.csv` | 71 | Traducción de categorías al inglés |

Total: 1.550.922 filas, unos 126 MB, formato CSV.

### Calidad de los datos de entrada

- 775 pedidos no tienen ítems asociados.
- 551 pedidos tienen más de una reseña.
- La geolocalización tiene 261.831 filas repetidas y 19.015 prefijos postales distintos; se calcula un punto aproximado por prefijo.
- 2.965 pedidos no tienen fecha de entrega al cliente.
- El 58,7 % de las reseñas no tiene comentario.
- Entre los pedidos entregados hay 646 sin reseña, 1 sin pago, 264 sin coordenadas y 299 con diferencia de pago superior a un centavo. Se informan en el dashboard, no se ocultan.
- No hay pedidos entregados en noviembre de 2016, y septiembre y diciembre de 2016 tienen un solo pedido cada uno.

## Arquitectura del pipeline

```text
ENTRADA                    PROCESO                                   SALIDA
data/raw/ (9 CSV)  ──►  src/etl.py         pedidos entregados   ──►  data/processed/dashboard360.sqlite
config/settings.json    src/indicadores.py reseñas, entregas,         (8 tablas)
                                           categorías              ──►  dashboard.py (Streamlit)
                        src/contexto.py    clientes, pagos,        ──►  reports/pipeline.log
                                           vendedores, geografía
```

`pipeline.py` es el punto de entrada: carga la configuración, activa el registro y ejecuta las tres etapas en orden.

| Etapa | Módulo y función | Qué hace |
|---|---|---|
| 1 | `src/etl.py` → `ejecutar_etl` | Lee pedidos e ítems, valida claves e importes, selecciona pedidos entregados, agrega ítems por pedido, resume por mes y guarda `pedidos_entregados` y `resumen_mensual`. |
| 2 | `src/indicadores.py` → `generar_indicadores` | Une fechas y reseñas (una fila por pedido), evalúa las entregas, asigna categorías con traducción, reconcilia el GMV y guarda `pedidos_dashboard`, `ventas_categorias` y `kpis_generales`. |
| 3 | `src/contexto.py` → `incorporar_contexto` | Une clientes, pagos agregados por pedido, vendedores y geografía aproximada, comprueba que se conservan pedidos y GMV, y guarda `pedidos_dashboard` ampliada, `clientes_geografia`, `vendedores_dashboard` y `geografia_postal`. |

Funciones principales de `src/etl.py`:

| Función | Responsabilidad |
|---|---|
| `validar_clave` | Detiene el proceso si una clave tiene nulos o duplicados. |
| `transformar_pedidos` | Comprueba ítems huérfanos, convierte fechas e importes, rechaza nulos y negativos, y deja una fila por pedido entregado. |
| `resumir_por_mes` | Suma pedidos, ítems, GMV y flete por mes y calcula el ticket del mismo período. |
| `ejecutar_etl` | Coordina lectura, transformación y escritura en SQLite. |

**Reglas de integración.**

- Cada unión se declara con `validate="one_to_one"` o `validate="many_to_one"`, de modo que pandas falla si la cardinalidad no es la esperada.
- Los pagos y las reseñas se agregan por pedido antes de unirlos; nunca se unen filas de pagos con filas de ítems, porque multiplicaría los importes.
- Un pago o una reseña ausente se conserva como nulo, no como cero.
- Los prefijos postales se leen como texto y se normalizan a cinco posiciones.
- Las coordenadas ausentes o fuera de rango mundial se excluyen del cálculo del punto por prefijo.
- Se exige que el GMV por categoría y por vendedor coincida con el GMV total (tolerancia de medio centavo).

**Herramientas:** Python 3.12, pandas, sqlite3 (biblioteca estándar), Streamlit y Altair para el dashboard, pytest para las pruebas y logging para el registro.

## Requisitos e instalación

- Python 3.12.
- Los nueve CSV en `data/raw/`.
- Dependencias declaradas en `requirements.txt`.

Ejecuta desde la raíz `Dashboard360/` en Bash (Git Bash o MSYS2):

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
```

Al abrir otra terminal, activa el entorno nuevamente:

```bash
source .venv/Scripts/activate
```

Debe aparecer `(.venv)` en el prompt. En Mac o Linux, la activación es `source .venv/bin/activate`.

## Cómo ejecutar

### 1. Pipeline completo (un solo comando)

Desde la raíz del proyecto y con `.venv` activo:

```bash
python pipeline.py
```

Lee y valida los CSV, integra las tablas, calcula los indicadores y guarda los resultados en SQLite. Los mensajes aparecen en la terminal y en `reports/pipeline.log`. Con los datos del curso termina en unos 10 segundos y cierra con `Pipeline completado correctamente.`

Las tablas calculadas se **reemplazan** al repetir la ejecución, así que ejecutarlo varias veces no duplica pedidos ni importes. El pipeline se ejecutó dos veces con las mismas entradas: las ocho tablas conservaron sus conteos y sus hashes SHA-256. La evidencia está en `reports/verificacion_pipeline_completo.json` (pipeline completo) y `reports/verificacion_repeticion_etl.json` (primer ETL).

### 2. Dashboard

En otra terminal, desde `Dashboard360/`, con `.venv` activo:

```bash
python -m streamlit run dashboard.py
```

El dashboard tiene tres pestañas:

- **Resumen ejecutivo:** los cinco indicadores, evolución mensual del GMV, categorías con mayores ventas (5, 10 o 15), distribución de la satisfacción por puntaje, entregas a tiempo por mes, resumen mensual descargable y vendedores con mayores ventas.
- **Explorar pedidos:** filtros por rango de meses y estado del cliente; los indicadores se recalculan con la selección. Los filtros afectan solo esta pestaña.
- **Calidad y definiciones:** controles de cobertura (pedidos sin reseña, entregas no evaluables, sin pago, sin coordenadas, diferencias de pago) y cómo se interpreta cada indicador.

Para actualizar los datos, ejecuta de nuevo `python pipeline.py` y pulsa **Actualizar datos** en el dashboard. El dashboard abre la base en modo de solo lectura.

### 3. Exploración inicial (opcional)

```bash
python src/explorar_datos.py
```

Lee pedidos e ítems y genera los reportes de calidad de la primera etapa en `reports/`: `inventario_inicial.csv`, `calidad_por_columna.csv`, `relacion_pedidos_items.csv` y `resumen_pedidos_estado.csv`. No es necesario ejecutarlo antes del pipeline.

### Configuración

El nivel y la ruta del registro están en `config/settings.json`:

```json
{
  "logging": {
    "level": "INFO",
    "file": "reports/pipeline.log"
  }
}
```

El nivel debe ser `DEBUG`, `INFO`, `WARNING`, `ERROR` o `CRITICAL`; si no, el pipeline se detiene con un mensaje claro. El proyecto no usa credenciales ni claves de acceso, por lo que no necesita un archivo `.env` (igualmente está ignorado por Git).

## Salidas

La base `data/processed/dashboard360.sqlite` contiene ocho tablas:

| Tabla | Filas | Nivel y contenido |
|---|---:|---|
| `pedidos_entregados` | 96.478 | Una fila por pedido entregado, importes y mes de compra |
| `resumen_mensual` | 23 | Pedidos, ítems, GMV, flete y ticket por mes |
| `pedidos_dashboard` | 96.478 | Pedidos entregados con reseñas, fechas, cliente, pago y coordenadas |
| `ventas_categorias` | 74 | GMV, flete, ítems y pedidos por categoría |
| `kpis_generales` | 1 | Una fila con los indicadores ejecutivos y sus denominadores |
| `clientes_geografia` | 99.441 | Clientes y coordenadas aproximadas cuando existen |
| `vendedores_dashboard` | 3.095 | Vendedores con ubicación y ventas de pedidos entregados |
| `geografia_postal` | 19.015 | Punto aproximado por prefijo postal |

SQLite guarda todo en un archivo binario: no se abre como texto. Para inspeccionarlo, usa un visor de SQLite en VS Code, consultas SQL o Python. Que VS Code avise que no puede mostrarlo como texto no significa que esté dañado.

Reportes generados en `reports/`:

| Archivo | Contenido |
|---|---|
| `pipeline.log` | Registro de cada ejecución del pipeline |
| `verificacion_pipeline_completo.json` | Conteos y hashes de las ocho tablas antes y después de repetir el pipeline |
| `verificacion_repeticion_etl.json` | Verificación de repetición del primer ETL |
| `inventario_inicial.csv` | Filas, columnas, nulos, duplicados y claves de pedidos e ítems |
| `calidad_por_columna.csv` | Tipo y nulos por columna |
| `relacion_pedidos_items.csv` | Pedidos sin ítems e ítems sin pedido |
| `resumen_pedidos_estado.csv` | Pedidos por estado |

Los resultados procesados no reemplazan los CSV originales.

## Pruebas con pytest

Ejecuta desde la raíz con `.venv` activo:

```bash
python -m pytest -v
```

Salida real de la ejecución del 27 de octubre de 2026 (Python 3.12.9, pytest 9.1.1, Windows):

```text
$ python -m pytest -v
=========================== test session starts ===========================
platform win32 -- Python 3.12.9, pytest-9.1.1, pluggy-1.7.0 -- C:\Users\favio\ProyectoDiplimadoPython\Dashboard360\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\favio\ProyectoDiplimadoPython\Dashboard360
plugins: anyio-4.15.1
collected 9 items

tests/test_etl.py::test_validar_clave_acepta_clave_unica PASSED                   [ 11%]
tests/test_etl.py::test_validar_clave_rechaza_nulos PASSED                        [ 22%]
tests/test_etl.py::test_validar_clave_rechaza_duplicados PASSED                   [ 33%]
tests/test_etl.py::test_transformar_pedidos_incluye_solo_entregados PASSED        [ 44%]
tests/test_etl.py::test_transformar_pedidos_rechaza_item_sin_pedido PASSED        [ 55%]
tests/test_etl.py::test_transformar_pedidos_rechaza_precio_negativo PASSED        [ 66%]
tests/test_etl.py::test_resumir_por_mes_crea_un_registro_por_mes PASSED           [ 77%]
tests/test_etl.py::test_resumir_por_mes_suma_pedidos_items_y_gmv PASSED           [ 88%]
tests/test_etl.py::test_resumir_por_mes_calcula_ticket_del_mismo_periodo PASSED   [100%]

============================ 9 passed in 2.66s ============================
```

Las nueve pruebas usan tablas pequeñas creadas en memoria: no leen los CSV reales ni modifican la base del proyecto.

| # | Prueba | Qué verifica |
|---|---|---|
| 1 | `test_validar_clave_acepta_clave_unica` | Una clave completa y única se acepta. |
| 2 | `test_validar_clave_rechaza_nulos` | Una clave con nulos lanza `ValueError`. |
| 3 | `test_validar_clave_rechaza_duplicados` | Una clave repetida lanza `ValueError`. |
| 4 | `test_transformar_pedidos_incluye_solo_entregados` | Solo los pedidos `delivered` pasan, con su GMV. |
| 5 | `test_transformar_pedidos_rechaza_item_sin_pedido` | Un ítem de un pedido inexistente lanza `ValueError`. |
| 6 | `test_transformar_pedidos_rechaza_precio_negativo` | Un precio negativo lanza `ValueError`. |
| 7 | `test_resumir_por_mes_crea_un_registro_por_mes` | Una fila por mes de compra. |
| 8 | `test_resumir_por_mes_suma_pedidos_items_y_gmv` | Suma correcta de pedidos, ítems y GMV de un mes. |
| 9 | `test_resumir_por_mes_calcula_ticket_del_mismo_periodo` | El ticket es GMV mensual dividido por pedidos de ese mes. |

Cobertura actual: tres pruebas por cada función de transformación de `src/etl.py` (`validar_clave`, `transformar_pedidos`, `resumir_por_mes`). Las reglas de `src/indicadores.py` y `src/contexto.py` se comprobaron con la reconciliación de totales del propio pipeline y con la verificación de repetición, pero aún no tienen pruebas unitarias propias (ver [Próximos pasos](#próximos-pasos)).

## Calidad y buenas prácticas

- **Código modular:** lectura y transformación en `src/`, punto de entrada en `pipeline.py`, interfaz en `dashboard.py`, con docstrings en sus funciones.
- **Validación de datos:** claves nulas o duplicadas, importes nulos o negativos, ítems sin pedido, puntuaciones fuera de 1 a 5, pagos nulos o negativos, ítems con vendedores o productos inexistentes y conservación de pedidos y GMV al integrar.
- **Manejo de errores y logging:** `pipeline.py` registra el inicio, cada etapa, el cierre y cualquier excepción (con su traza) en la terminal y en `reports/pipeline.log`, y vuelve a lanzar el error para que la ejecución indique fallo. El dashboard muestra un mensaje claro si falta la base o no se puede leer.
- **Configuración externa:** nivel y archivo del registro en `config/settings.json`, validados al iniciar.
- **Rutas relativas:** todas se construyen a partir de la ubicación del archivo (`Path(__file__)`), sin rutas personales.
- **Sin credenciales en el código:** el proyecto no usa claves. `.env` está en `.gitignore`.
- **Dependencias:** `requirements.txt` con las versiones exactas del entorno.
- **Repetible sin duplicar:** las tablas de resultados se reemplazan (`if_exists="replace"`) y se comprobó con hashes SHA-256 que dos ejecuciones dan resultados idénticos.
- **Datos originales intactos:** los CSV de `data/raw/` solo se leen.
- **`.gitignore`:** excluye el entorno virtual, la caché de pytest, `.env`, los CSV de `data/raw/`, `data/processed/*` y `reports/*`.

## Estructura del proyecto

```text
Dashboard360/
├── config/
│   └── settings.json          Configuración del registro
├── data/
│   ├── raw/                   Nueve CSV originales (solo lectura)
│   └── processed/             Base SQLite generada
├── docs/                      Documentación por etapa y guía de desarrollo
│   └── presentacion/          Presentación final de 15 minutos y capturas del dashboard
├── reports/                   Reportes, registro y verificaciones generados
├── src/
│   ├── etl.py                 Validación, selección de pedidos entregados y resumen mensual
│   ├── indicadores.py         Satisfacción, entregas y categorías
│   ├── contexto.py            Clientes, pagos, vendedores y geografía
│   └── explorar_datos.py      Exploración inicial y reportes de calidad
├── tests/
│   └── test_etl.py            Nueve pruebas pytest
├── dashboard.py               Interfaz Streamlit
├── pipeline.py                Punto de entrada del procesamiento
├── proyecto-integrador.md     Encargo y rúbrica del profesor
├── requirements.txt           Dependencias
└── README.md
```

Documentación en `docs/`:

| Archivo | Contenido |
|---|---|
| `Guia_de_estudio_Dashboard360.md` | Proceso completo de desarrollo: pasos, comandos, código explicado, errores y glosario |
| `Referencia_rapida_Dashboard360.md` | Comandos, reglas, cifras y preguntas de defensa |
| `Guia_desarrollo_Dashboard_360_Olist.docx` | Guía de desarrollo del tema |

### Cómo creció el proyecto por unidad

| Unidad | Qué se entregó |
|---|---|
| 1 (Clases 1–3) | `src/explorar_datos.py`: lee pedidos e ítems, valida claves y genera los reportes básicos de calidad. |
| 2 (Clases 4–6) | ETL con pandas: limpia, combina con `merge`, resume con `groupby` y guarda en SQLite sin duplicar al repetir. Se amplía a las nueve tablas. |
| 3 (Clases 7–9) | Funciones, errores, logging, pruebas con pytest, configuración externa, dashboard y presentación. |

## Cumplimiento de la rúbrica

| Criterio (peso) | Dónde se ve |
|---|---|
| **Funcionalidad del pipeline (35 %)** | Un solo comando (`python pipeline.py`); nueve tablas integradas; resultados reproducibles con evidencia en `reports/verificacion_pipeline_completo.json`. |
| **Calidad del código (30 %)** | Código modular en `src/`; docstrings; errores y logging en `pipeline.py`; nueve pruebas en `tests/test_etl.py`. |
| **Buenas prácticas (15 %)** | Rutas relativas; `config/settings.json`; `requirements.txt`; este README; ejecución repetible sin duplicar; sin credenciales en el código. |
| **Presentación y valor de negocio (20 %)** | `docs/presentacion/Dashboard360_presentacion.pptx`, basada en la plantilla del curso; demo con `pipeline.py` y `dashboard.py`. |

Checklist de entrega del profesor:

- [x] Carpeta del proyecto con el pipeline en Python (scripts organizados).
- [x] Corre localmente en VS Code, de principio a fin, con un comando.
- [x] Al menos 2 fuentes o tablas de Olist integradas (son nueve).
- [x] Validación de datos y manejo de errores con logging.
- [x] Tests con pytest y salida de `pytest -v` en el README.
- [x] `requirements.txt` con las dependencias.
- [x] README con qué hace, cómo instalarlo y cómo ejecutarlo.
- [x] Presentación final de 15 minutos basada en el template del curso.

## Control de versiones con Git

Repositorio: <https://github.com/Favio-Richar/ProyectoDiplomadoPython.git>

Los comandos se ejecutan en Git Bash. El repositorio guarda la carpeta `Dashboard360/` dentro de `ProyectoDiplomadoPython/`. **No incluye** los CSV originales (`data/raw/*.csv`), el entorno virtual (`.venv/`), la base generada (`data/processed/`) ni los reportes (`reports/`); están en `.gitignore`. Los resultados se regeneran con `python pipeline.py`.

### Subir el proyecto por primera vez

Desde la carpeta `ProyectoDiplomadoPython/` (la que contiene `Dashboard360/`):

```bash
git init                      # convierte la carpeta en un repositorio
git branch -M main            # nombra la rama principal "main"
git add .                     # prepara todos los archivos (menos los del .gitignore)
git status                    # muestra qué se va a subir
git commit -m "Dashboard 360 de Olist: pipeline, dashboard, pruebas y documentación"   # guarda una versión con un mensaje
git remote add origin https://github.com/Favio-Richar/ProyectoDiplomadoPython.git      # enlaza con el repositorio de GitHub
git push -u origin main       # sube la rama main a GitHub
```

Antes del `commit`, `git status` no debe mostrar `.venv/`, `data/processed/` ni `reports/`. Si es la primera vez que se usa Git en el computador, se configura la identidad:

```bash
git config --global user.name "Nombre Apellido"          # nombre que aparece en los commits
git config --global user.email "correo@ejemplo.com"      # correo que aparece en los commits
```

### Clonar en otro computador

```bash
git clone https://github.com/Favio-Richar/ProyectoDiplomadoPython.git   # descarga el repositorio
cd ProyectoDiplomadoPython/Dashboard360                  # entra a la carpeta del proyecto
py -3.12 -m venv .venv                                   # crea el entorno virtual
source .venv/Scripts/activate                            # activa el entorno
python -m pip install -r requirements.txt                # instala las dependencias
mkdir -p data/raw                                        # crea la carpeta de datos
```

Después se copian los nueve CSV del curso a `data/raw/` y se ejecuta `python pipeline.py`.

### Actualizar el repositorio

Traer los cambios publicados:

```bash
git pull                      # descarga y une los cambios de GitHub
```

Subir cambios nuevos:

```bash
git status                    # muestra qué archivos cambiaron
git add .                     # prepara los cambios
git commit -m "Descripción breve del cambio"   # guarda una versión con un mensaje
git push                      # sube los cambios a GitHub
```

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `command not found` al usar `Get-Location` o `Get-ChildItem` | Son comandos de PowerShell y la terminal es Bash. | Usa `pwd` y `ls`. |
| `ModuleNotFoundError: No module named 'pandas'` | El entorno virtual no está activo o no se instalaron las dependencias. | `source .venv/Scripts/activate` y `python -m pip install -r requirements.txt`. |
| `FileNotFoundError` en `data/raw/...` | Faltan CSV en `data/raw/` o se ejecutó fuera de la raíz del proyecto. | Verifica los nueve archivos y ejecuta desde `Dashboard360/`. |
| `ValueError: logging.level debe ser ...` | Nivel inválido en `config/settings.json`. | Usa `DEBUG`, `INFO`, `WARNING`, `ERROR` o `CRITICAL`. |
| El dashboard dice «No se encontró la base de resultados» | Aún no se ejecutó el pipeline. | Ejecuta `python pipeline.py` y vuelve a abrir el dashboard. |
| El dashboard muestra datos antiguos | Caché del dashboard. | Pulsa **Actualizar datos** en la barra lateral. |
| VS Code no muestra el `.sqlite` como texto | Es un archivo binario. | Usa un visor de SQLite o consultas SQL. |

## Limitaciones conocidas

- Los datos son históricos; los meses extremos tienen cobertura parcial y no hay pedidos entregados en noviembre de 2016.
- Los indicadores comerciales incluyen solo pedidos con estado `delivered`.
- Hay pedidos sin pago, sin coordenadas y con diferencias entre el pago y productos más flete; se informan sin ocultarlos.
- Las coordenadas son aproximaciones por prefijo postal, no domicilios exactos.
- Una diferencia de pago requiere investigación y no demuestra por sí sola fraude.
- No se calcula utilidad porque no hay datos de costos suficientes.
- Las entregas a tiempo se comparan en días calendario, no en horas.
- Las tablas de resultados se reemplazan una a una: se comprobó que repetir la ejecución no duplica datos, pero no se comprobó la recuperación ante un corte a mitad de escritura.
- Una API externa y la IA local son opcionales y no forman parte de la implementación actual.

## Próximos pasos

- Extraer funciones pequeñas de `indicadores.py` y `contexto.py` y escribir pruebas unitarias para ellas, igual que para `etl.py`.
- Usar `logging` también dentro de los módulos de `src/` en lugar de `print`.
- Publicar la base de forma atómica para tolerar cortes durante la escritura.
- Ampliar `config/settings.json` con rutas y parámetros.
- Opcional: sumar una segunda fuente con una API externa, guardar en Parquet y generar el «resumen para gerencia» con IA local, que es el ángulo sugerido para este tema.

## Presentación y uso de IA

La presentación de 15 minutos más 5 de preguntas está en `docs/presentacion/Dashboard360_presentacion.pptx`, basada en la plantilla del curso. Sigue el orden: problema de negocio, datos, arquitectura, demo, resultados, calidad y buenas prácticas, valor de negocio y aprendizajes. Ambos integrantes presentan. Las capturas del dashboard, útiles como respaldo de la demo, están en `docs/presentacion/capturas/`.

Uso de IA: se usó Codex en VS Code como asistente para escribir código, y Claude para revisar el sistema, desarrollar la presentación y hacer pequeñas correcciones en la documentación. Las instalaciones, las ejecuciones y la verificación de los resultados las hizo el estudiante a mano, comparando cada resultado con lo esperado (por ejemplo, la repetición del pipeline con hashes). Cada etapa quedó documentada en `docs/` (guía de estudio).
