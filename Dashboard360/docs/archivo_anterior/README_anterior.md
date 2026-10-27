# Dashboard 360 de Olist

Proyecto integrador del curso **DPL1046: Programación en Python y Manipulación de Datos**. Construye un pipeline local para resumir ventas, satisfacción y entregas de Olist y consultar los resultados en un dashboard.

## Pregunta de negocio

¿Cómo se comportan las ventas, las reseñas y las entregas de los pedidos registrados en Olist, y qué categorías y regiones concentran las ventas?

El destinatario es una persona responsable de la gestión comercial u operativa. El dashboard describe los datos históricos del conjunto Olist; no representa ventas actuales ni calcula utilidad.

## Indicadores

- **GMV:** suma de precios de productos en pedidos entregados. El flete se presenta separado y GMV no representa utilidad.
- **Ticket promedio:** GMV dividido por pedidos de la misma población.
- **Satisfacción:** primero se calcula la media de reseñas de cada pedido; luego se promedian los pedidos con puntuación. Cada pedido tiene el mismo peso en la media final.
- **Entregas a tiempo:** fecha real igual o anterior al día estimado. Solo se incluyen pedidos con fechas válidas para esa comparación.
- **Categorías principales:** suma de precios de productos entregados agrupados por categoría. Se conserva el nombre original si falta la traducción y se agrupan los productos sin categoría como `sin_categoria`.

Los importes se muestran en la moneda original de los datos, sin conversión. No se declara una moneda porque no se verificó documentalmente en los materiales disponibles.

## Datos de entrada

Coloca en `data/raw/` los nueve CSV originales proporcionados para el curso:

| Archivo | Registros | Uso |
|---|---:|---|
| `olist_orders_dataset.csv` | 99441 | Estado, compra y entrega de pedidos |
| `olist_order_items_dataset.csv` | 112650 | Productos, precios, flete y vendedores |
| `olist_order_payments_dataset.csv` | 103886 | Métodos e importes de pago |
| `olist_order_reviews_dataset.csv` | 99224 | Puntuaciones de reseñas |
| `olist_products_dataset.csv` | 32951 | Categorías y datos de productos |
| `olist_customers_dataset.csv` | 99441 | Identidad y ubicación de clientes |
| `olist_sellers_dataset.csv` | 3095 | Identidad y ubicación de vendedores |
| `olist_geolocation_dataset.csv` | 1000163 | Coordenadas asociadas a prefijos postales |
| `product_category_name_translation.csv` | 71 | Traducciones disponibles de categorías |

El pipeline utiliza los nueve archivos y conserva los CSV originales sin modificarlos.

## Requisitos

- Python 3.12.
- Los nueve CSV en `data/raw/`.
- Dependencias declaradas en `requirements.txt`.

SQLite forma parte de la biblioteca estándar de Python.

## Preparar el entorno

Ejecuta desde la raíz `Dashboard360/` en Bash:

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
```

Al abrir otra terminal, activa el entorno nuevamente:

```bash
source .venv/Scripts/activate
```

## Ejecutar el pipeline

Desde la raíz del proyecto y con `.venv` activo:

```bash
python pipeline.py
```

El pipeline lee y valida los CSV, integra las tablas, calcula los indicadores y guarda resultados en SQLite. La configuración del nivel y la ruta del registro está en `config/settings.json`; los mensajes aparecen en la terminal y en `reports/pipeline.log`.

Las tablas calculadas se reemplazan al repetir la ejecución. El pipeline se ejecutó dos veces con las mismas entradas: las ocho tablas SQLite conservaron sus conteos y hashes, sin duplicar registros ni importes. La evidencia está en `reports/verificacion_pipeline_completo.json`.

## Abrir el dashboard

En otra terminal, desde `Dashboard360/`, activa `.venv` si hace falta y ejecuta:

```bash
python -m streamlit run dashboard.py
```

El dashboard presenta resumen ejecutivo, exploración por mes y estado del cliente, y calidad y definiciones. Los filtros afectan solo la vista de exploración.

Para actualizar los datos, ejecuta de nuevo `python pipeline.py` y pulsa **Actualizar datos** en el dashboard.

## Salidas

La base `data/processed/dashboard360.sqlite` contiene ocho tablas:

| Tabla | Nivel y contenido |
|---|---|
| `pedidos_entregados` | Una fila por pedido entregado, importes y mes de compra |
| `resumen_mensual` | Pedidos, ítems, GMV, flete y ticket por mes |
| `pedidos_dashboard` | Pedidos entregados con reseñas, fechas, cliente y pago |
| `ventas_categorias` | GMV, flete, ítems y pedidos por categoría |
| `kpis_generales` | Una fila con los indicadores ejecutivos y denominadores |
| `clientes_geografia` | Clientes y coordenadas aproximadas cuando existen |
| `vendedores_dashboard` | Vendedores con ubicación y ventas de pedidos entregados |
| `geografia_postal` | Punto aproximado por prefijo postal |

Los reportes de calidad y relación inicial están en `reports/`. Los resultados procesados no reemplazan los CSV originales.

## Pruebas

Ejecuta desde la raíz con `.venv` activo:

```bash
python -m pytest -v
```

Salida real compartida después de ejecutar el comando:

```text
collected 9 items
9 passed in 0.72s
```

Las pruebas cubren claves nulas y duplicadas, selección de pedidos entregados, relaciones inexistentes, precios negativos, agrupación mensual, sumas y ticket promedio.

## Estructura

```text
Dashboard360/
├── config/settings.json
├── data/raw/                 CSV originales
├── data/processed/           Base SQLite generada
├── docs/                     Guía y documentación por etapa
├── reports/                  Reportes y registros generados
├── src/                      Lectura, integración e indicadores
├── tests/                    Pruebas pytest
├── dashboard.py              Interfaz Streamlit
├── pipeline.py               Punto de entrada del procesamiento
├── requirements.txt          Dependencias
└── README.md
```

## Limitaciones conocidas

- Los datos son históricos; los meses extremos tienen cobertura parcial.
- Los indicadores comerciales incluyen pedidos con estado `delivered`.
- Hay pedidos sin pago, sin coordenadas y con diferencias entre el pago y productos más flete; se informan sin ocultarlos.
- Las coordenadas son aproximaciones por prefijo postal, no domicilios exactos.
- Una diferencia de pago requiere investigación y no demuestra por sí sola fraude.
- No se calcula utilidad porque no hay datos de costos suficientes.
- Una API externa y la IA local son opcionales y no forman parte de la implementación actual.

## Presentación

El curso solicita una presentación de 15 minutos y 5 minutos de preguntas. Debe cubrir problema, datos, arquitectura, demo, resultados, calidad del código, valor de negocio y aprendizajes. Completa los nombres de integrantes, usa la plantilla oficial del curso y conserva evidencia de la demo. Ambos integrantes presentan.
