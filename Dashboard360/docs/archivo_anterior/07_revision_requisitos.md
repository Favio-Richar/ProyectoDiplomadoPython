# Revisión del proyecto Dashboard 360 contra los requisitos del profesor

**Fecha de la revisión:** 27 de octubre de 2026
**Alcance:** lectura completa de `proyecto-integrador.md`, la rúbrica y temas, la teoría de las Clases 3 y 4, la plantilla de la presentación, la guía Word, el código, las pruebas, los reportes, la base SQLite y los nueve CSV.
**Qué NO se hizo:** no se modificó ni borró ningún archivo existente. Este documento y los archivos nuevos son lo único agregado.

## Cómo se verificó

- Las nueve pruebas de `tests/test_etl.py` se ejecutaron en una copia aparte, con un sustituto mínimo de `pytest.raises` porque en el entorno de revisión no estaba instalado. Las nueve pasan. La evidencia oficial sigue siendo tu ejecución de `python -m pytest -v`.
- Los tamaños de las tablas (filas, columnas, nulos, duplicados) se recalcularon sobre los CSV y coinciden con el README.
- Los indicadores (GMV, ticket, satisfacción, entregas a tiempo, categorías) se leyeron de la base `dashboard360.sqlite` y coinciden con `docs/04_indicadores.md`.
- No se pudo ejecutar `python pipeline.py` ni el dashboard de Streamlit desde aquí. El `pipeline.log` del 27/10/2026 10:20 muestra una ejecución completa y correcta.

## Resumen

El proyecto **cumple el núcleo técnico** de la rúbrica: un comando, nueve tablas, resultados repetibles, logging, configuración externa, README y pruebas. Lo que falta o conviene reforzar está abajo, ordenado por riesgo.

| Criterio | Peso | Estado | Comentario breve |
|---|---:|---|---|
| Funcionalidad del pipeline | 35 % | Cumple | `python pipeline.py`, nueve tablas, `replace` idempotente, evidencia en JSON |
| Calidad del código | 30 % | Cumple con brechas | Pruebas solo cubren `src/etl.py`; `print` en módulos; PEP 8 en `explorar_datos.py` |
| Buenas prácticas | 15 % | Cumple con brechas | Falta la salida completa de `pytest -v` en el README; configuración solo de logging |
| Presentación y valor de negocio | 20 % | Pendiente | Se preparó la presentación; faltan nombres, fecha, ensayo y respaldo de la demo |

## Lo que falta o conviene corregir (por prioridad)

### Prioridad alta

1. **Las pruebas no cubren la lógica principal.**
   La rúbrica pide al menos 3 pruebas por función de transformación. Hoy hay 9 pruebas para 3 funciones de `src/etl.py` (`validar_clave`, `transformar_pedidos`, `resumir_por_mes`). Las reglas de negocio más delicadas están en `src/indicadores.py` y `src/contexto.py` y no tienen ninguna prueba: promedio de reseñas por pedido, `entrega_a_tiempo` y entregas no evaluables, categoría con traducción ausente o `sin_categoria`, agregación de pagos y `diferencia_pago`, punto aproximado por prefijo postal.
   Además, `generar_indicadores` y `incorporar_contexto` son funciones de 229 y 270 líneas que leen CSV y escriben SQLite dentro de la misma función. Eso las hace difíciles de probar y de explicar.
   *Sugerencia:* extraer funciones pequeñas y puras (por ejemplo `calcular_satisfaccion`, `clasificar_entrega`, `asignar_categoria`, `agregar_pagos`, `punto_por_prefijo`) y escribir 3 pruebas por cada una con tablas pequeñas en memoria. Hay que hacerlo sin cambiar los resultados: la base debe seguir con los mismos hashes (`reports/verificacion_pipeline_completo.json`).

2. **El README no incluye la salida completa de `pytest -v`.**
   El checklist del profesor dice "incluye la salida de `pytest -v` en el README". El README actual solo muestra `collected 9 items` y `9 passed in 0.72s`. Falta pegar las líneas por prueba (`tests/test_etl.py::test_... PASSED`). Se debe pegar la salida real de tu terminal; no se inventa.

3. **El README no presenta el caso como caso.**
   Tiene la pregunta de negocio y los indicadores, pero no una sección que cuente el caso: quién es Olist, qué contiene el conjunto de datos, quién toma decisiones con el dashboard y por qué importa. Se redactó `README_propuesto.md` (no reemplaza tu README) con esa sección y el resto del contenido actual conservado. Revísalo y, si te gusta, cámbialo tú por el README.

4. **Nombres de los integrantes y fecha.**
   El proyecto es en pareja y no aparece en ningún archivo el nombre de la pareja. La portada de la presentación lleva `[Nombre Apellido]` y `[fecha]`. Completa ambos.

### Prioridad media

