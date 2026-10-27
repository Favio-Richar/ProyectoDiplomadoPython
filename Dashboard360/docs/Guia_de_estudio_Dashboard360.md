# Guía de estudio: cómo se desarrolló Dashboard 360 (Olist)

Proyecto integrador del curso DPL1046, Diplomado en Ingeniería de Datos con Python (UDLA). Tema 10: Dashboard 360 del negocio.

**Para qué sirve este documento.** Reúne en un solo lugar, en orden cronológico, los pasos, comandos y código del proyecto, con la explicación de por qué se hizo cada cosa. Sirve para estudiar en lugar de leer `docs/01` a `docs/06`; su contenido está integrado en esta guía.

**Cómo estudiarlo.** Lee una fase, cierra el documento e intenta explicarla en voz alta con tus palabras. Luego abre el código real y comprueba. Las preguntas de defensa están en `Referencia_rapida_Dashboard360.md`.

**Quién hizo qué.** Según los documentos originales, el estudiante escribió y ejecutó el código y los comandos; el asistente de IA (llamado Codex en esos documentos) revisó los archivos, comprobó resultados y ayudó con la instalación del 26 de octubre de 2026. El README declara el uso de IA. Para la defensa, lo importante es que puedas explicar cada línea.

**Los fragmentos de código están copiados literalmente de los archivos del proyecto**, con su número de línea. Si editas un archivo, esos números dejarán de coincidir.

---

## Índice

0. Visión general: qué se construyó y cómo fluyen los datos
1. Fase 0: preparar el entorno
2. Fase 1: explorar los datos (`src/explorar_datos.py`)
3. Fase 2: primer ETL y SQLite (`src/etl.py`)
4. Fase 3: los cinco indicadores (`src/indicadores.py`)
5. Fase 4: integrar las nueve tablas (`src/contexto.py`)
6. Fase 5: configuración, logging y punto de entrada (`pipeline.py`)
7. Fase 6: pruebas con pytest (`tests/test_etl.py`)
8. Fase 7: el dashboard (`dashboard.py`)
9. Fase 8: README, revisión y presentación
10. Secuencia completa de comandos, de cero a dashboard
11. Errores que aparecieron y qué enseñan
12. Glosario
13. Qué faltaba en los documentos originales

---

## 0. Visión general

### El caso

Olist es un marketplace brasileño. El conjunto de datos público reúne pedidos históricos (septiembre de 2016 a agosto de 2018) en **nueve archivos CSV**. Una persona de gestión comercial u operativa necesita ver el negocio completo: cuánto se vende, cuánto gasta cada pedido, qué tan satisfechos quedan los clientes, si las entregas llegan a tiempo y qué categorías y regiones concentran las ventas.

**Pregunta de negocio:** ¿cómo se comportan las ventas, las reseñas y las entregas de los pedidos registrados en Olist, y qué categorías y regiones concentran las ventas?

### El problema técnico central

Un pedido tiene **varios ítems, varios pagos y a veces varias reseñas**. Si se unen las tablas sin agregar antes, las filas se multiplican y los importes se inflan. Toda la arquitectura gira alrededor de una regla:

> **Agregar cada tabla al nivel "una fila por pedido" ANTES de unirla, y comprobar después que no cambió ni el número de pedidos ni el GMV.**

### Flujo de datos

```text
data/raw/*.csv  (9 archivos, solo lectura)
      |
      v
pipeline.py  -- carga config/settings.json y configura el logging
      |
      +--> etapa 1  src/etl.py          ejecutar_etl
      |        pedidos + ítems --> pedidos_entregados, resumen_mensual
      |
      +--> etapa 2  src/indicadores.py  generar_indicadores
      |        + reseñas, productos, traducciones --> pedidos_dashboard,
      |          ventas_categorias, kpis_generales
      |
      +--> etapa 3  src/contexto.py     incorporar_contexto
               + clientes, pagos, vendedores, geolocalización
               --> pedidos_dashboard (ampliada), clientes_geografia,
                   vendedores_dashboard, geografia_postal
      |
      v
data/processed/dashboard360.sqlite  (8 tablas)
      |
      v
dashboard.py  (Streamlit; lee la base en modo solo lectura)
```

### Estructura del proyecto

```text
Dashboard360/
├── config/settings.json      configuración de logging
├── data/raw/                 9 CSV originales (no se modifican)
├── data/processed/           base SQLite generada
├── docs/                     documentación por etapa
├── reports/                  reportes y pipeline.log generados
├── src/
│   ├── explorar_datos.py     exploración inicial
│   ├── etl.py                primer ETL
│   ├── indicadores.py        cinco indicadores
│   └── contexto.py           integración de las nueve tablas
├── tests/test_etl.py         9 pruebas pytest
├── dashboard.py              interfaz Streamlit
├── pipeline.py               punto de entrada (un solo comando)
├── requirements.txt          dependencias
└── README.md
```

### Cifras clave

| Dato | Valor |
|---|---:|
| Pedidos totales | 99.441 |
| Pedidos entregados (población de los indicadores) | 96.478 (97,02 %) |
| Ítems de pedidos entregados | 110.197 |
| GMV (precios, sin flete) | 13.221.498,11 |
| Flete | 2.198.275,64 |
| Ticket promedio | 137,04 |
| Satisfacción promedio | 4,16 sobre 5 (95.832 pedidos con reseña; 646 sin reseña) |
| Entregas a tiempo | 93,23 % (89.936 de 96.470 evaluables; 8 no evaluables) |
| Categorías en la tabla | 74 (`sin_categoria`: 170.726,63 de GMV y 1.537 ítems) |
| Meses con pedidos entregados | 23 |
| Tablas en SQLite | 8 |
| Pruebas | 9, todas pasan |

---

## 1. Fase 0: preparar el entorno

**Objetivo:** un entorno independiente, para que las bibliotecas del proyecto no se mezclen con las de otros proyectos.

**Terminal:** Bash de MSYS2 UCRT64 en Windows. Los comandos `Get-Location` y `Get-ChildItem` son de PowerShell y **no funcionan** en esta terminal; se usan `pwd` y `ls`.

### 1.1 Ubicarse y mirar

```bash
pwd                 # carpeta actual; debe terminar en Dashboard360
ls -la              # archivos y carpetas, incluidos los ocultos
ls data/raw         # comprobar que están los 9 CSV
```

### 1.2 Elegir la versión de Python

```bash
py -3.12 --version  # versión comprobada: Python 3.12.9
```

Primero se había creado un entorno con Python 3.14. Se decidió usar 3.12 para este proyecto.

### 1.3 Reemplazar el entorno inicial

```bash
deactivate                              # salir del entorno anterior
mv .venv .venv-python314-respaldo       # conservarlo con otro nombre
py -3.12 -m venv .venv                  # crear el definitivo
```

Un entorno virtual mantiene las dependencias del proyecto separadas del Python general. Estos comandos registran algo ya hecho: **no se repiten** cada vez que abres la terminal.

### 1.4 Activar el entorno (esto sí se repite en cada terminal nueva)

```bash
source .venv/Scripts/activate           # aparece (.venv) en el prompt
python --version
python -c "import sys; print(sys.executable)"   # debe estar dentro de Dashboard360/.venv
```

### 1.5 Instalar las dependencias iniciales y comprobarlas

```bash
python -m pip install pandas pytest
python -c "import pandas; import pytest; print('pandas:', pandas.__version__); print('pytest:', pytest.__version__)"
```

- `pandas` lee y transforma tablas; `pytest` ejecuta pruebas automáticas.
- `python -m pip` usa el instalador del Python seleccionado (evita instalar en otro intérprete).

### 1.6 Registrar las dependencias

```bash
python -m pip freeze > requirements.txt     # guarda las versiones instaladas
cat requirements.txt                        # ver el archivo
python -m pip install -r requirements.txt   # en un entorno nuevo, reinstala esas versiones
```

`>` guarda la salida en el archivo y **reemplaza** su contenido. `freeze` crea el registro; `install -r` lo usa.

### 1.7 Crear la estructura de carpetas

```bash
mkdir -p data/processed docs reports src tests   # crea las que falten, conserva las existentes
ls -d data/raw data/processed docs reports src tests
```

### 1.8 Crear `.gitignore`

```bash
cd /c/Users/favio/ProyectoDiplimadoPython/Dashboard360
cat > .gitignore <<'EOF'
# Entornos virtuales
.venv/
.venv-python314-respaldo/

# Archivos temporales de Python
__pycache__/
*.py[cod]

# Cache de pruebas
.pytest_cache/

# Secretos locales
.env

# Resultados generados
data/processed/*
reports/*
EOF
cat .gitignore      # comprobar
```

`cat > archivo <<'EOF' ... EOF` escribe en el archivo todo el texto hasta la palabra `EOF`. Las reglas le dicen a Git qué omitir; no borran nada.

### 1.9 Completar y verificar la instalación (26 de octubre de 2026)

La instalación manual terminó con `Operation cancelled by user`, así que se instalaron las versiones de `requirements.txt` directamente en `.venv`, con la ruta explícita al ejecutable (así se elige el entorno correcto aunque no esté activado):

```bash
./.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe -c "import sys,pandas,pytest; print('Python:',sys.version.split()[0]); print('Ejecutable:',sys.executable); print('pandas:',pandas.__version__); print('pytest:',pytest.__version__)"
./.venv/Scripts/python.exe -m pip check
```

Resultado: Python 3.12.9, pandas 3.1.0, pytest 9.1.1 y `No broken requirements found.` (`pip check` solo comprueba la compatibilidad de las dependencias; no prueba tu código).

También se comparó el contenido de los nueve CSV con `olist_raw.zip` del repositorio del curso mediante SHA-256: todos coinciden, es decir, los datos no están alterados.

### 1.10 Problemas de esta fase

| Síntoma | Causa | Solución |
|---|---|---|
| `command not found` | Se usaron comandos de PowerShell en Bash | Usar `pwd`, `ls` |
| `ModuleNotFoundError` (pandas) | Biblioteca no instalada en el intérprete usado | Instalar dentro del entorno del proyecto |
| `[200~ls -la .gitignore~: command not found` | Se pegaron caracteres extra | Escribir `ls -la .gitignore`; el archivo ya estaba bien |

---

## 2. Fase 1: explorar los datos

