# Referencia rápida de Dashboard 360 (Olist)

Segundo documento de estudio. La **Guía de estudio** (`Guia_de_estudio_Dashboard360.md`) cuenta el proceso completo; este documento es la hoja de repaso: comandos, reglas, cifras y preguntas de defensa con respuesta.

---

## 1. Comandos

| Para qué | Comando |
|---|---|
| Entrar al proyecto | `cd /c/Users/favio/ProyectoDiplimadoPython/Dashboard360` |
| Activar el entorno (terminal nueva) | `source .venv/Scripts/activate` |
| Crear el entorno (una sola vez) | `py -3.12 -m venv .venv` |
| Instalar dependencias | `python -m pip install -r requirements.txt` |
| Comprobar dependencias | `python -m pip check` |
| Registrar dependencias | `python -m pip freeze > requirements.txt` |
| Explorar los datos | `python src/explorar_datos.py` |
| **Ejecutar el pipeline completo** | `python pipeline.py` |
| **Ejecutar las pruebas** | `python -m pytest -v` |
| **Abrir el dashboard** | `python -m streamlit run dashboard.py` |
| Ubicación / archivos (Bash) | `pwd`, `ls -la` |
| Comprobar el Python activo | `python -c "import sys; print(sys.executable)"` |

Orden normal de trabajo: activar el entorno → `python pipeline.py` → `python -m pytest -v` → `python -m streamlit run dashboard.py`.

---

## 2. El pipeline en una pantalla

| Etapa | Archivo / función | Lee | Produce (tablas SQLite) |
|---|---|---|---|
| 1 | `src/etl.py` / `ejecutar_etl` | orders, order_items | `pedidos_entregados` (96.478), `resumen_mensual` (23) |
| 2 | `src/indicadores.py` / `generar_indicadores` | + reviews, products, translation | `pedidos_dashboard`, `ventas_categorias` (74), `kpis_generales` (1) |
| 3 | `src/contexto.py` / `incorporar_contexto` | + customers, payments, sellers, geolocation | amplía `pedidos_dashboard`; `clientes_geografia` (99.441), `vendedores_dashboard` (3.095), `geografia_postal` (19.015) |

`pipeline.py` carga `config/settings.json`, configura el logging (terminal y `reports/pipeline.log`) y llama las tres etapas. Si una falla: registra el error con traceback y lo relanza.

---

## 3. Reglas que debes poder explicar

1. **Agregar antes de unir.** Ítems, pagos y reseñas se resumen a una fila por pedido antes del `merge`. Si no, se multiplican filas e importes.
2. **`validate=` en cada `merge`.** `one_to_one` o `many_to_one`: pandas falla si la relación no es la esperada.
3. **Reconciliar.** Después de integrar, el número de pedidos y el GMV deben seguir iguales (tolerancia 0,005). GMV por categoría y por vendedor deben sumar el total.
4. **Idempotencia.** `to_sql(..., if_exists="replace")`: repetir no duplica. Se comprobó con SHA-256 de los datos.
5. **No inventar datos.** Sin reseña → satisfacción nula. Sin pago → `total_pagado` nulo, no cero. Entrega no evaluable → no cuenta como atrasada.
6. **Fallar con mensaje claro.** Claves nulas o duplicadas, importes negativos, ítems huérfanos, puntuaciones inválidas: `ValueError`.
7. **Datos originales intactos.** Los CSV solo se leen. El dashboard abre SQLite en solo lectura (`?mode=ro`).

---

## 4. Definiciones de los indicadores

| Indicador | Definición | Resultado |
|---|---|---:|
| GMV | Suma de precios de productos de pedidos `delivered`, sin flete. No es utilidad | 13.221.498,11 |
| Flete | Suma del flete de esos pedidos, aparte | 2.198.275,64 |
| Ticket promedio | GMV / pedidos de la misma población | 137,04 |
| Satisfacción | Media de las medias de reseña por pedido; cada pedido pesa igual | 4,16 de 5 |
| Entregas a tiempo | Fecha real ≤ estimada (días calendario) sobre pedidos evaluables | 93,23 % |
| Categorías | GMV por categoría (traducida; si falta, original; si no hay, `sin_categoria`) | top 5: health_beauty, watches_gifts, bed_bath_table, sports_leisure, computers_accessories |

