# Exploración inicial de pedidos e ítems

## Objetivo y relación con la guía

Iniciar la Unidad 1 del proyecto con lectura de dos tablas y un reporte
básico de calidad. Se consultaron las secciones 6 y 7 de
`Guia_desarrollo_Dashboard_360_Olist.docx`, ubicada en esta carpeta docs,
y el encargo `proyecto-integrador.md`.

## Trabajo realizado y comprobado

El estudiante creó `src/explorar_datos.py`. Codex revisó el código
guardado y el archivo `reports/inventario_inicial.csv`, que ya existía
al comenzar la revisión. No se atribuye a Codex la ejecución del estudiante.

El script lee los archivos originales sin modificarlos:

- `data/raw/olist_orders_dataset.csv`.
- `data/raw/olist_order_items_dataset.csv`.

## Ejecución

Desde Dashboard360, en Bash, con el entorno virtual activo:

```bash
python src/explorar_datos.py
```

Si la terminal no tiene el entorno activado, la activación es:

```bash
source .venv/Scripts/activate
```

Activar el entorno selecciona su intérprete para el comando `python`.
No reinstala bibliotecas.

## Explicación del código existente

- `Path` permite construir rutas de archivos.
- `Path(__file__).resolve().parents[1]` encuentra Dashboard360 a partir
  del archivo guardado en src, sin fijar una ruta personal.
- El diccionario `archivos` relaciona nombres de tablas con archivos CSV.
- `resumen` es una lista que acumula un diccionario de métricas por tabla.
- `for tabla, nombre_archivo in archivos.items()` recorre ambas entradas.
- `pd.read_csv()` carga un CSV en un DataFrame, una tabla en memoria.
- `len(datos)` cuenta filas y `len(datos.columns)` cuenta columnas.
- `datos.isna().sum().sum()` cuenta celdas nulas en toda la tabla.
- `datos.duplicated().sum()` cuenta filas completamente repetidas
  después de la primera aparición; todavía no valida claves de negocio.
- `pd.DataFrame(resumen)` convierte la lista de resultados en una tabla.
- `mkdir(..., exist_ok=True)` conserva la carpeta de reportes si existe.
- `to_csv(..., index=False)` guarda el inventario sin una columna de índice.
- `main()` organiza el trabajo. El bloque `if __name__ == "__main__"`
  llama a la función cuando se ejecuta directamente el archivo.

## Resultados verificados

Contenido del reporte existente:

```csv
tabla,filas,columnas,celdas_nulas,filas_duplicadas
orders,99441,8,4908,0
order_items,112650,7,0,0
```

Los 4908 nulos son celdas, no necesariamente 4908 pedidos diferentes.
No se eliminaron registros. Un nulo necesita interpretación según
la columna y el estado del pedido.

Repetir este script reemplaza el archivo del inventario. No agrega
filas al reporte ni modifica los CSV de entrada.

## Ampliación comprobada de calidad por columna

El estudiante añadió `detalle_columnas = []` y un segundo ciclo dentro
del ciclo de tablas. Codex revisó el archivo guardado y comprobó el
reporte generado tras la ejecución compartida por el estudiante.

El comando de ejecución se mantiene:

```bash
python src/explorar_datos.py
```

### Funcionamiento

```python
for columna in datos.columns:
    detalle_columnas.append({
        "tabla": tabla,
        "columna": columna,
        "tipo_detectado": str(datos[columna].dtype),
        "celdas_nulas": int(datos[columna].isna().sum()),
        "porcentaje_nulos": round(datos[columna].isna().mean() * 100, 2),
    })
```

Este fragmento corresponde al ciclo interno: en el archivo real está
indentado dentro del ciclo que recorre las tablas. Por cada tabla,
registra el nombre de cada columna, el tipo inferido por pandas, sus
nulos y el porcentaje de nulos sobre las filas de esa tabla.

`isna()` produce valores booleanos. Su suma cuenta nulos; su media
calcula la proporción, que se multiplica por 100 y se redondea a dos
decimales. `dtype` refleja el tipo detectado al leer, no una validación
del tipo de negocio. Las fechas todavía aparecen como texto (`str`).

La lista se convierte en DataFrame y se guarda mediante:

```python
detalle = pd.DataFrame(detalle_columnas)
salida_detalle = carpeta_reportes / "calidad_por_columna.csv"
detalle.to_csv(salida_detalle, index=False)
```

### Evidencias verificadas

- `reports/calidad_por_columna.csv`: 15 filas de datos, ocho de orders
  y siete de order_items.
