# Primer ETL comercial y persistencia en SQLite

## Estado

Unidad 2: núcleo técnico terminado. Se verificaron lectura de dos tablas,
validación y conversión de datos, groupby, merge y persistencia SQLite
reproducible sin duplicaciones. El alcance completo Dashboard 360 sigue
en desarrollo: todavía no están todos los indicadores ni las nueve tablas.

## Archivos implementados por el estudiante

- `pipeline.py`: punto de entrada; encuentra la raíz y llama al ETL.
- `src/etl.py`: lectura, validaciones, transformaciones y escritura.

El estudiante ejecutó el pipeline y compartió la salida. Codex revisó
ambos archivos y abrió la base en modo de solo lectura para comprobarla.

## Ejecución

Desde Dashboard360, en Bash con el entorno activo:

```bash
python pipeline.py
```

No hace falta ejecutar previamente `src/explorar_datos.py`: el ETL
lee directamente los archivos originales de `data/raw`.

## Entradas y alcance

- `olist_orders_dataset.csv`: identificador, estado y fecha de compra.
- `olist_order_items_dataset.csv`: pedido, ítem, precio y flete.

Población comercial: pedidos con estado `delivered`.
GMV inicial: suma de precios de productos, sin flete.
Flete: importe separado. No se interpreta GMV como utilidad.
Agrupación temporal: mes de compra, no mes de entrega.
La moneda todavía requiere confirmación documental.

## Funciones y pasos

1. `validar_clave`: detiene el proceso por claves nulas o duplicadas.
2. `transformar_pedidos`: comprueba correspondencia de ítems, copia las
   tablas, convierte fechas e importes, rechaza nulos y valores negativos
   en importes y selecciona pedidos entregados.
3. `groupby` agrega ítems por pedido antes de integrar los datos.
4. `merge(..., validate="one_to_one")` conserva una fila por pedido
   entregado. Se rechazan pedidos entregados sin ítems.
5. `resumir_por_mes`: suma pedidos, ítems, GMV y flete por mes; calcula
   ticket como GMV mensual dividido por pedidos de esa misma población.
6. `ejecutar_etl`: coordina la lectura y guarda las dos tablas con
   `to_sql(..., if_exists="replace", index=False)`.

`replace` reconstruye las tablas de resultados en cada ejecución.
No se utiliza una carga acumulativa. Se verificó empíricamente que dos
ejecuciones con las mismas entradas conservan los resultados.
La sustitución conjunta de ambas tablas no está implementada como
una actualización atómica: es una mejora pendiente de robustez.

## Salida comprobada

Base: `data/processed/dashboard360.sqlite`.

| Tabla | Filas | Columnas | Nivel |
|---|---:|---:|---|
| pedidos_entregados | 96478 | 6 | Un pedido entregado |
| resumen_mensual | 23 | 6 | Un mes de compra con pedidos entregados |

Comprobaciones realizadas en modo de solo lectura:

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

Resultados:

- Integridad SQLite: `ok`.
- Pedidos: 96478; identificadores distintos: 96478.
- Ítems de pedidos entregados: 110197.
- GMV sin flete: 13221498,11.
- Flete: 2198275,64.
- Los totales mensuales coinciden con los totales de la tabla de pedidos.

## Cómo interpretar el archivo SQLite

SQLite guarda varias tablas en un archivo binario. No se visualiza como
texto CSV. Si VS Code avisa que no puede mostrarlo como texto, ese aviso
no demuestra corrupción. La base revisada pasó `integrity_check`.
Las tablas se consultan con SQL, un visor de SQLite o Python.

## Verificación de repetición realizada

Codex ejecutó `pipeline.py` dos veces con el Python de `.venv`.
Después de cada ejecución abrió SQLite en modo de solo lectura,
ordenó las filas por sus claves y comparó hashes SHA-256 de sus
contenidos serializados. Se compararon datos, no los bytes del archivo
SQLite, que pueden variar por su organización interna.

| Comprobación | Ejecución 1 | Ejecución 2 |
|---|---:|---:|
| Pedidos entregados | 96478 | 96478 |
| Pedidos distintos | 96478 | 96478 |
| Filas mensuales | 23 | 23 |
| GMV sin flete | 13221498,11 | 13221498,11 |
| Integridad | ok | ok |

Los hashes de ambas tablas coincidieron entre ejecuciones.
Evidencia guardada: `reports/verificacion_repeticion_etl.json`.
La prueba corresponde a las entradas actuales, sin fallos inducidos.

## Visualización instalada por el estudiante

El estudiante instaló SQLite Viewer y compartió una captura donde
se ven ambas tablas y los 96478 registros de pedidos. El visor permite
inspeccionar el archivo binario desde VS Code. Si muestra datos en caché
después de ejecutar el ETL, se debe actualizar la vista o reabrirla.

## Pendientes

- Ampliar el ETL progresivamente a las tablas necesarias para Dashboard 360.
- Incorporar configuración, logging, pruebas y manejo de errores de la
  siguiente unidad antes de considerar completo el producto final.