**Objetivo (Unidad 1):** leer al menos dos tablas, validar su calidad y generar un reporte básico. Se leen `orders` e `order_items`.

**Comando:**

```bash
python src/explorar_datos.py
```

Lee los CSV sin modificarlos y genera cuatro reportes en `reports/`. Cada ejecución **reemplaza** los reportes; no agrega filas.

### 2.1 Cómo se construyó, capa por capa

El script se fue **ampliando por capas**; cada capa se ejecutó y comprobó antes de pasar a la siguiente.

**Capa 1: inventario (filas, columnas, nulos, duplicados).** Conceptos usados:

- `Path(__file__).resolve().parents[1]` encuentra la raíz del proyecto desde el archivo guardado en `src`, sin escribir rutas personales.
- Un diccionario `archivos` relaciona nombre de tabla y archivo CSV; `resumen` es una lista a la que se agrega un diccionario de métricas por tabla.
- `pd.read_csv()` carga el CSV en un DataFrame; `len(datos)` son filas; `datos.isna().sum().sum()` cuenta celdas nulas; `datos.duplicated().sum()` cuenta filas completas repetidas.
- `pd.DataFrame(resumen).to_csv(..., index=False)` guarda el reporte sin columna de índice.
- `main()` organiza el trabajo y `if __name__ == "__main__":` lo llama solo si ejecutas el archivo directamente.

*`src/explorar_datos.py`, líneas 6–15*

```python
def main():
    """Lee pedidos e ítems y genera un inventario básico."""
    raiz = Path(__file__).resolve().parents[1]
    carpeta_datos = raiz / "data" / "raw"
    carpeta_reportes = raiz / "reports"

    archivos = {
        "orders": "olist_orders_dataset.csv",
        "order_items": "olist_order_items_dataset.csv",
    }
```


*`src/explorar_datos.py`, líneas 22–28*

```python
    resumen = []
    detalle_columnas = []
    tablas = {}

    for tabla, nombre_archivo in archivos.items():
        datos = pd.read_csv(carpeta_datos / nombre_archivo)
        tablas[tabla] = datos
```


*`src/explorar_datos.py`, líneas 41–54*

```python
        resumen.append({
            "tabla": tabla,
            "filas": len(datos),
            "columnas": len(datos.columns),
            "celdas_nulas": int(datos.isna().sum().sum()),
            "filas_duplicadas": int(datos.duplicated().sum()),
            "clave": " + ".join(columnas_clave),
            "filas_clave_nula":int(
                datos[columnas_clave].isna().any(axis=1).sum()
            ),
            "duplicados_clave": int(
                datos.duplicated(subset=columnas_clave).sum()
            ),     
        })
```


*`src/explorar_datos.py`, líneas 70–74*

```python
    reporte = pd.DataFrame(resumen)

    carpeta_reportes.mkdir(parents=True, exist_ok=True)
    salida = carpeta_reportes / "inventario_inicial.csv"
    reporte.to_csv(salida, index=False)
```


(Las tres últimas métricas del diccionario, `clave`, `filas_clave_nula` y `duplicados_clave`, se añadieron en la capa 3.)

Resultado de esa capa: `orders` 99.441 filas, 8 columnas, 4.908 celdas nulas; `order_items` 112.650 filas, 7 columnas, 0 nulos. Los 4.908 son **celdas**, no pedidos distintos.

**Capa 2: calidad por columna.** Se añadió la lista `detalle_columnas = []` y un segundo ciclo **dentro** del ciclo de tablas:

*`src/explorar_datos.py`, líneas 59–68*

```python
        for columna in datos.columns:
            detalle_columnas.append({
                "tabla": tabla,
                "columna": columna,
                "tipo_detectado": str(datos[columna].dtype),
                "celdas_nulas": int(datos[columna].isna().sum()),
                "porcentaje_nulos": round(
                    datos[columna].isna().mean() * 100, 2
                ),
            })
```


La lista se convierte en DataFrame y se guarda:

*`src/explorar_datos.py`, líneas 75–77*

```python
    detalle = pd.DataFrame(detalle_columnas)
    salida_detalle = carpeta_reportes / "calidad_por_columna.csv"
    detalle.to_csv(salida_detalle, index=False)
```


`isna()` da booleanos: su suma cuenta nulos y su media da la proporción (×100 y redondeo a 2 decimales). `dtype` es el tipo que pandas detectó al leer, no una validación de negocio (las fechas aparecen como texto).

Evidencia: `calidad_por_columna.csv` tiene 15 filas (8 de orders y 7 de order_items). Nulos relevantes: `order_approved_at` 160 (0,16 %), `order_delivered_carrier_date` 1.783 (1,79 %), `order_delivered_customer_date` 2.965 (2,98 %).

**Capa 3: validación de columnas clave.**

*`src/explorar_datos.py`, líneas 17–20*

```python
    claves ={
        "orders": ["order_id"],
        "order_items": ["order_id", "order_item_id"],
     }
```


*`src/explorar_datos.py`, líneas 30–39*

```python
        columnas_clave =claves[tabla]
        columnas_faltantes = [
            columna for columna in columnas_clave 
            if columna not in datos.columns
        ]

        if columnas_faltantes:
            raise ValueError(
                f"{tabla}: faltan columnas clave: {columnas_faltantes}"
            )
```


Cada pedido se identifica por `order_id`; cada ítem por `order_id` + `order_item_id`. Repetir `order_id` en ítems es normal. Los valores del diccionario son **listas** aunque tengan un solo elemento, para seleccionar columnas de forma uniforme. Al inventario se añadieron `clave`, `filas_clave_nula` y `duplicados_clave` (`any(axis=1)` busca filas con algún componente nulo; `subset=` limita `duplicated` a las columnas clave). Resultado: 0 nulos y 0 duplicados en ambas claves.

**Capa 4: relación entre pedidos e ítems.** Cada DataFrame se guardó en un diccionario `tablas = {}` para compararlos después del ciclo de lectura, y luego:

*`src/explorar_datos.py`, líneas 88–97*

```python
    pedidos = tablas["orders"]
    items = tablas["order_items"]

    pedidos_sin_items = int(
        (~pedidos["order_id"].isin(items["order_id"])).sum()
    )

    items_sin_pedido = int(
        (~items["order_id"].isin(pedidos["order_id"])).sum()
    )
```


`isin` pregunta si cada `order_id` existe en la otra tabla; `~` invierte los booleanos; `sum` cuenta los que no tienen correspondencia. Se comprueban **las dos direcciones** porque responden preguntas distintas. Resultado (`relacion_pedidos_items.csv`): 99.441 pedidos, **775 sin ítems**, 112.650 ítems, 0 ítems sin pedido.

**Capa 5: resumen por estado.**

*`src/explorar_datos.py`, líneas 113–122*

```python
    resumen_estados = (
    pedidos["order_status"]
    .value_counts(dropna=False)
    .rename_axis("estado")
    .reset_index(name="cantidad_pedidos")
    )

    resumen_estados["porcentaje"] = (
        resumen_estados["cantidad_pedidos"] / len(pedidos) * 100
    ).round(2)
```


`value_counts` cuenta pedidos por estado; `rename_axis` nombra el índice; `reset_index` lo convierte en columna. El denominador es el total de pedidos (99.441).

| Estado | Pedidos | % |
|---|---:|---:|
| delivered | 96.478 | 97,02 |
| shipped | 1.107 | 1,11 |
| canceled | 625 | 0,63 |
| unavailable | 609 | 0,61 |
| invoiced | 314 | 0,32 |
| processing | 301 | 0,30 |
| created | 5 | 0,01 |
| approved | 2 | 0,00 |

Los 2 `approved` existen aunque el porcentaje redondeado sea 0,00 %.

### 2.2 Reportes que genera

| Archivo | Filas de datos | Contenido |
|---|---:|---|
| `inventario_inicial.csv` | 2 | filas, columnas, nulos, duplicados, clave |
| `calidad_por_columna.csv` | 15 | tipo y nulos por columna |
| `relacion_pedidos_items.csv` | 1 | huérfanos en ambos sentidos |
| `resumen_pedidos_estado.csv` | 8 | pedidos por estado |

### 2.3 Errores que aparecieron aquí

| Error | Causa | Arreglo |
|---|---|---|
| `NameError` | Lista creada como `detalles_columnas` y usada como `detalle_columnas` | Unificar el nombre |
| Solo 7 filas en vez de 15 | El ciclo de columnas quedó **fuera** del ciclo de tablas (solo procesaba la última tabla) | Indentarlo dentro del ciclo |
| `SyntaxError: '(' was never closed` | Faltaba el paréntesis de `raise ValueError(...)` | Cerrar el paréntesis |
| `valueError` | Python distingue mayúsculas | `ValueError` |
| Letras en vez de columnas | `"orders": "order_id"` es texto | `"orders": ["order_id"]` es lista |
| `TypeError` | `tabla[tabla] = datos` intenta modificar un texto | `tablas[tabla] = datos` |
| `NameError: tablas` | Faltaba `tablas = {}` antes del ciclo | Crear el diccionario antes |

**Lección:** una ejecución sin excepciones no demuestra que el resultado sea correcto; hay que comprobar las tablas incluidas y los conteos (las 7 filas eran la pista).

**Nota:** este archivo tiene detalles de formato PEP 8 por ordenar (por ejemplo `claves ={`). No afecta los resultados.

---

## 3. Fase 2: primer ETL y SQLite

**Objetivo (Unidad 2):** pasar de explorar a transformar. Leer dos tablas, validar y convertir datos, usar `groupby` y `merge`, y guardar en SQLite de forma que **repetir la ejecución no duplique nada**.

**Archivos:** `src/etl.py` (lógica) y `pipeline.py` (punto de entrada; su versión final está en la Fase 5).

**Comando:**

```bash
python pipeline.py
```

No hace falta ejecutar antes `explorar_datos.py`: el ETL lee directamente `data/raw`.

**Reglas de negocio fijadas en esta fase:**

- Población comercial: pedidos con estado `delivered`.
- GMV = suma de **precios de productos, sin flete**. El flete va aparte. GMV no es utilidad.
- El mes se toma de la **fecha de compra**, no de la entrega.
- Ticket = GMV dividido por pedidos de la **misma población**.

### 3.1 `validar_clave`: la regla de entrada

*`src/etl.py`, líneas 8–14*