- `order_approved_at`: 160 nulos (0,16 %).
- `order_delivered_carrier_date`: 1783 nulos (1,79 %).
- `order_delivered_customer_date`: 2965 nulos (2,98 %).
- Las demás columnas de estas dos tablas no presentan nulos.
- La suma de nulos por columna coincide con el inventario: 4908 para
  orders y cero para order_items.
- El inventario mantiene los conteos originales de filas y columnas.

### Errores corregidos y aprendizaje

1. La lista se había creado como `detalles_columnas` y se utilizaba
   como `detalle_columnas`, lo que provocó `NameError`. Se unificó
   el nombre en `detalle_columnas`.
2. El ciclo de columnas estaba fuera del ciclo de tablas. El programa
   terminaba, pero solo generaba siete filas de order_items, la última
   tabla leída. Se indentó todo el ciclo interno cuatro espacios más,
   y ahora se obtienen las quince filas esperadas.

Una ejecución sin excepciones no basta para demostrar que el resultado
es correcto: también se deben comprobar las tablas incluidas y sus
conteos. No se eliminaron nulos ni se modificaron datos originales.

## Validación de columnas clave

El estudiante incorporó las definiciones y ejecutó el script. Codex
comprobó el código guardado y el inventario actualizado.

### Definición

```python
claves = {
    "orders": ["order_id"],
    "order_items": ["order_id", "order_item_id"],
}
```

Cada pedido se identifica por `order_id`. Cada ítem se identifica por
la combinación de pedido y número de ítem. Repetir `order_id` en ítems
es válido: un pedido puede contener varios ítems.

Los valores del diccionario son listas incluso cuando contienen una
única columna. Así se pueden seleccionar columnas de forma uniforme.

### Comprobaciones incorporadas

```python
columnas_clave = claves[tabla]
columnas_faltantes = [
    columna for columna in columnas_clave
    if columna not in datos.columns
]

if columnas_faltantes:
    raise ValueError(
        f"{tabla}: faltan columnas clave: {columnas_faltantes}"
    )
```

Este bloque está dentro del ciclo de tablas. Detiene la ejecución si
falta una columna clave. Todavía no comprueba todas las columnas del
esquema esperado.

Las nuevas métricas guardadas en cada fila del inventario son:

```python
"clave": " + ".join(columnas_clave),
"filas_clave_nula": int(
    datos[columnas_clave].isna().any(axis=1).sum()
),
"duplicados_clave": int(
    datos.duplicated(subset=columnas_clave).sum()
),
```

- `any(axis=1)` identifica las filas con algún componente nulo en la clave.
- `subset` limita la detección de duplicados a las columnas clave.
- `duplicated` cuenta las apariciones posteriores a la primera.
- Estos dos conteos se reportan: el código todavía no detiene la
  ejecución por claves nulas o repetidas.

### Resultado verificado

Comando utilizado por el estudiante:

```bash
python src/explorar_datos.py
```

| Tabla | Clave | Filas con clave nula | Duplicados de clave |
|---|---|---:|---:|
| orders | order_id | 0 | 0 |
| order_items | order_id + order_item_id | 0 | 0 |

El inventario conserva los conteos anteriores y añade estas métricas.

### Correcciones realizadas durante el aprendizaje

- Se añadió el paréntesis de cierre de `raise ValueError(...)`, cuya
  ausencia causaba `SyntaxError: '(' was never closed`.
- Se corrigió `valueError` a `ValueError`: Python distingue mayúsculas.
- Se cambió `"orders": "order_id"` por `"orders": ["order_id"]`.
  Recorrer el texto directamente habría recorrido sus letras.

## Relación entre pedidos e ítems comprobada

El estudiante conservó las tablas leídas en un diccionario para poder
compararlas después del ciclo de lectura:

```python
tablas = {}
```

Dentro del ciclo de lectura se guardó cada DataFrame:

```python
datos = pd.read_csv(carpeta_datos / nombre_archivo)
tablas[tabla] = datos
```

`tablas` es el diccionario; `tabla` es el nombre de la entrada actual,
por ejemplo `orders`. No son variables intercambiables.

Tras leer ambas tablas se recuperan sus DataFrames:

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

`isin` comprueba pertenencia a la otra tabla; `~` invierte los booleanos
y `sum` cuenta los casos sin correspondencia. Se comprueban ambas
direcciones porque responden preguntas distintas. No se realiza un merge.

El estudiante ejecutó:

```bash
python src/explorar_datos.py
```