5. **Logging solo en el punto de entrada.**
   `pipeline.py` configura el logging y registra las etapas y las excepciones. Los módulos de `src/` usan `print`. La rúbrica pide "try/except + logging". Está cubierto a nivel del pipeline, pero es más sólido que cada módulo use `logging.getLogger(__name__)` y que un archivo CSV faltante dé un mensaje claro (hoy se registra el traceback de `FileNotFoundError`).

6. **Configuración externa limitada.**
   `config/settings.json` solo tiene el nivel y el archivo del log. Rutas, nombres de archivo, la regla de estado `delivered` y la tolerancia de 0,005 están dentro del código. Cumple "rutas relativas y configuración externa" en lo mínimo; ampliarla es una mejora, no un requisito roto.

7. **PEP 8 en `src/explorar_datos.py`.**
   Tiene espacios sin formato (`claves ={`, `columnas_clave =claves[tabla]`), espacios al final de línea e indentación irregular en el cierre. No afecta los resultados. Conviene ordenarlo antes de entregar. No lo toqué.

8. **Documentación `docs/` con "Pendientes" ya resueltos.**
   `03_etl_sqlite.md`, `04_indicadores.md` y `05_contexto_nueve_tablas.md` listan como pendiente cosas que `06_calidad_pruebas_y_readme.md` ya resolvió (dashboard, logging, pruebas, README). Si el profesor revisa `docs/`, puede parecer contradictorio. Sugerencia: agregar una línea de "estado actual" al inicio de cada una.

9. **Escritura SQLite no atómica.**
   Las tablas se reemplazan una a una. Si el proceso falla a la mitad quedan resultados mezclados. Ya lo documentaste como limitación. Para la defensa, ten lista la respuesta: se garantiza la repetición con las mismas entradas, no la recuperación ante un corte.

### Prioridad baja o decisiones tuyas

10. **API externa, Parquet e IA local: no están.**
    Son opcionales. La Clase 4 presenta la API pública `mindicador.cl` como "segunda fuente opcional que suma valor" y Parquet como formato de salida. El tema 10 sugiere como ángulo IA "generar el resumen para gerencia". La rúbrica exige al menos dos fuentes o tablas, y tú integras nueve, así que el requisito se cumple. Si agregas una API, define qué aporta y qué pasa sin internet. Si no la agregas, la presentación debe decirlo con naturalidad (ya está en "próximos pasos").

11. **Moneda no declarada.**
    El README dice que no se declara moneda porque no se verificó en los materiales del curso. Es una decisión honesta y correcta. Si quieres declararla, confirma antes en la descripción oficial del dataset en Kaggle y cítala.

12. **Archivos al entregar.**
    `.gitignore` excluye `reports/*` y `data/processed/*`. Si la entrega es por Blackboard u otro medio (no Git), incluye `reports/` (log y verificaciones) y la base `data/processed/dashboard360.sqlite` o indica cómo regenerarla. Excluye `.venv/` y `.pytest_cache/`. Los CSV originales pesan unos 126 MB.

13. **Datos: lo que debes saber para las preguntas.**
    - Hay 99.441 pedidos y 96.478 (97,02 %) están entregados; esa es la población de los indicadores.
    - Hay 775 pedidos sin ítems y 551 pedidos con más de una reseña; por eso la satisfacción se promedia primero por pedido.
    - La cobertura mensual va de 2016-09 a 2018-08 con 23 meses: **no hay pedidos entregados en 2016-11**. En 2016-09 y 2016-12 hay un solo pedido por mes, así que esos meses no sirven para comparar.
    - Entregas: 8 pedidos entregados no son evaluables (fechas ausentes o anteriores a la compra); 93,23 % a tiempo sobre 96.470 evaluables.
    - 646 pedidos entregados sin reseña, 1 sin pago, 264 sin coordenadas y 299 con diferencia de pago mayor a un centavo.

## Checklist oficial del profesor

| Requisito | Estado |
|---|---|
| Carpeta con el pipeline en Python (scripts organizados) | Cumple |
| Corre localmente en VS Code con un comando | Cumple (`python pipeline.py`) |
| Al menos 2 fuentes o tablas de Olist integradas | Cumple (nueve tablas) |
| Validación de datos y manejo de errores con logging | Cumple en lo esencial; ver puntos 1 y 5 |
| Pruebas con pytest, con la salida de `pytest -v` en el README | Parcial; ver puntos 1 y 2 |
| `requirements.txt` | Cumple |
| README claro (qué hace, cómo instalar, cómo ejecutar) | Cumple; falta el caso y la salida de `pytest -v` |
| Presentación de 15 minutos con la plantilla del curso | Preparada; faltan nombres, fecha y ensayo |

## Antes de presentar

- Completar nombres de la pareja y fecha en la portada.
- Ensayar `python pipeline.py` (unos 10 segundos según el log) y `python -m streamlit run dashboard.py`.
- Grabar una captura o video corto de respaldo de la demo.
- Repartir las secciones entre los dos integrantes: ambos deben presentar y pueden preguntarte por cualquier línea de código.
