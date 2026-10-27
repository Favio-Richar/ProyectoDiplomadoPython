# Integración de las nueve tablas de Olist

## Estado

Unidad 2 terminada para el alcance de integración implementado:
ETL con pandas, limpieza, merge, groupby y persistencia SQLite
reproducible sin duplicaciones. El proyecto final aún requiere
visualización ejecutiva, configuración, logging, pruebas y entrega.

El estudiante creó `src/contexto.py`, actualizó `pipeline.py` y ejecutó
el proceso. Codex revisó los archivos y verificó la base resultante.

## Comando y secuencia

Desde Dashboard360, en Bash con el entorno virtual activo:

```bash
python pipeline.py
```

1. `ejecutar_etl`: prepara pedidos entregados y resumen mensual.
2. `generar_indicadores`: calcula satisfacción, entregas y categorías.
3. `incorporar_contexto`: integra clientes, pagos, vendedores y geografía.

La exploración no necesita ejecutarse previamente.

## Aporte de las nueve fuentes

| Fuente | Aporte implementado |
|---|---|
| orders | Estado, compra, fechas de entrega y relación con cliente |
| order_items | Ítems, GMV, flete y relación con producto y vendedor |
| order_reviews | Satisfacción por pedido |
| products | Categoría de cada producto |
| category_translation | Traducción cuando está disponible |
| customers | Identidad de cliente, ciudad, estado y prefijo postal |
| order_payments | Total pagado por pedido y conciliación |
| sellers | Identidad, ubicación y ventas elegibles por vendedor |
| geolocation | Coordenadas aproximadas por prefijo postal |

## Reglas de integración

- Los prefijos postales se leen como texto y se normalizan a cinco
  posiciones con `str.zfill(5)`.
- Coordenadas no numéricas, ausentes o fuera de los rangos mundiales
  de latitud y longitud se excluyen del cálculo de puntos.
- Se eliminan repeticiones de la combinación prefijo y coordenadas
  y se calcula la media de coordenadas distintas por prefijo.
  El resultado es un punto aproximado, no un domicilio exacto ni
  una validación de que toda coordenada esté dentro de Brasil.
- Clientes y vendedores se unen a esa geografía con many_to_one.
  La ausencia de coordenadas no elimina al cliente ni al pedido.
- Los pagos se agregan por pedido antes de unirlos. No se unen las
  filas de pagos directamente con las filas de ítems.
- Un pago ausente se conserva nulo, no se sustituye por cero.
- `diferencia_pago = total_pagado - gmv - flete`, redondeada a dos
  decimales. Se reportan diferencias absolutas superiores a 0,01.
- Las ventas de vendedores se calculan solo con ítems de pedidos
  entregados. Los vendedores sin ventas elegibles se conservan con cero.
- Se exige conservar el número de pedidos, sus claves únicas y el GMV.
  El GMV de vendedores debe reconciliar con el total de pedidos.

## Resultados comprobados

| Tabla SQLite | Filas |
|---|---:|
| pedidos_entregados | 96478 |
| resumen_mensual | 23 |
| pedidos_dashboard | 96478 |
| ventas_categorias | 74 |
| kpis_generales | 1 |
| clientes_geografia | 99441 |
| vendedores_dashboard | 3095 |
| geografia_postal | 19015 |

- Pedidos únicos en pedidos_dashboard: 96478.
- GMV conservado: 13221498,11.
- GMV por vendedores: 13221498,11.
- Pedidos entregados sin pago registrado: 1.
- Pedidos entregados sin coordenadas: 264.
- Pedidos entregados con diferencia de pago superior a un centavo: 299.
- Integridad de la base: `PRAGMA integrity_check = ok`.

Los 299 casos requieren investigación; la diferencia no demuestra
por sí sola fraude ni un error de cálculo del GMV. Los conteos se
refieren exclusivamente a pedidos entregados, no a todos los pedidos.

## Repetición del pipeline completo

Codex tomó una instantánea lógica de las ocho tablas, ejecutó nuevamente
el pipeline completo y comparó los resultados. Las filas se ordenaron
por sus claves antes de calcular SHA-256 de sus contenidos.

Resultado: las ocho tablas conservaron sus conteos y hashes, y SQLite
mantuvo integridad `ok`. No se duplicaron pedidos ni importes.

Evidencia: `reports/verificacion_pipeline_completo.json`.
Este control amplía la comprobación anterior, que solo cubría las
dos tablas del primer ETL. No sustituye las futuras pruebas de pytest
ni comprueba recuperación frente a un fallo a mitad de escritura.

## Incidencia de terminal

El estudiante pulsó Ctrl+C después de que el comando terminara y
regresara el prompt. La base revisada estaba íntegra y completa.

## Preparación de la visualización realizada

El estudiante instaló Streamlit y compartió la salida de instalación,
la consulta de versión y la actualización de requirements.txt:

```bash
python -m pip install streamlit
python -m streamlit version
python -m pip freeze > requirements.txt
```

Codex comprobó que el entorno devuelve `Streamlit, version 1.66.1`
y que requirements.txt incluye Streamlit y sus dependencias.
Esta comprobación no significa que el dashboard ya esté implementado
o visualmente verificado.

## Pendientes para terminar el proyecto

- Dashboard ejecutivo sobre los datos preparados.
- Configuración externa y ejecución con logging y errores controlados.
- Pruebas con pytest según la rúbrica.
- Publicación consistente de las tablas ante fallos de escritura.
- README, evidencias y presentación de 15 minutos más preguntas.