---

## 5. Cifras para tener en la cabeza

| Dato | Valor |
|---|---:|
| Pedidos totales / entregados | 99.441 / 96.478 (97,02 %) |
| Ítems de entregados | 110.197 |
| Pedidos sin ítems (todas las tablas) | 775 |
| Pedidos con más de una reseña | 551 |
| Pedidos con reseña / sin reseña (entregados) | 95.832 / 646 |
| Entregas evaluables / no evaluables | 96.470 / 8 |
| Entregas a tiempo (cantidad) | 89.936 |
| Sin pago / sin coordenadas / con diferencia de pago | 1 / 264 / 299 |
| `sin_categoria` | 170.726,63 de GMV; 1.537 ítems |
| Categorías | 74 |
| Meses | 23 (no hay entregados en 2016-11; 2016-09 y 2016-12 tienen 1 pedido cada uno) |
| Prefijos postales con coordenadas | 19.015 |
| Tablas SQLite | 8 |
| Pruebas | 9 (3 por cada función de transformación de `etl.py`) |
| Duración del pipeline | ≈ 10 s |
| Versiones | Python 3.12.9, pandas 3.1.0, pytest 9.1.1, Streamlit 1.66.1 |

---

## 6. Preguntas de defensa y respuestas

**1. ¿Qué problema resuelve el proyecto?**
Reúne nueve tablas de Olist en un solo dashboard para responder cómo se comportan ventas, reseñas y entregas, y qué categorías y regiones concentran las ventas. Un pedido tiene varios ítems, pagos y reseñas, y unirlos sin cuidado multiplica los importes; el proyecto lo evita.

**2. ¿Por qué solo pedidos entregados?**
Es la población con ventas concretadas: 96.478 de 99.441 (97,02 %). Los demás estados (enviado, cancelado, no disponible…) no son ventas completadas. La población se aplica igual a GMV, ticket, categorías y vendedores.

**3. ¿Qué es el GMV y por qué sin flete?**
Es la suma de precios de productos. El flete se informa aparte porque no es ingreso por producto. GMV no es utilidad: no hay datos de costos.

**4. ¿Por qué la satisfacción se promedia primero por pedido?**
Porque 551 pedidos tienen más de una reseña. Promediar reseñas directamente haría pesar más a esos pedidos. Con la media por pedido, cada pedido pesa igual.

**5. ¿Qué pasa con los pedidos sin reseña?**
Se conservan con satisfacción nula y no entran al promedio (646 entregados). No se inventa una puntuación.

**6. ¿Cómo mides "entrega a tiempo"?**
Fecha real ≤ fecha estimada, comparando días calendario, porque la estimada viene a medianoche. Solo entran los pedidos evaluables (96.470); 8 no lo son y no se cuentan como atrasados. Resultado: 93,23 %.

**7. ¿Por qué el ticket global no es el promedio de los tickets mensuales?**
Porque cada mes tiene distinto número de pedidos. El ticket global es GMV total / pedidos totales; el mensual es GMV del mes / pedidos del mes.

**8. ¿Cómo evitas que los `merge` multipliquen filas?**
Agrego primero (`groupby`) a una fila por pedido y uso `validate="one_to_one"` o `"many_to_one"`. Luego compruebo que el número de pedidos y el GMV no cambiaron.

**9. ¿Qué hace `validate="one_to_one"`?**
Hace que pandas lance un error si alguna de las dos tablas repite la columna de unión. Convierte una suposición en una comprobación.

**10. ¿Por qué `how="left"` y luego revisas nulos?**
`left` conserva todos los pedidos. Si algún pedido no tuviera ítems quedaría con nulos, y eso se detecta y se rechaza o se informa; no se pierde en silencio.

**11. ¿Qué significa que el pipeline sea idempotente?**
Ejecutarlo dos veces da el mismo resultado. Se logra reemplazando las tablas (`if_exists="replace"`) en vez de agregar. Se comprobó comparando conteos y hashes SHA-256 de las ocho tablas entre dos ejecuciones.

**12. ¿Y si el proceso se corta a mitad de escritura?**
Las tablas se reemplazan una a una, no en una transacción única. Se comprobó la repetición, no la recuperación ante un corte. Es una limitación conocida; la mejora sería escribir en una base temporal y renombrarla al terminar.