```python
def validar_clave(datos, columnas, nombre):
    """Exige una clave completa y única."""
    if datos[columnas].isna().any().any():
        raise ValueError(f"{nombre}: hay claves nulas.")

    if datos.duplicated(subset=columnas).any():
        raise ValueError(f"{nombre}: hay claves duplicadas.")
```


Detiene el proceso si la clave tiene nulos (`isna().any().any()`: el primer `any` por columna, el segundo sobre el resultado) o duplicados (`duplicated(subset=...)`). Es la función que más se reutiliza: aparece en `etl.py`, `indicadores.py` y `contexto.py`, y tiene 3 pruebas.

### 3.2 `transformar_pedidos`: una fila por pedido entregado

Se explica por bloques; los fragmentos son del archivo real.

**Bloque 1. Validaciones de entrada y relación.**

*`src/etl.py`, líneas 17–24*

```python
def transformar_pedidos(pedidos, items):
    """Construye una tabla con una fila por pedido entregado."""
    validar_clave(pedidos, ["order_id"], "orders")
    validar_clave(items, ["order_id", "order_item_id"], "order_items")

    # Todos los ítems deben pertenecer a un pedido existente.
    if not items["order_id"].isin(pedidos["order_id"]).all():
        raise ValueError("Hay ítems asociados a pedidos inexistentes.")
```


**Bloque 2. Copias y fecha de compra.** Se trabaja con `.copy()` para no alterar las tablas de entrada. `pd.to_datetime(..., errors="raise")` convierte el texto en fecha y **falla** si algo no es una fecha.

*`src/etl.py`, líneas 26–37*

```python
    # Trabajamos sobre copias para conservar las tablas de entrada.
    pedidos = pedidos.copy()
    items = items.copy()

    # Convertimos las fechas de compra a un tipo adecuado.
    pedidos["order_purchase_timestamp"] = pd.to_datetime(
        pedidos["order_purchase_timestamp"],
        errors="raise",
    )

    if pedidos["order_purchase_timestamp"].isna().any():
        raise ValueError("Hay pedidos sin fecha de compra.")
```


**Bloque 3. Importes válidos.** Numéricos (`to_numeric` con `raise`), sin nulos y sin negativos.

*`src/etl.py`, líneas 39–47*

```python
    # Los importes deben ser numéricos, completos y no negativos.
    for columna in ["price", "freight_value"]:
        items[columna] = pd.to_numeric(items[columna], errors="raise")

        if items[columna].isna().any():
            raise ValueError(f"{columna}: hay importes nulos.")

        if (items[columna] < 0).any():
            raise ValueError(f"{columna}: hay importes negativos.")
```


**Bloque 4. Alcance: solo entregados.** `.eq("delivered")` compara cada fila con el estado; `.loc[filtro, columnas]` selecciona filas y columnas a la vez.

*`src/etl.py`, líneas 49–56*

```python
    # Alcance comercial inicial: solo pedidos entregados.
    entregados = pedidos.loc[
        pedidos["order_status"].eq("delivered"),
        ["order_id", "order_purchase_timestamp"],
    ].copy()

    if entregados.empty:
        raise ValueError("No hay pedidos entregados para analizar.")
```


**Bloque 5. Agregar ítems ANTES de unir.** Esta es la regla central del proyecto: `groupby("order_id")` deja una fila por pedido con cantidad de ítems, GMV y flete (agregación con nombre: `columna_nueva=("columna_origen", "función")`).

*`src/etl.py`, líneas 58–66*

```python
    # Sumamos los ítems antes de unir: una fila por pedido.
    importes = (
        items.groupby("order_id", as_index=False)
        .agg(
            cantidad_items=("order_item_id", "count"),
            gmv=("price", "sum"),
            flete=("freight_value", "sum"),
        )
    )
```


**Bloque 6. Unir, comprobar y fijar tipos.** `validate="one_to_one"` hace que pandas **falle** si alguna de las dos tablas repite el `order_id`. Con `how="left"` los entregados sin ítems quedarían con nulos; por eso se comprueba y se rechaza. `to_period("M")` convierte la fecha en mes (`2017-11`) y `astype(str)` lo deja como texto.

*`src/etl.py`, líneas 68–89*

```python
    # La unión debe conservar una sola fila por pedido.
    resultado = entregados.merge(
        importes,
        on="order_id",
        how="left",
        validate="one_to_one",
    )

    if resultado["cantidad_items"].isna().any():
        raise ValueError("Hay pedidos entregados sin ítems.")

    resultado["cantidad_items"] = resultado["cantidad_items"].astype(int)
    resultado[["gmv", "flete"]] = resultado[["gmv", "flete"]].round(2)

    # El mes corresponde a la fecha de compra del pedido.
    resultado["mes_compra"] = (
        resultado["order_purchase_timestamp"]
        .dt.to_period("M")
        .astype(str)
    )

    return resultado
```


### 3.3 `resumir_por_mes`

*`src/etl.py`, líneas 92–112*

```python
def resumir_por_mes(pedidos):
    """Calcula indicadores mensuales sobre los pedidos preparados."""
    resumen = (
        pedidos.groupby("mes_compra", as_index=False)
        .agg(
            cantidad_pedidos=("order_id", "nunique"),
            cantidad_items=("cantidad_items", "sum"),
            gmv=("gmv", "sum"),
            flete=("flete", "sum"),
        )
    )

    # Numerador y denominador pertenecen a la misma población.
    resumen["ticket_promedio"] = (
        resumen["gmv"] / resumen["cantidad_pedidos"]
    )

    columnas_importes = ["gmv", "flete", "ticket_promedio"]
    resumen[columnas_importes] = resumen[columnas_importes].round(2)

    return resumen
```


- `nunique` cuenta pedidos distintos; `sum` suma ítems, GMV y flete.
- El ticket mensual divide el GMV del mes por los pedidos **de ese mismo mes**: numerador y denominador de la misma población.
- Por eso el ticket global (137,04) **no** es el promedio simple de los 23 tickets mensuales.

### 3.4 `ejecutar_etl`: leer, transformar, guardar

*`src/etl.py`, líneas 115–161*

```python
def ejecutar_etl(raiz):
    """Lee los CSV, transforma y guarda resultados en SQLite."""
    carpeta_raw = raiz / "data" / "raw"

    # Solo leemos las columnas necesarias para este primer ETL.
    pedidos = pd.read_csv(
        carpeta_raw / "olist_orders_dataset.csv",
        usecols=["order_id", "order_status", "order_purchase_timestamp"],
        dtype={"order_id": "string"},
    )

    items = pd.read_csv(
        carpeta_raw / "olist_order_items_dataset.csv",
        usecols=["order_id", "order_item_id", "price", "freight_value"],
        dtype={"order_id": "string"},
    )

    pedidos_preparados = transformar_pedidos(pedidos, items)
    resumen_mensual = resumir_por_mes(pedidos_preparados)

    carpeta_salida = raiz / "data" / "processed"
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    ruta_base = carpeta_salida / "dashboard360.sqlite"

    # Cada ejecución reemplaza las tablas de resultados.
    # No agregamos nuevamente los mismos pedidos.
    with sqlite3.connect(ruta_base) as conexion:
        pedidos_preparados.to_sql(
            "pedidos_entregados",
            conexion,
            if_exists="replace",
            index=False,
        )

        resumen_mensual.to_sql(
            "resumen_mensual",
            conexion,
            if_exists="replace",
            index=False,
        )

    print("\nETL completado.")
    print(f"Pedidos entregados: {len(pedidos_preparados):,}")
    print(f"GMV sin flete: {pedidos_preparados['gmv'].sum():,.2f}")
    print(f"Base SQLite: {ruta_base}")
    print("\nResumen mensual:")
    print(resumen_mensual.to_string(index=False))
```


Puntos para explicar:

- `usecols` lee solo las columnas necesarias; `dtype={"order_id": "string"}` fija el identificador como texto.
- `mkdir(parents=True, exist_ok=True)` crea la carpeta si falta y no falla si ya existe.
- **Idempotencia:** `to_sql(..., if_exists="replace")` reconstruye la tabla en cada ejecución. No se usa `append`, que sumaría de nuevo los mismos pedidos.
- `with sqlite3.connect(...) as conexion` confirma (commit) los cambios al salir si no hubo error. Ojo: el `with` de sqlite3 no cierra la conexión por sí solo.
- Limitación conocida: las dos tablas se reemplazan una a una, no en una sola transacción atómica. Si el proceso se corta a la mitad, puede quedar una mezcla. Se comprobó que repetir la ejecución no duplica; no se comprobó la recuperación ante un corte.

### 3.5 Comprobaciones en SQLite (modo solo lectura)

```sql
PRAGMA integrity_check;

SELECT name FROM sqlite_master WHERE type = 'table';

SELECT COUNT(*), COUNT(DISTINCT order_id),
       ROUND(SUM(gmv), 2), ROUND(SUM(flete), 2), SUM(cantidad_items)
FROM pedidos_entregados;

SELECT SUM(cantidad_pedidos), ROUND(SUM(gmv), 2),
       ROUND(SUM(flete), 2), SUM(cantidad_items)
FROM resumen_mensual;
```

| Tabla | Filas | Columnas | Nivel |
|---|---:|---:|---|
| `pedidos_entregados` | 96.478 | 6 | un pedido entregado |
| `resumen_mensual` | 23 | 6 | un mes de compra |

Resultados: integridad `ok`; 96.478 pedidos y 96.478 identificadores distintos; 110.197 ítems; GMV 13.221.498,11; flete 2.198.275,64; los totales mensuales coinciden con los de pedidos.

Un archivo SQLite es binario: si VS Code dice que no puede mostrarlo como texto, eso no indica corrupción. Se puede abrir con la extensión SQLite Viewer (la instaló el estudiante), con SQL o con Python.

### 3.6 Verificación de repetición

Se ejecutó el pipeline **dos veces** con las mismas entradas. Tras cada ejecución se abrió SQLite en solo lectura, se ordenaron las filas por sus claves y se compararon hashes **SHA-256 de los datos** (no de los bytes del archivo `.sqlite`, que pueden variar por su organización interna). Resultado: mismos conteos, mismo GMV (13.221.498,11), mismos hashes, integridad `ok`. Evidencia: `reports/verificacion_repeticion_etl.json`; después se amplió a las ocho tablas en `reports/verificacion_pipeline_completo.json`.

