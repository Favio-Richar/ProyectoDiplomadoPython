# Dashboard 360 del negocio · Olist

DPL1046 · Programación en Python y Manipulación de Datos · UDLA
Tema 10 — Dashboard 360 del negocio

## Problema de negocio

El gerente comercial de Olist (marketplace brasileño, 99.441 pedidos) no ve
en un solo lugar cuánto se vende, si se entrega a tiempo y si los clientes
quedan contentos: los datos están en tablas separadas.

**Pregunta:** ¿Cómo va el negocio y dónde conviene actuar primero?

**Para quién:** el gerente comercial.

**Por qué importa:** sin una vista única, los problemas de entrega se
descubren tarde, cuando el cliente ya dejó una mala reseña.

**Decisión que permite:** priorizar la logística en los estados con peor
puntualidad y atacar primero los atrasos de más de 10 días.

## Solución: un pipeline de 3 pasos

1. **Extraer** (`pipeline.py`): lee 6 tablas de Olist y el dólar desde la API
   mindicador.cl (si la API falla, usa un valor de respaldo y lo avisa).
2. **Transformar** (`transformar.py`): limpia, combina (`merge`) y resume
   (`groupby`) para responder la pregunta.
3. **Cargar** (`pipeline.py` y `dashboard.py`): guarda en SQLite y CSV, crea
   el **dashboard interactivo** (`salida/dashboard.html`, se abre solo en el
   navegador) y muestra el resumen para la gerencia.

## Resultados

| Hallazgo | Resultado |
|---|---|
| Panorama | Ventas 13,2 M BRL, ticket 137,04, satisfacción 4,16, 93,23 % a tiempo |
| Atrasos y satisfacción | A tiempo 4,29 → más de 10 días de atraso 1,71 |
| Dónde se atrasa más | AL (78,59 %), MA (82,57 %), SE (84,78 %) |

## Cómo ejecutarlo

Siempre desde la carpeta del proyecto (`Dashboard360`), con el entorno
virtual activo y los CSV de Olist en `data/raw/`.

```bash
# 1. Activar el entorno virtual (Git Bash en Windows)
source .venv/Scripts/activate

# 2. Instalar las librerías: SOLO si te falta alguna (se hace una vez)
pip install -r requirements.txt

# 3. Correr el pipeline completo (un solo comando)
python pipeline.py

# 4. Correr las pruebas
pytest -v
```

- Si las librerías ya están instaladas, salta el paso 2.
- La URL de la API del dólar está en el archivo `.env` (no se sube a git). Si
  no lo tienes, copia `.env.example` como `.env`; sin él, el pipeline usa la
  misma URL por defecto.
- Al terminar se abre `salida/dashboard.html` en el navegador (si no se abre,
  haz doble clic en ese archivo). Pasa el mouse sobre las barras para ver el
  detalle y usa el botón para elegir cuántos estados mostrar.
- Los resultados quedan en `salida/` (dashboard, base SQLite, CSV y log).
- Ejecutar el pipeline dos veces da el mismo resultado (no duplica datos).

## Archivos

```text
Dashboard360/
├── pipeline.py        extraer + cargar + main
├── transformar.py     funciones de transformación
├── dashboard.py       dashboard interactivo (HTML con Plotly)
├── test_pipeline.py   pruebas con pytest
├── requirements.txt
├── data/raw/          CSV originales (no se suben a git)
└── salida/            dashboard.html, dashboard360.db, CSV y pipeline.log
```

## Resultado de las pruebas (`pytest -v`)

```text
test_pipeline.py::test_validar_tabla_acepta_tabla_correcta PASSED
test_pipeline.py::test_validar_tabla_rechaza_tabla_vacia PASSED
test_pipeline.py::test_validar_tabla_rechaza_columna_faltante PASSED
test_pipeline.py::test_preparar_pedidos_ignora_no_entregados PASSED
test_pipeline.py::test_preparar_pedidos_calcula_dias_de_atraso PASSED
test_pipeline.py::test_preparar_pedidos_sin_fecha_de_entrega_queda_vacio PASSED
test_pipeline.py::test_indicadores_ignora_items_de_pedidos_no_entregados PASSED
test_pipeline.py::test_indicadores_promedia_resenas_y_excluye_sin_resena PASSED
test_pipeline.py::test_indicadores_entregas_a_tiempo_ignora_sin_fecha PASSED
test_pipeline.py::test_top_categorias_suma_ventas_y_ordena PASSED
test_pipeline.py::test_top_categorias_traduce_y_usa_original_si_no_hay_traduccion PASSED
test_pipeline.py::test_top_categorias_no_cuenta_pedidos_no_entregados PASSED
test_pipeline.py::test_clasificar_atraso_a_tiempo PASSED
test_pipeline.py::test_clasificar_atraso_tramos_intermedios PASSED
test_pipeline.py::test_clasificar_atraso_mas_de_10 PASSED
test_pipeline.py::test_satisfaccion_por_atraso_calcula_nota_de_cada_tramo PASSED
test_pipeline.py::test_satisfaccion_por_atraso_ordena_de_menor_a_mayor_atraso PASSED
test_pipeline.py::test_satisfaccion_por_atraso_ignora_sin_resena_ni_fecha PASSED
test_pipeline.py::test_entregas_por_estado_calcula_porcentaje_a_tiempo PASSED
test_pipeline.py::test_entregas_por_estado_pone_primero_el_peor PASSED
test_pipeline.py::test_entregas_por_estado_ignora_pedidos_sin_fecha PASSED
test_pipeline.py::test_cargar_dos_veces_no_duplica_filas PASSED
============================== 22 passed ==============================
```

## Datos y decisiones de calidad

- Se usan solo pedidos **entregados** (96.478 de 99.441).
- Reseñas repetidas en un pedido: se promedian por pedido.
- Pedidos sin reseña: no cuentan en la satisfacción (no se inventa nota).
- 8 pedidos sin fecha de entrega: no cuentan en entregas a tiempo.

## Limitación

Los datos son de 2016–2018 y no incluyen costos, así que no se mide
rentabilidad, solo ventas, entregas y satisfacción.

## Siguiente paso

Hoy el pipeline se corre a mano con `python pipeline.py`. Un paso natural
sería automatizarlo para que corra cada semana (Programador de tareas de
Windows o cron) y el gerente tenga el dashboard siempre al día.