**13. ¿Por qué los códigos postales se leen como texto?**
Son identificadores. Como número se perdería el cero inicial (`01037` → `1037`). Se normalizan a cinco posiciones con `zfill(5)`.

**14. ¿Las coordenadas son exactas?**
No. Hay muchas coordenadas por prefijo postal; se calcula la media por prefijo. Es un punto aproximado, no un domicilio.

**15. ¿Qué son los 299 pedidos con diferencia de pago?**
Pedidos entregados donde `total_pagado − gmv − flete` difiere en más de un centavo. Requieren investigación; la diferencia no prueba fraude ni un error del GMV.

**16. ¿Por qué un pago ausente queda nulo y no cero?**
Cero diría "se pagó cero"; nulo dice "no hay dato". Hay 1 pedido entregado sin pago.

**17. ¿Cómo está organizado el logging y el manejo de errores?**
`pipeline.py` lee `config/settings.json`, valida el nivel y la ruta, y configura dos destinos: la terminal y `reports/pipeline.log`. Cada etapa se registra. Si falla, `logger.exception` guarda el traceback y se relanza el error para que la ejecución termine en fallo.

**18. ¿Qué cubren las pruebas?**
Nueve pruebas con tablas pequeñas en memoria: claves válidas, nulas y duplicadas; selección de entregados, ítems sin pedido y precio negativo; y resumen mensual (un registro por mes, sumas y ticket). Cubren `etl.py`. Las reglas de `indicadores.py` y `contexto.py` no tienen pruebas propias, pero se validan en cada ejecución con las reconciliaciones.

**19. ¿Cómo evita el dashboard dañar los datos?**
Abre SQLite con `?mode=ro` (solo lectura). Además usa caché que se invalida sola cuando cambia la fecha de modificación del archivo.

**20. ¿Los filtros cambian el resumen ejecutivo?**
No. Los filtros (rango de meses y estado del cliente) solo afectan la pestaña "Explorar pedidos", donde los indicadores se recalculan con la selección. El resumen ejecutivo mantiene el periodo completo.

**21. ¿Qué limitaciones tiene el proyecto?**
Datos históricos con cobertura parcial en los meses extremos; solo pedidos entregados; sin utilidad (no hay costos); coordenadas aproximadas; escritura no atómica; no se declara moneda porque no se verificó en los materiales; API externa e IA local son opcionales y no están implementadas.

**22. ¿Por qué no declaran la moneda?**
No se verificó en la documentación disponible. Se prefirió decir "importes originales, sin conversión" antes que afirmar algo no comprobado.

**23. ¿Cómo reproduce otra persona tu resultado?**
Clona la carpeta, coloca los nueve CSV en `data/raw/`, crea y activa el entorno, instala `requirements.txt`, ejecuta `python pipeline.py`, luego `python -m pytest -v` y `python -m streamlit run dashboard.py`.

**24. ¿Qué parte hizo la IA?**
Según el registro del proyecto, el estudiante escribió y ejecutó el código y los comandos; el asistente de IA revisó los archivos, comprobó resultados, ayudó con la instalación y preparó documentación y presentación. El README lo declara. Debes poder explicar cada línea del código.

**25. ¿Qué mejorarías con más tiempo?**
Escritura atómica de la base; extraer funciones pequeñas de `indicadores.py` y `contexto.py` y probarlas; logging con `getLogger(__name__)` en cada módulo; ampliar la configuración externa; opcionalmente una segunda fuente (API) y un resumen automático con IA.

---

## 7. Errores típicos (para no repetirlos)

| Error | Qué recordar |
|---|---|
| `command not found` | Estás en Bash, no en PowerShell |
| `ModuleNotFoundError` | Activa `.venv` o usa `./.venv/Scripts/python.exe` |
| `ValueError: ... claves duplicadas` | La validación de datos funcionó: revisa la tabla de origen |
| `FileNotFoundError` en `data/raw` | Faltan CSV en `data/raw/` |
| Dashboard: "No se encontró la base" | Ejecuta antes `python pipeline.py` |
| Resultados "viejos" en el dashboard | Pulsa **Actualizar datos** |
| SQLite no se ve en VS Code | Es binario; usa SQLite Viewer, SQL o Python |