---

## 4. Fase 3: los cinco indicadores

**Objetivo:** añadir lo que pide el tema: ticket, satisfacción, entregas a tiempo y categorías, además del GMV. Se agrega `src/indicadores.py`, y `pipeline.py` pasa a llamar primero `ejecutar_etl` y luego `generar_indicadores`.

**Comando:** el mismo, `python pipeline.py`.

**Cómo se comunican las etapas:** `generar_indicadores` **lee de SQLite** la tabla `pedidos_entregados` que dejó la etapa anterior (no recibe un DataFrame por parámetro). Por eso el orden de las etapas importa.

**Definiciones (memorizar):**

| Indicador | Definición |
|---|---|
| GMV | Suma de precios de productos de pedidos entregados. Sin flete. No es utilidad. |
| Ticket promedio | GMV / pedidos de la misma población. |
| Satisfacción | Primero la media de reseñas **por pedido**; luego la media entre los pedidos con reseña. Cada pedido pesa igual. |
| Entregas a tiempo | Fecha real ≤ fecha estimada, comparando **días calendario**, sobre pedidos evaluables. |
| Categorías | Suma de precios por categoría (traducida si existe; si no, nombre original; si falta, `sin_categoria`). |

### 4.1 Recuperar la base y leer las fuentes

*`src/indicadores.py`, líneas 10–49*

```python
def generar_indicadores(raiz):
    """Amplía los resultados comerciales con los indicadores del tema."""
    carpeta_raw = raiz / "data" / "raw"
    ruta_base = raiz / "data" / "processed" / "dashboard360.sqlite"

    # Recuperamos los pedidos entregados preparados por el primer ETL.
    with sqlite3.connect(ruta_base) as conexion:
        base = pd.read_sql_query(
            "SELECT * FROM pedidos_entregados",
            conexion,
        )

    # Leemos las columnas necesarias de los archivos originales.
    fechas = pd.read_csv(
        carpeta_raw / "olist_orders_dataset.csv",
        usecols=[
            "order_id",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    )

    resenas = pd.read_csv(
        carpeta_raw / "olist_order_reviews_dataset.csv",
        usecols=["order_id", "review_score"],
    )

    items = pd.read_csv(
        carpeta_raw / "olist_order_items_dataset.csv",
        usecols=["order_id", "product_id", "price", "freight_value"],
    )

    productos = pd.read_csv(
        carpeta_raw / "olist_products_dataset.csv",
        usecols=["product_id", "product_category_name"],
    )

    traducciones = pd.read_csv(
        carpeta_raw / "product_category_name_translation.csv"
    )
```


### 4.2 Validar claves y reseñas

*`src/indicadores.py`, líneas 51–66*

```python
    validar_clave(fechas, ["order_id"], "fechas de pedidos")
    validar_clave(productos, ["product_id"], "productos")
    validar_clave(
        traducciones,
        ["product_category_name"],
        "traducciones",
    )

    # Las reseñas deben tener una puntuación válida entre 1 y 5.
    resenas["review_score"] = pd.to_numeric(
        resenas["review_score"],
        errors="raise",
    )

    if not resenas["review_score"].isin([1, 2, 3, 4, 5]).all():
        raise ValueError("Hay puntuaciones de reseña nulas o inválidas.")
```


Las puntuaciones deben ser numéricas y estar en {1, 2, 3, 4, 5}; si no, el proceso se detiene.

### 4.3 Satisfacción: promediar primero por pedido

*`src/indicadores.py`, líneas 68–76*

```python
    # Puede haber varias reseñas por pedido.
    # Primero calculamos una puntuación media por pedido.
    puntuaciones = (
        resenas.groupby("order_id", as_index=False)
        .agg(
            satisfaccion=("review_score", "mean"),
            cantidad_resenas=("review_score", "count"),
        )
    )
```


Hay 551 pedidos con más de una reseña. Si se promediaran las reseñas directamente, esos pedidos pesarían más que el resto. Promediar primero por pedido da a cada pedido el mismo peso.

### 4.4 Uniones que conservan una fila por pedido

*`src/indicadores.py`, líneas 78–94*

```python
    # Cada unión mantiene exactamente una fila por pedido.
    base = base.merge(
        fechas,
        on="order_id",
        how="left",
        validate="one_to_one",
    )

    base = base.merge(
        puntuaciones,
        on="order_id",
        how="left",
        validate="one_to_one",
    )

    # Los pedidos sin reseña se conservan sin inventar una puntuación.
    base["cantidad_resenas"] = base["cantidad_resenas"].fillna(0).astype(int)
```


Los pedidos sin reseña **se conservan**, con satisfacción nula (no se inventa una puntuación) y `cantidad_resenas = 0`.

### 4.5 Entregas a tiempo: días calendario y "no evaluable"

*`src/indicadores.py`, líneas 96–126*

```python
    columnas_fecha = [
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]

    for columna in columnas_fecha:
        base[columna] = pd.to_datetime(base[columna], errors="raise")

    # Comparamos días calendario: la fecha estimada viene a medianoche.
    real = base["order_delivered_customer_date"].dt.normalize()
    estimada = base["order_estimated_delivery_date"].dt.normalize()
    compra = base["order_purchase_timestamp"].dt.normalize()

    base["entrega_evaluable"] = (
        real.notna()
        & estimada.notna()
        & compra.notna()
        & real.ge(compra)
        & estimada.ge(compra)
    )

    # NaN significa no evaluable; no se registra como entrega atrasada.
    base["entrega_a_tiempo"] = float("nan")
    evaluables = base["entrega_evaluable"]

    base.loc[evaluables, "entrega_a_tiempo"] = (
        real.loc[evaluables]
        .le(estimada.loc[evaluables])
        .astype(float)
    )
```


- `dt.normalize()` deja solo la fecha (a medianoche). Se hace porque la fecha estimada viene a medianoche y la real trae hora; comparar con hora marcaría como atrasadas entregas del mismo día.
- Es **evaluable** el pedido con las tres fechas presentes y con entrega y estimación no anteriores a la compra. Los 8 no evaluables se guardan como `NaN`, **no** como atrasados.
- `entrega_a_tiempo` vale 1.0 o 0.0 solo en los evaluables; su media × 100 es el porcentaje.

### 4.6 Categorías

*`src/indicadores.py`, líneas 128–140*

```python
    # Conservamos categorías originales sin traducción.
    productos = productos.merge(
        traducciones,
        on="product_category_name",
        how="left",
        validate="many_to_one",
    )

    productos["categoria"] = (
        productos["product_category_name_english"]
        .fillna(productos["product_category_name"])
        .fillna("sin_categoria")
    )
```


`validate="many_to_one"`: muchas filas de productos pueden compartir traducción, pero cada categoría aparece una vez en la tabla de traducciones. La cadena `fillna` usa primero la traducción, luego el nombre original y por último `sin_categoria`.

*`src/indicadores.py`, líneas 142–172*

```python
    # Solo incluimos ítems de la misma población de pedidos entregados.
    items_entregados = items.merge(
        base[["order_id", "mes_compra"]],
        on="order_id",
        how="inner",
        validate="many_to_one",
    )

    items_entregados = items_entregados.merge(
        productos[["product_id", "categoria"]],
        on="product_id",
        how="left",
        validate="many_to_one",
    )

    if items_entregados["categoria"].isna().any():
        raise ValueError("Hay ítems sin correspondencia en productos.")

    categorias = (
        items_entregados.groupby("categoria", as_index=False)
        .agg(
            gmv=("price", "sum"),
            flete=("freight_value", "sum"),
            cantidad_items=("order_id", "size"),
            cantidad_pedidos=("order_id", "nunique"),
        )
        .sort_values("gmv", ascending=False)
        .reset_index(drop=True)
    )

    categorias[["gmv", "flete"]] = categorias[["gmv", "flete"]].round(2)
```


- Solo se incluyen ítems de pedidos entregados (`how="inner"`), la misma población del GMV.
- `size` cuenta filas (ítems); `nunique` cuenta pedidos distintos. **Los pedidos por categoría no son aditivos**: un pedido con productos de dos categorías cuenta en ambas. El GMV y los ítems sí se pueden sumar.

### 4.7 Reconciliar y armar la tabla de indicadores

*`src/indicadores.py`, líneas 174–209*

```python
    # Las ventas por categoría deben reconciliar con las ventas por pedido.
    gmv_total = round(float(base["gmv"].sum()), 2)
    gmv_categorias = round(float(categorias["gmv"].sum()), 2)

    if abs(gmv_total - gmv_categorias) > 0.005:
        raise ValueError("El GMV por categoría no coincide con el total.")

    cantidad_pedidos = len(base)
    cantidad_evaluable = int(evaluables.sum())

    porcentaje_a_tiempo = None
    if cantidad_evaluable:
        porcentaje_a_tiempo = round(
            base.loc[evaluables, "entrega_a_tiempo"].mean() * 100,
            2,
        )

    # Satisfacción: media de las puntuaciones medias por pedido.
    # Cada pedido con reseña tiene el mismo peso.
    satisfaccion = base["satisfaccion"].mean()

    kpis = pd.DataFrame([{
        "cantidad_pedidos": cantidad_pedidos,
        "gmv": gmv_total,
        "flete": round(float(base["flete"].sum()), 2),
        "ticket_promedio": round(gmv_total / cantidad_pedidos, 2),
        "satisfaccion_promedio": (
            round(float(satisfaccion), 2)
            if pd.notna(satisfaccion)
            else None
        ),
        "pedidos_con_resena": int(base["satisfaccion"].notna().sum()),
        "entregas_evaluables": cantidad_evaluable,
        "entregas_no_evaluables": cantidad_pedidos - cantidad_evaluable,
        "porcentaje_entregas_a_tiempo": porcentaje_a_tiempo,
    }])
```


- La **reconciliación** exige que la suma del GMV por categoría coincida con el GMV total, con tolerancia de medio centavo (0,005). Si no, se detiene.
- `None` y `pd.notna` evitan errores si no hubiera datos evaluables o reseñas.

### 4.8 Guardar

*`src/indicadores.py`, líneas 211–238*