Codex revisó el archivo y el reporte guardado. Resultado:

```csv
pedidos_totales,pedidos_sin_items,items_totales,items_sin_pedido
99441,775,112650,0
```

Salida: `reports/relacion_pedidos_items.csv`, una fila de datos y
cuatro columnas. Se reemplaza al ejecutar nuevamente el script.

### Interpretación

- Hay 775 pedidos sin registros asociados en order_items.
- Todos los ítems hacen referencia a un pedido presente en orders.
- Los pedidos sin ítems no se eliminan ni se consideran automáticamente
  errores: queda pendiente relacionarlos con sus estados y contexto.
- Estas comprobaciones no calculan ventas ni multiplican registros.

### Errores corregidos

- `tabla[tabla] = datos` intentaba modificar un texto y causó `TypeError`.
  Se corrigió a `tablas[tabla] = datos`.
- Faltaba `tablas = {}` antes del ciclo, lo que causó `NameError`.
  Se creó el diccionario antes de utilizarlo.

### Tamaños de los reportes comprobados hasta este paso

Sin contar encabezados como filas:

| Reporte | Filas de datos | Columnas |
|---|---:|---:|
| inventario_inicial.csv | 2 | 8 |
| calidad_por_columna.csv | 15 | 5 |
| relacion_pedidos_items.csv | 1 | 4 |

## Resumen básico de pedidos por estado

El estudiante añadió el resumen, ejecutó el script y generó
`reports/resumen_pedidos_estado.csv`. Codex verificó el archivo:
ocho filas, tres columnas, estados únicos y 99441 pedidos en total.

### Alcance

Incluye todos los registros de orders, sin filtrar por fecha ni estado.
Cada fila de orders representa un pedido, según la clave comprobada.
Este resumen describe el estado registrado en el dataset histórico;
no mide ventas actuales ni permite interpretar estados pendientes
como pedidos que siguen abiertos hoy.

### Código y explicación

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

salida_estados = carpeta_reportes / "resumen_pedidos_estado.csv"
resumen_estados.to_csv(salida_estados, index=False)
```

- `value_counts` cuenta pedidos por estado. `dropna=False` incluiría
  también estados nulos, en caso de existir.
- `rename_axis` asigna el nombre estado al índice del conteo.
- `reset_index` convierte el resultado en una tabla de columnas normales.
- El denominador de cada porcentaje es el total de pedidos: 99441.
- `round(2)` redondea los porcentajes a dos decimales.
- El reporte se reemplaza al ejecutar nuevamente el script.

Comando utilizado por el estudiante:

```bash
python src/explorar_datos.py
```

### Resultados comprobados

| Estado | Pedidos | Porcentaje |
|---|---:|---:|
| delivered | 96478 | 97,02 % |
| shipped | 1107 | 1,11 % |
| canceled | 625 | 0,63 % |
| unavailable | 609 | 0,61 % |
| invoiced | 314 | 0,32 % |
| processing | 301 | 0,30 % |
| created | 5 | 0,01 % |
| approved | 2 | 0,00 % |

Los dos pedidos approved existen aunque su porcentaje redondeado sea
0,00 %. Una diferencia mínima de representación binaria al sumar
porcentajes con float no equivale a una pérdida de pedidos.

### Interpretación de negocio

El 97,02 % de los pedidos del archivo figura como entregado.
Este dato ofrece contexto para definir posteriormente la población
del GMV y los indicadores de entregas. No es por sí mismo una tasa
de entrega a tiempo: aún no se comparan fechas reales y estimadas.

## Estado y límites

Lectura, inventario, calidad por columna, claves, correspondencia entre
las dos tablas y resumen básico por estado comprobados.
Unidad 1: núcleo técnico terminado, conforme al encargo oficial:
lectura de al menos dos tablas, validación de calidad y reporte básico.
Se comprobaron el script y los cuatro reportes guardados.

Mejoras para las siguientes etapas, sin bloquear el cierre técnico
de la Unidad 1:

- Validación del resto de las columnas requeridas de cada tabla.
- Valores y fechas inválidos pertinentes al reporte.
- Inspección documentada de las demás tablas al ampliar el ETL.

La ficha de integrantes queda como pendiente administrativo separado.
La guía propone comprobaciones adicionales; no todas son condiciones
del encargo oficial para cerrar la primera entrega.

No se han desarrollado el ETL completo, SQLite, dashboard ni los KPIs
definitivos. Los cambios futuros solo se registrarán como realizados
después de comprobar el código y sus salidas.