```python
    # Estas tablas servirán como entradas del dashboard.
    with sqlite3.connect(ruta_base) as conexion:
        base.to_sql(
            "pedidos_dashboard",
            conexion,
            if_exists="replace",
            index=False,
        )

        categorias.to_sql(
            "ventas_categorias",
            conexion,
            if_exists="replace",
            index=False,
        )

        kpis.to_sql(
            "kpis_generales",
            conexion,
            if_exists="replace",
            index=False,
        )

    print("\nIndicadores generales:")
    print(kpis.to_string(index=False))

    print("\nCinco categorias con mayor GMV:")
    print(categorias.head(5).to_string(index=False))
```


Tablas nuevas: `pedidos_dashboard` (96.478 filas), `ventas_categorias` (74) y `kpis_generales` (1). Con las dos anteriores hay cinco tablas.

### 4.9 Resultados comprobados

| Métrica | Resultado |
|---|---:|
| GMV sin flete | 13.221.498,11 |
| Flete | 2.198.275,64 |
| Ticket promedio | 137,04 |
| Satisfacción promedio | 4,16 sobre 5 |
| Pedidos con reseña / sin reseña | 95.832 / 646 |
| Entregas evaluables / no evaluables | 96.470 / 8 |
| Entregas a tiempo | 89.936 (93,23 % de los evaluables) |

Las 74 categorías suman 13.221.498,11 de GMV y 110.197 ítems, igual que la base comercial. `sin_categoria` conserva 170.726,63 de GMV y 1.537 ítems. Las cinco categorías con más GMV: health_beauty, watches_gifts, bed_bath_table, sports_leisure y computers_accessories.

**Límites a recordar:** el 93,23 % usa días calendario, no timestamps; "entregado" no significa "a tiempo"; el ticket global no es el promedio de los tickets mensuales.

---

## 5. Fase 4: integrar las nueve tablas

**Objetivo:** que el proyecto use las nueve fuentes del dataset. Se agrega `src/contexto.py` (clientes, pagos, vendedores, geolocalización) y `pipeline.py` llama una tercera etapa.

**Comando:** `python pipeline.py`. Secuencia: `ejecutar_etl` → `generar_indicadores` → `incorporar_contexto`.

| Fuente | Aporte |
|---|---|
| orders | Estado, compra, fechas de entrega, relación con cliente |
| order_items | Ítems, GMV, flete, relación con producto y vendedor |
| order_reviews | Satisfacción por pedido |
| products | Categoría de cada producto |
| category_translation | Traducción de categoría |
| customers | Cliente, ciudad, estado y prefijo postal |
| order_payments | Total pagado por pedido y conciliación |
| sellers | Vendedor, ubicación y ventas |
| geolocation | Coordenadas aproximadas por prefijo postal |

### 5.1 Punto de partida y "fotografía" de control

*`src/contexto.py`, líneas 10–22*

```python
def incorporar_contexto(raiz):
    """Enriquece los pedidos conservando una fila por pedido."""
    carpeta_raw = raiz / "data" / "raw"
    ruta_base = raiz / "data" / "processed" / "dashboard360.sqlite"

    with sqlite3.connect(ruta_base) as conexion:
        base = pd.read_sql_query(
            "SELECT * FROM pedidos_dashboard",
            conexion,
        )

    cantidad_original = len(base)
    gmv_original = round(float(base["gmv"].sum()), 2)
```


Antes de unir nada se guardan el número de pedidos y el GMV. Al final se comprobará que **no cambiaron**.

### 5.2 Lecturas y validación de claves

*`src/contexto.py`, líneas 24–67*

```python
    # Recuperamos la relación entre pedido y cliente.
    pedidos_clientes = pd.read_csv(
        carpeta_raw / "olist_orders_dataset.csv",
        usecols=["order_id", "customer_id"],
    )

    clientes = pd.read_csv(
        carpeta_raw / "olist_customers_dataset.csv",
        dtype={"customer_zip_code_prefix": "string"},
    )

    vendedores = pd.read_csv(
        carpeta_raw / "olist_sellers_dataset.csv",
        dtype={"seller_zip_code_prefix": "string"},
    )

    pagos = pd.read_csv(
        carpeta_raw / "olist_order_payments_dataset.csv",
        usecols=["order_id", "payment_sequential", "payment_value"],
    )

    geografia = pd.read_csv(
        carpeta_raw / "olist_geolocation_dataset.csv",
        usecols=[
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
        ],
        dtype={"geolocation_zip_code_prefix": "string"},
    )

    items = pd.read_csv(
        carpeta_raw / "olist_order_items_dataset.csv",
        usecols=["order_id", "seller_id", "price", "freight_value"],
    )

    validar_clave(pedidos_clientes, ["order_id"], "pedidos_clientes")
    validar_clave(clientes, ["customer_id"], "clientes")
    validar_clave(vendedores, ["seller_id"], "vendedores")
    validar_clave(
        pagos,
        ["order_id", "payment_sequential"],
        "pagos",
    )
```


Los prefijos postales se leen como texto (`dtype="string"`) porque son identificadores, no números: un prefijo como `01037` perdería su cero inicial si se leyera como número.

### 5.3 Prefijos postales de cinco posiciones

*`src/contexto.py`, líneas 69–80*

```python
    # Los prefijos postales se tratan como texto de cinco posiciones.
    geografia["prefijo_postal"] = (
        geografia["geolocation_zip_code_prefix"].str.zfill(5)
    )

    clientes["customer_zip_code_prefix"] = (
        clientes["customer_zip_code_prefix"].str.zfill(5)
    )

    vendedores["seller_zip_code_prefix"] = (
        vendedores["seller_zip_code_prefix"].str.zfill(5)
    )
```


### 5.4 Coordenadas válidas y un punto por prefijo

*`src/contexto.py`, líneas 82–98*

```python
    # Excluimos coordenadas ausentes o fuera del rango mundial.
    latitud = pd.to_numeric(
        geografia["geolocation_lat"],
        errors="coerce",
    )
    longitud = pd.to_numeric(
        geografia["geolocation_lng"],
        errors="coerce",
    )

    coordenadas_validas = (
        latitud.between(-90, 90)
        & longitud.between(-180, 180)
    )

    geografia["geolocation_lat"] = latitud
    geografia["geolocation_lng"] = longitud
```


`to_numeric(errors="coerce")` convierte lo no numérico en nulo en vez de fallar; `between` deja solo latitudes en [-90, 90] y longitudes en [-180, 180].

*`src/contexto.py`, líneas 100–129*

```python
    # Varias coordenadas pueden corresponder al mismo prefijo.
    # Obtenemos un punto aproximado por prefijo antes de unir.
    puntos = (
        geografia.loc[
            coordenadas_validas,
            ["prefijo_postal", "geolocation_lat", "geolocation_lng"],
        ]
        .drop_duplicates()
        .groupby("prefijo_postal", as_index=False)
        .agg(
            latitud=("geolocation_lat", "mean"),
            longitud=("geolocation_lng", "mean"),
        )
    )

    clientes_geo = clientes.merge(
        puntos,
        left_on="customer_zip_code_prefix",
        right_on="prefijo_postal",
        how="left",
        validate="many_to_one",
    ).drop(columns="prefijo_postal")

    vendedores_geo = vendedores.merge(
        puntos,
        left_on="seller_zip_code_prefix",
        right_on="prefijo_postal",
        how="left",
        validate="many_to_one",
    ).drop(columns="prefijo_postal")
```


La geolocalización tiene muchas filas repetidas por prefijo (261.831 repetidas; 19.015 prefijos distintos). Se eliminan repeticiones exactas y se calcula la **media** de las coordenadas distintas por prefijo. El resultado es un punto **aproximado**, no un domicilio ni una verificación de que esté dentro de Brasil. Cliente y vendedor se unen con `many_to_one`; si no hay coordenadas, **no se elimina** al cliente ni al pedido.

### 5.5 Pagos: agregar primero

*`src/contexto.py`, líneas 131–150*

```python
    # Primero agregamos pagos: nunca unimos sus filas directamente
    # con ítems, porque eso podría multiplicar importes.
    pagos["payment_value"] = pd.to_numeric(
        pagos["payment_value"],
        errors="raise",
    )

    if pagos["payment_value"].isna().any():
        raise ValueError("Hay pagos con importe nulo.")

    if (pagos["payment_value"] < 0).any():
        raise ValueError("Hay pagos con importe negativo.")

    pagos_por_pedido = (
        pagos.groupby("order_id", as_index=False)
        .agg(
            total_pagado=("payment_value", "sum"),
            registros_pago=("payment_sequential", "count"),
        )
    )
```


Nunca se unen las filas de pagos directamente con las de ítems: un pedido con 3 pagos y 2 ítems daría 6 filas y multiplicaría los importes.

### 5.6 Unir a los pedidos y calcular la diferencia de pago

*`src/contexto.py`, líneas 152–179*

```python
    base = base.merge(
        pedidos_clientes,
        on="order_id",
        how="left",
        validate="one_to_one",
    )

    base = base.merge(
        clientes_geo,
        on="customer_id",
        how="left",
        validate="many_to_one",
    )

    if base["customer_unique_id"].isna().any():
        raise ValueError("Hay pedidos sin correspondencia en clientes.")

    base = base.merge(
        pagos_por_pedido,
        on="order_id",
        how="left",
        validate="one_to_one",
    )

    # Un pago ausente se conserva como nulo, no como cero.
    base["diferencia_pago"] = (
        base["total_pagado"] - base["gmv"] - base["flete"]
    ).round(2)
```


`diferencia_pago = total_pagado − gmv − flete`, redondeada a 2 decimales. Un pago ausente queda como nulo, **no** como cero (cero diría "se pagó nada", nulo dice "no hay dato").

### 5.7 Vendedores

*`src/contexto.py`, líneas 181–225*

```python
    # Ranking comercial de vendedores para pedidos entregados.
    if not items["seller_id"].isin(vendedores["seller_id"]).all():
        raise ValueError("Hay ítems con vendedores inexistentes.")

    items_entregados = items.loc[
        items["order_id"].isin(base["order_id"])
    ].copy()

    ventas_vendedores = (
        items_entregados.groupby("seller_id", as_index=False)
        .agg(
            gmv=("price", "sum"),
            flete=("freight_value", "sum"),
            cantidad_items=("order_id", "size"),
            cantidad_pedidos=("order_id", "nunique"),
        )
    )

    vendedores_dashboard = vendedores_geo.merge(
        ventas_vendedores,
        on="seller_id",
        how="left",
        validate="one_to_one",
    )

    # Un vendedor sin pedidos entregados tiene ventas elegibles cero.
    columnas_ventas = [
        "gmv",
        "flete",
        "cantidad_items",
        "cantidad_pedidos",
    ]

    vendedores_dashboard[columnas_ventas] = (
        vendedores_dashboard[columnas_ventas].fillna(0)
    )

    vendedores_dashboard[["gmv", "flete"]] = (
        vendedores_dashboard[["gmv", "flete"]].round(2)
    )

    for columna in ["cantidad_items", "cantidad_pedidos"]:
        vendedores_dashboard[columna] = (
            vendedores_dashboard[columna].astype(int)
        )
```


Solo cuentan ítems de pedidos entregados. Los vendedores sin ventas elegibles se conservan con cero (`fillna(0)`).

### 5.8 Controles de integridad y guardado

*`src/contexto.py`, líneas 227–239*

```python
    # Las uniones deben conservar los pedidos y su GMV.
    validar_clave(base, ["order_id"], "pedidos_dashboard")

    if len(base) != cantidad_original:
        raise ValueError("Cambió la cantidad de pedidos al integrar.")

    if abs(float(base["gmv"].sum()) - gmv_original) > 0.005:
        raise ValueError("Cambió el GMV al integrar.")

    if abs(
        float(vendedores_dashboard["gmv"].sum()) - gmv_original
    ) > 0.005:
        raise ValueError("El GMV por vendedor no coincide con el total.")
```


*`src/contexto.py`, líneas 241–279*

```python
    with sqlite3.connect(ruta_base) as conexion:
        base.to_sql(
            "pedidos_dashboard",
            conexion,
            if_exists="replace",
            index=False,
        )

        clientes_geo.to_sql(
            "clientes_geografia",
            conexion,
            if_exists="replace",
            index=False,
        )

        vendedores_dashboard.to_sql(
            "vendedores_dashboard",
            conexion,
            if_exists="replace",
            index=False,
        )

        puntos.to_sql(
            "geografia_postal",
            conexion,
            if_exists="replace",
            index=False,
        )

    print("\nContexto integrado: clientes, pagos, vendedores y geografia.")
    print(f"Pedidos conservados: {len(base):,}")
    print(f"Vendedores: {len(vendedores_dashboard):,}")
    print(f"Prefijos postales con coordenadas: {len(puntos):,}")
    print(f"Pedidos sin pago registrado: {base['total_pagado'].isna().sum()}")
    print(f"Pedidos sin coordenadas: {base['latitud'].isna().sum()}")
    print(
        "Pedidos con diferencia de pago superior a un centavo:",
        base["diferencia_pago"].abs().gt(0.01).sum(),
    )
```


Si cambia el número de pedidos o el GMV al integrar, el proceso falla. El GMV por vendedor también debe sumar el total.

### 5.9 Resultados comprobados

| Tabla SQLite | Filas |
|---|---:|
| `pedidos_entregados` | 96.478 |
| `resumen_mensual` | 23 |
| `pedidos_dashboard` | 96.478 |
| `ventas_categorias` | 74 |
| `kpis_generales` | 1 |
| `clientes_geografia` | 99.441 |
| `vendedores_dashboard` | 3.095 |
| `geografia_postal` | 19.015 |

Entre los pedidos **entregados**: 1 sin pago registrado, 264 sin coordenadas y 299 con diferencia de pago superior a un centavo. Esos 299 casos requieren investigación; una diferencia no demuestra fraude ni un error del GMV. Integridad de la base: `ok`. GMV conservado y GMV por vendedores: 13.221.498,11.

Repetición del pipeline completo: se tomó una instantánea lógica de las ocho tablas, se volvió a ejecutar todo y se compararon conteos y hashes (SHA-256 de los contenidos ordenados por clave). Evidencia: `reports/verificacion_pipeline_completo.json`.

**Nota para otra máquina:** al reproducir el pipeline con otra versión de pandas o de plataforma, las cuatro tablas con coordenadas pueden diferir en el decimal 1e-14 (promedios en coma flotante). Eso no es duplicación ni pérdida de datos; los conteos, el GMV y la integridad no cambian. Si comparas hashes exactos entre máquinas, redondea las coordenadas antes de comparar.

**Incidencia menor:** el estudiante pulsó Ctrl+C después de que el comando ya había terminado y regresado el prompt; la base estaba íntegra y completa.

### 5.10 Streamlit instalado

```bash
python -m pip install streamlit
python -m streamlit version                # Streamlit, version 1.66.1
python -m pip freeze > requirements.txt    # actualizar el registro
```

---

## 6. Fase 5: configuración, logging y punto de entrada

**Objetivo (Unidad 3):** que el pipeline sea configurable, deje un registro de lo que hace y falle de forma controlada.

### 6.1 `config/settings.json`

*`config/settings.json`, líneas 1–6*

```json
{
  "logging": {
    "level": "INFO",
    "file": "reports/pipeline.log"
  }
}
```


Se creó primero **un archivo llamado `config`**, cuando el código esperaba una **carpeta** `config/` con `settings.json` dentro. Se conservó el contenido y se movió a `config/settings.json`.

### 6.2 Cargar y validar la configuración

*`pipeline.py`, líneas 16–35*

```python
def cargar_configuracion(ruta):
    """Lee y valida la configuración externa del proyecto."""
    with ruta.open(encoding="utf-8") as archivo:
        configuracion = json.load(archivo)

    logging_config = configuracion.get("logging", {})
    nivel = logging_config.get("level")
    archivo_log = logging_config.get("file")

    niveles_validos = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

    if nivel not in niveles_validos:
        raise ValueError(
            "logging.level debe ser DEBUG, INFO, WARNING, ERROR o CRITICAL."
        )

    if not archivo_log:
        raise ValueError("Falta logging.file en config/settings.json.")

    return configuracion
```


`json.load` lee el archivo. Se valida que el nivel sea uno de los cinco válidos y que exista la ruta del log; si no, `ValueError` con un mensaje claro.

### 6.3 Configurar el logging

*`pipeline.py`, líneas 38–53*

```python
def configurar_logging(configuracion):
    """Escribe los registros en la terminal y en reports/pipeline.log."""
    ruta_log = RAIZ / configuracion["logging"]["file"]
    ruta_log.parent.mkdir(parents=True, exist_ok=True)

    formato = "%(asctime)s %(levelname)s %(name)s: %(message)s"

    logging.basicConfig(
        level=configuracion["logging"]["level"],
        format=formato,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(ruta_log, encoding="utf-8"),
        ],
        force=True,
    )
```


- Dos destinos a la vez: la terminal (`StreamHandler`) y el archivo `reports/pipeline.log` (`FileHandler`).
- `force=True` reemplaza cualquier configuración previa del logging.
- El formato muestra fecha, nivel, nombre del logger y mensaje.

### 6.4 `main`: etapas, errores y relanzamiento

*`pipeline.py`, líneas 56–86*

```python
def main():
    """Ejecuta el pipeline completo y registra errores."""
    try:
        configuracion = cargar_configuracion(RUTA_CONFIGURACION)
        configurar_logging(configuracion)
    except Exception:
        logging.basicConfig(level=logging.INFO)
        logging.exception("No se pudo cargar la configuración del pipeline.")
        raise

    logger = logging.getLogger("dashboard360")
    logger.info("Inicio del pipeline.")

    try:
        logger.info("Procesando pedidos e ítems.")
        ejecutar_etl(RAIZ)

        logger.info("Calculando los cinco indicadores.")
        generar_indicadores(RAIZ)

        logger.info("Integrando clientes, pagos y geolocalización.")
        incorporar_contexto(RAIZ)

        logger.info("Pipeline completado correctamente.")
    except Exception:
        logger.exception("El pipeline falló.")
        raise


if __name__ == "__main__":
    main()
```


- Primer `try`: si falla la configuración, se registra la excepción y se **relanza** (`raise`): no se oculta el error.
- Segundo `try`: ejecuta las tres etapas en orden. Si alguna falla, `logger.exception` guarda el mensaje **con el traceback** y `raise` hace que la ejecución termine con fallo.
- `if __name__ == "__main__":` permite ejecutar `python pipeline.py` directamente.

Registro real de una ejecución correcta (`reports/pipeline.log`, 27 de octubre de 2026, aproximadamente 10 segundos):

```text
2026-10-27 10:20:02,531 INFO dashboard360: Inicio del pipeline.
2026-10-27 10:20:02,531 INFO dashboard360: Procesando pedidos e ítems.
2026-10-27 10:20:07,481 INFO dashboard360: Calculando los cinco indicadores.
2026-10-27 10:20:09,013 INFO dashboard360: Integrando clientes, pagos y geolocalización.
2026-10-27 10:20:12,123 INFO dashboard360: Pipeline completado correctamente.
```

---

## 7. Fase 6: pruebas con pytest

**Objetivo:** la rúbrica pide al menos 3 pruebas por función de transformación. Se probaron las tres funciones puras de `src/etl.py`: `validar_clave`, `transformar_pedidos` y `resumir_por_mes` (3 × 3 = 9 pruebas).

**Comando:**

```bash
python -m pytest -v
```

**Idea clave:** las pruebas usan **tablas pequeñas creadas en memoria**. No leen los CSV reales ni tocan la base del proyecto, así que son rápidas y repetibles.

### 7.1 Datos de ejemplo

*`tests/test_etl.py`, líneas 13–32*

```python
def pedidos_ejemplo():
    """Crea dos pedidos pequeños para probar sin leer los CSV reales."""
    return pd.DataFrame({
        "order_id": ["pedido-1", "pedido-2"],
        "order_status": ["delivered", "shipped"],
        "order_purchase_timestamp": [
            "2020-01-10 10:00:00",
            "2020-02-05 12:00:00",
        ],
    })


def items_ejemplo():
    """Crea dos ítems pequeños asociados a los pedidos de ejemplo."""
    return pd.DataFrame({
        "order_id": ["pedido-1", "pedido-2"],
        "order_item_id": [1, 1],
        "price": [100.00, 50.00],
        "freight_value": [10.00, 5.00],
    })
```


### 7.2 Pruebas de `validar_clave`

*`tests/test_etl.py`, líneas 35–53*

```python
# Tres casos para validar claves: correcta, nula y repetida.
def test_validar_clave_acepta_clave_unica():
    datos = pd.DataFrame({"id": ["a", "b"]})

    validar_clave(datos, ["id"], "prueba")


def test_validar_clave_rechaza_nulos():
    datos = pd.DataFrame({"id": ["a", None]})

    with pytest.raises(ValueError, match="nulas"):
        validar_clave(datos, ["id"], "prueba")


def test_validar_clave_rechaza_duplicados():
    datos = pd.DataFrame({"id": ["a", "a"]})

    with pytest.raises(ValueError, match="duplicadas"):
        validar_clave(datos, ["id"], "prueba")
```


`pytest.raises(ValueError, match="nulas")` comprueba que se lance **ese** error y que su mensaje contenga esa palabra.

### 7.3 Pruebas de `transformar_pedidos`

*`tests/test_etl.py`, líneas 56–80*

```python
# Tres casos para transformar_pedidos.
def test_transformar_pedidos_incluye_solo_entregados():
    resultado = transformar_pedidos(
        pedidos_ejemplo(),
        items_ejemplo(),
    )

    assert resultado["order_id"].tolist() == ["pedido-1"]
    assert resultado.iloc[0]["gmv"] == 100.00


def test_transformar_pedidos_rechaza_item_sin_pedido():
    items = items_ejemplo()
    items.loc[0, "order_id"] = "pedido-inexistente"

    with pytest.raises(ValueError, match="inexistentes"):
        transformar_pedidos(pedidos_ejemplo(), items)


def test_transformar_pedidos_rechaza_precio_negativo():
    items = items_ejemplo()
    items.loc[0, "price"] = -1.00

    with pytest.raises(ValueError, match="negativos"):
        transformar_pedidos(pedidos_ejemplo(), items)
```


### 7.4 Pruebas de `resumir_por_mes`

*`tests/test_etl.py`, líneas 83–118*

```python
# Tres casos para resumir_por_mes.
def pedidos_preparados_ejemplo():
    """Crea pedidos ya agregados, con las columnas que usa el resumen."""
    return pd.DataFrame({
        "order_id": ["a", "b", "c"],
        "mes_compra": ["2020-01", "2020-01", "2020-02"],
        "cantidad_items": [1, 2, 1],
        "gmv": [100.00, 50.00, 90.00],
        "flete": [10.00, 5.00, 9.00],
    })


def test_resumir_por_mes_crea_un_registro_por_mes():
    resultado = resumir_por_mes(pedidos_preparados_ejemplo())

    assert resultado["mes_compra"].tolist() == ["2020-01", "2020-02"]


def test_resumir_por_mes_suma_pedidos_items_y_gmv():
    resultado = resumir_por_mes(pedidos_preparados_ejemplo())
    enero = resultado.loc[
        resultado["mes_compra"].eq("2020-01")
    ].iloc[0]

    assert enero["cantidad_pedidos"] == 2
    assert enero["cantidad_items"] == 3
    assert enero["gmv"] == 150.00


def test_resumir_por_mes_calcula_ticket_del_mismo_periodo():
    resultado = resumir_por_mes(pedidos_preparados_ejemplo())
    enero = resultado.loc[
        resultado["mes_compra"].eq("2020-01")
    ].iloc[0]

    assert enero["ticket_promedio"] == 75.00
```


### 7.5 Salida real de `python -m pytest -v`

```text
platform win32 -- Python 3.12.9, pytest-9.1.1, pluggy-1.7.0
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

**Brecha reconocida:** las reglas más delicadas (satisfacción por pedido, entrega a tiempo, categorías, pagos, geografía) están en `indicadores.py` y `contexto.py` y **no tienen pruebas propias**. Se validan en cada ejecución mediante las reconciliaciones (GMV, número de pedidos). Una mejora futura sería extraer funciones pequeñas y probarlas.

---

## 8. Fase 7: el dashboard

**Objetivo:** mostrar los resultados a una persona no técnica. Se usa Streamlit para la interfaz y Altair para los gráficos de barras.

**Comando:**

```bash
python -m streamlit run dashboard.py
```

Se abre en el navegador (por defecto en `http://localhost:8501`). Requiere haber ejecutado antes `python pipeline.py`, porque lee `data/processed/dashboard360.sqlite`.

> **Aviso:** los documentos `01` a `06` no registran paso a paso cómo se escribió `dashboard.py`. Esta sección explica el código final tal como está. Conviene que añadas con tus palabras en qué orden lo fuiste construyendo.

### 8.1 Configuración de la página

*`dashboard.py`, líneas 1–18*

```python
"""Dashboard ejecutivo sobre los resultados preparados en SQLite."""

import sqlite3
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


# Configuración general de la página.
st.set_page_config(
    page_title="Dashboard 360 | Olist",
    layout="wide",
)

RAIZ = Path(__file__).resolve().parent
RUTA_BASE = RAIZ / "data" / "processed" / "dashboard360.sqlite"
```


### 8.2 Formato numérico en español

*`dashboard.py`, líneas 21–27*

```python
def numero(valor, decimales=0):
    """Presenta números con separadores habituales en español."""
    if pd.isna(valor):
        return "Sin datos"

    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")
```


Python escribe `13,221,498.11`. La función cambia coma por punto y punto por coma usando `X` como marcador temporal para no confundirlos: `13.221.498,11`.

### 8.3 Cargar datos de forma segura y rápida

*`dashboard.py`, líneas 30–57*

```python
@st.cache_data(max_entries=2, show_spinner="Cargando resultados...")
def cargar_datos(ruta, version):
    """Lee una instantánea de resultados sin modificar SQLite."""
    # version contiene la fecha de modificación del archivo:
    # cuando cambia la base, cambia la clave de la caché.
    tablas = [
        "pedidos_dashboard",
        "resumen_mensual",
        "ventas_categorias",
        "vendedores_dashboard",
    ]

    with sqlite3.connect(
        Path(ruta).resolve().as_uri() + "?mode=ro",
        uri=True,
    ) as conexion:
        # Las consultas comparten una misma instantánea de lectura.
        conexion.execute("BEGIN")

        resultados = {
            tabla: pd.read_sql_query(
                f"SELECT * FROM {tabla}",
                conexion,
            )
            for tabla in tablas
        }

    return resultados
```


- `@st.cache_data`: Streamlit guarda el resultado. Si el usuario cambia un filtro, no relee la base.
- El parámetro `version` es la fecha de modificación del archivo (`st_mtime_ns`): si `pipeline.py` regenera la base, la clave cambia y la caché se invalida sola.
- `?mode=ro` abre SQLite en **solo lectura**: el dashboard no puede dañar los resultados.
- `BEGIN` hace que las cuatro lecturas vean la misma instantánea.

### 8.4 Indicadores sobre cualquier población

*`dashboard.py`, líneas 60–109*

```python
def mostrar_indicadores(pedidos):
    """Muestra métricas calculadas sobre la población recibida."""
    cantidad = len(pedidos)
    gmv = pedidos["gmv"].sum()
    satisfaccion = pedidos["satisfaccion"].mean()

    # Los valores nulos se excluyen del denominador de entregas.
    entregas = pedidos["entrega_a_tiempo"].dropna()
    porcentaje = entregas.mean() * 100 if len(entregas) else None

    columnas = st.columns(5)

    columnas[0].metric(
        "GMV sin flete",
        numero(gmv),
        help=f"Importe completo: {numero(gmv, 2)}",
        border=True,
    )
    columnas[1].metric(
        "Ticket promedio",
        numero(gmv / cantidad, 2),
        help="GMV dividido por pedidos de esta selección.",
        border=True,
    )
    columnas[2].metric(
        "Satisfacción",
        f"{numero(satisfaccion, 2)} / 5"
        if pd.notna(satisfaccion)
        else "Sin datos",
        border=True,
    )
    columnas[3].metric(
        "Entregas a tiempo",
        f"{numero(porcentaje, 2)} %"
        if porcentaje is not None
        else "Sin datos",
        border=True,
    )
    columnas[4].metric(
        "Pedidos entregados",
        numero(cantidad),
        border=True,
    )

    con_resena = int(pedidos["satisfaccion"].notna().sum())

    st.caption(
        f"Satisfacción: {numero(con_resena)} pedidos con reseña. "
        f"Entregas a tiempo: {numero(len(entregas))} pedidos evaluables."
    )
```


La misma función calcula los cinco indicadores para el periodo completo y para una selección filtrada. Los nulos de entregas se excluyen del denominador. Debajo se indica cuántos pedidos tienen reseña y cuántos son evaluables.

### 8.5 Gráfico de barras reutilizable

*`dashboard.py`, líneas 112–134*

```python
def grafico_barras(datos, categoria, valor, titulo_valor):
    """Construye barras horizontales ordenadas por valor."""
    return (
        alt.Chart(datos)
        .mark_bar(color="#1E40AF")
        .encode(
            x=alt.X(f"{valor}:Q", title=titulo_valor),
            y=alt.Y(
                f"{categoria}:N",
                sort="-x",
                title=None,
            ),
            tooltip=[
                alt.Tooltip(f"{categoria}:N", title="Grupo"),
                alt.Tooltip(
                    f"{valor}:Q",
                    title=titulo_valor,
                    format=",.2f",
                ),
            ],
        )
        .properties(height=340)
    )
```


### 8.6 `main`: validar, cargar y manejar errores

*`dashboard.py`, líneas 137–198*

```python
def main():
    """Organiza las vistas ejecutiva, exploratoria y de calidad."""
    st.title("Dashboard 360")
    st.write("Ventas, satisfacción y entregas de Olist.")

    if not RUTA_BASE.is_file():
        st.error(
            "No se encontró la base de resultados. "
            "Ejecuta primero: python pipeline.py"
        )
        st.stop()

    st.sidebar.header("Resultados del negocio")
    st.sidebar.caption(
        "Datos históricos. Los indicadores comerciales incluyen "
        "exclusivamente pedidos entregados."
    )

    if st.sidebar.button("Actualizar datos"):
        cargar_datos.clear()

    try:
        datos = cargar_datos(
            str(RUTA_BASE),
            RUTA_BASE.stat().st_mtime_ns,
        )
    except (sqlite3.Error, pd.errors.DatabaseError) as error:
        st.error(
            "No se pudieron leer las tablas. "
            "Ejecuta python pipeline.py para generar los resultados."
        )
        with st.expander("Detalle del error"):
            st.code(str(error))
        st.stop()

    pedidos = datos["pedidos_dashboard"]
    mensual = datos["resumen_mensual"].sort_values("mes_compra")
    categorias = datos["ventas_categorias"].sort_values(
        "gmv",
        ascending=False,
    )
    vendedores = datos["vendedores_dashboard"].sort_values(
        "gmv",
        ascending=False,
    )

    if pedidos.empty or mensual.empty:
        st.info("No hay pedidos entregados para mostrar.")
        st.stop()

    st.caption(
        f"Meses de compra: {mensual['mes_compra'].min()} "
        f"a {mensual['mes_compra'].max()}. "
        "Importes originales, sin conversión de moneda. "
        "El GMV excluye flete."
    )

    resumen, exploracion, calidad = st.tabs([
        "Resumen ejecutivo",
        "Explorar pedidos",
        "Calidad y definiciones",
    ])
```


- Si no existe la base, muestra un mensaje que dice qué ejecutar (`python pipeline.py`) y `st.stop()` detiene la página.
- El botón **Actualizar datos** limpia la caché.
- Si la lectura falla, muestra un error amigable y un detalle técnico plegable.

### 8.7 Las tres pestañas

| Pestaña | Contenido |
|---|---|
| **Resumen ejecutivo** | 5 indicadores; evolución mensual del GMV; categorías con más ventas (selector 5/10/15); distribución de la satisfacción (puntaje 1 a 5); entregas a tiempo por mes (se omiten meses con menos de 30 pedidos evaluables); tabla y descarga del resumen mensual; los 10 vendedores con más ventas |
| **Explorar pedidos** | Filtros por rango de meses y estado del cliente; los indicadores **se recalculan** con la selección; ventas por estado (gráfico, tabla y descarga). El resumen ejecutivo **no** cambia con estos filtros |
| **Calidad y definiciones** | Controles (sin reseña, no evaluables, sin pago, sin coordenadas, diferencias de pago) y cómo se interpreta cada indicador |

Fragmento de los filtros de la pestaña de exploración:

*`dashboard.py`, líneas 316–381*

```python
    # Los filtros de esta pestaña afectan solo a su contenido.
    with exploracion:
        st.subheader("Analizar pedidos por periodo y región")
        st.caption(
            "Los indicadores siguientes se recalculan con esta selección. "
            "El resumen ejecutivo conserva el periodo completo."
        )

        meses = sorted(pedidos["mes_compra"].dropna().unique().tolist())
        estados = sorted(
            pedidos["customer_state"].dropna().unique().tolist()
        )

        inicio, fin = st.select_slider(
            "Meses de compra",
            options=meses,
            value=(meses[0], meses[-1]),
        )

        estado = st.selectbox(
            "Estado del cliente",
            options=["Todos"] + estados,
        )

        seleccion = pedidos.loc[
            pedidos["mes_compra"].between(inicio, fin)
        ].copy()

        if estado != "Todos":
            seleccion = seleccion.loc[
                seleccion["customer_state"].eq(estado)
            ]

        if seleccion.empty:
            st.info("No hay pedidos para esta selección.")
        else:
            mostrar_indicadores(seleccion)

            por_estado = (
                seleccion.groupby("customer_state", as_index=False)
                .agg(
                    pedidos=("order_id", "nunique"),
                    gmv=("gmv", "sum"),
                )
                .sort_values("gmv", ascending=False)
            )

            st.subheader("Ventas por estado del cliente")
            st.altair_chart(
                grafico_barras(
                    por_estado,
                    "customer_state",
                    "gmv",
                    "GMV sin flete",
                ),
                width="stretch",
            )

            st.dataframe(por_estado, hide_index=True)

            st.download_button(
                "Descargar selección por estado",
                data=por_estado.to_csv(index=False).encode("utf-8-sig"),
                file_name="ventas_por_estado.csv",
                mime="text/csv",
            )
```


Las descargas usan `utf-8-sig` para que Excel abra bien los acentos.

### 8.8 Observaciones al revisar el dashboard

- Los meses de 2016 casi no tienen ventas en el gráfico mensual: la cobertura es parcial. Ya está avisado en el pie del gráfico.
- Las tarjetas usan formato español y el eje de algunos gráficos usa formato inglés. Es un detalle estético.

---

## 9. Fase 8: README, revisión y presentación

1. **README.md.** Debe explicar el caso, qué hace, cómo instalar, cómo ejecutar, salida de `pytest -v`, estructura, limitaciones y uso de IA.
2. **Revisión contra los requisitos** (documento de revisión). Compara el proyecto con la rúbrica: Funcionalidad 35 %, Calidad del código 30 %, Buenas prácticas 15 %, Presentación y valor de negocio 20 %. No es un paso de desarrollo; es una auditoría.
3. **Presentación** (`docs/presentacion/Dashboard360_presentacion.pptx`): 15 minutos más 5 de preguntas, con la plantilla del curso (9 diapositivas base). Pendiente por el estudiante: nombres de los integrantes y fecha en la portada.
4. **Ejecución de verificación.** El pipeline se ejecutó de nuevo en una copia aparte: terminó con "Pipeline completado correctamente", los indicadores fueron idénticos, las ocho tablas tuvieron las mismas filas, la integridad de SQLite fue `ok`, las 9 pruebas pasaron y las tres pestañas del dashboard cargaron sin excepciones.

---

## 10. Secuencia completa de comandos, de cero a dashboard

Si empiezas en una máquina nueva (con Python 3.12, los 9 CSV en `data/raw/` y la carpeta del proyecto):

```bash
# 1. Entrar al proyecto
cd /c/Users/favio/ProyectoDiplimadoPython/Dashboard360

# 2. Crear y activar el entorno
py -3.12 -m venv .venv
source .venv/Scripts/activate

# 3. Instalar dependencias del registro
python -m pip install -r requirements.txt
python -m pip check

# 4. Ejecutar el pipeline (≈ 10 s). Crea data/processed/dashboard360.sqlite y reports/pipeline.log
python pipeline.py

# 5. Ejecutar las pruebas
python -m pytest -v

# 6. Abrir el dashboard
python -m streamlit run dashboard.py
```

Opcional, para repetir la exploración: `python src/explorar_datos.py`.

Al abrir una terminal nueva solo hace falta `source .venv/Scripts/activate` y el comando que necesites.

---

## 11. Errores que aparecieron y qué enseñan

| Dónde | Error | Qué enseña |
|---|---|---|
| Entorno | Comandos de PowerShell en Bash | Conocer en qué terminal estás |
| Entorno | `ModuleNotFoundError` | Instalar dentro del entorno del proyecto; usar `python -m pip` |
| Entorno | `[200~` al pegar | Mirar el comando pegado antes de ejecutarlo |
| Entorno | Instalación cancelada | Usar la ruta explícita `./.venv/Scripts/python.exe` |
| Exploración | `NameError` por nombres distintos | Un nombre, un sitio |
| Exploración | Ciclo fuera del ciclo (7 filas en vez de 15) | Verificar conteos, no solo que corra |
| Exploración | `SyntaxError` / `valueError` | Cerrar paréntesis; Python distingue mayúsculas |
| Exploración | Lista vs texto en las claves | Una lista de un elemento no es un texto |
| Exploración | `TypeError` `tabla[tabla]` | No confundir el diccionario con la clave |
| Configuración | Archivo `config` en vez de carpeta `config/` | Rutas y nombres exactos |
| Terminal | Ctrl+C tras terminar | Esperar el prompt; la base seguía íntegra |
| Pruebas | Brecha: solo se prueba `etl.py` | Funciones pequeñas son más fáciles de probar |

---

## 12. Glosario

| Término | Significado |
|---|---|
| **GMV** | Valor bruto de mercancía: suma de precios de productos. Aquí, sin flete. No es utilidad |
| **Flete** | Costo de envío cobrado en el ítem; se reporta aparte |
| **Ticket promedio** | GMV / número de pedidos de la misma población |
| **ETL** | Extraer, transformar y cargar |
| **DataFrame** | Tabla en memoria de pandas |
| **`groupby` / `agg`** | Agrupar filas por una columna y resumirlas (suma, conteo, media) |
| **`merge`** | Unir dos tablas por una columna |
| **`validate=`** | Exige que la unión sea `one_to_one` o `many_to_one`; si no, falla |
| **Idempotente** | Ejecutar dos veces da el mismo resultado que una |
| **Reconciliar** | Comprobar que dos sumas que deberían coincidir, coinciden |
| **Evaluable** | Pedido con fechas válidas para decidir si llegó a tiempo |
| **Prefijo postal** | Los primeros dígitos del código postal; aquí, de cinco posiciones |
| **SHA-256** | Huella digital del contenido; si cambia un dato, cambia la huella |
| **`PRAGMA integrity_check`** | Revisión interna de SQLite; debe devolver `ok` |
| **Logging** | Registro con fecha y nivel de lo que hace el programa |
| **Caché** | Resultado guardado para no repetir un cálculo |

---

## 13. Qué faltaba en los documentos originales

Para que sepas qué cubre esta guía y qué sigue siendo tu tarea:

| Hueco en los documentos originales `01`–`06` | Cómo se cubre aquí |
|---|---|
| No incluyen el código de `etl.py`, `indicadores.py`, `contexto.py` ni `pipeline.py`: solo describen lo que hacen | Fases 2 a 5 con el código literal, por bloques |
| No hay ninguna etapa sobre `dashboard.py` | Fase 7 explica el código final. **El orden real en que lo escribiste no está registrado:** añádelo tú |
| El comando `python -m streamlit run dashboard.py` no aparece en `docs/` (solo en el README) | Fase 7 y sección 10 |
| `03`, `04` y `05` listan como "pendientes" cosas que `06` ya resolvió (dashboard, logging, pruebas, README) | En esta guía el estado está actualizado |
| No muestran la salida completa de `pytest -v` (`06` solo dice 9 passed) | Sección 7.5 |
| La primera versión de `pipeline.py` y de `etl.py` no se conservó: los documentos describen su lógica, no su texto | Se muestra la versión final; la lógica coincide con lo descrito |
| No hay glosario ni secuencia única de comandos | Secciones 10 y 12 |

**No se modificó ningún documento original.**
