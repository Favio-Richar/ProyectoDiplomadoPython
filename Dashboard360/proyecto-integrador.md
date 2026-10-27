# Proyecto Integrador — DPL1046

**Programación en Python y Manipulación de Datos** · Diplomado en Ingeniería de Datos con Python · UDLA

El proyecto integrador es la **evaluación central del curso (100% del examen)**. Construyes un **pipeline de datos completo en Python**, que corre **localmente en tu computador**, sobre el dataset del curso (Olist). Se desarrolla **en parejas** a lo largo de las tres unidades y se presenta en la **Clase 9**.

---

## Cómo funciona

- **Se trabaja en parejas.**
- Cada pareja **elige uno de los 10 temas** de abajo, todos sobre el **dataset del curso (Olist Brazilian E-Commerce)**.
- El proyecto **crece unidad a unidad**, con lo que vemos en cada clase. No hay tareas entre clases: todo se trabaja en clase, y lo único que se evalúa es el proyecto final.
- **Opcional (suma valor):** complementar el análisis con un **dataset propio** (datos.gob.cl, INE, Banco Central, CMF, Kaggle, etc.) o con una **API externa**.
- **La IA es tu copiloto, no tu piloto:** puedes y se espera que la uses como asistente de código, pero tienes que entender y poder explicar cada parte de lo que entregas.
- Tu proyecto **no se sube a este repositorio**: este repo es del profesor y sirve para recibir el material de las clases. La entrega se hace como indique el profesor (Blackboard u otro).

---

## Los 10 temas

Todos usan las 9 tablas de Olist (órdenes, ítems, pagos, reseñas, productos, vendedores, clientes, geolocalización, traducción de categorías). El "ángulo IA" es una **idea opcional** para enriquecer el proyecto con IA local (Clase 8).

**1. Radar de satisfacción del cliente**
Analizar las reseñas (puntaje + comentario) por categoría y vendedor. *Tablas:* reviews, order_items, products. *Ángulo IA:* clasificar sentimiento y temas de los comentarios.

**2. Mapa logístico de entregas**
Tiempos de entrega (estimado vs real) y retrasos por región/estado. *Tablas:* orders, customers, geolocation. *Ángulo IA:* resumen ejecutivo automático de cuellos de botella.

**3. Segmentación de clientes (RFM)**
Recencia, frecuencia y monto para identificar clientes valiosos. *Tablas:* orders, order_payments, customers. *Ángulo IA:* describir en lenguaje natural cada segmento.

**4. Performance de vendedores**
Ranking de sellers por ventas, flete, reseñas y tiempos de despacho. *Tablas:* sellers, order_items, reviews. *Ángulo IA:* generar "fichas" de vendedor a partir de sus métricas.

**5. Análisis de métodos de pago**
Uso de tarjeta/boleto/voucher, cuotas y ticket por medio de pago. *Tablas:* order_payments, orders. *Ángulo IA:* detectar patrones y explicarlos.

**6. Pronóstico de demanda / ventas**
Serie de tiempo de ventas por categoría y mes, con estacionalidad. *Tablas:* orders, order_items, products. *Ángulo IA:* narrar tendencias y anomalías detectadas.

**7. Análisis de categorías de producto**
Qué categorías venden más, su flete y cómo se evalúan. *Tablas:* products, category_translation, order_items, reviews. *Ángulo IA:* clasificar productos sin categoría a partir de su descripción.

**8. Geografía de ventas**
Ventas por estado/ciudad y relación distancia cliente-vendedor vs flete. *Tablas:* geolocation, customers, sellers, order_items. *Ángulo IA:* resumen regional automático.

**9. Detección de órdenes en riesgo**
Predecir cancelaciones, retrasos o malas reseñas. *Tablas:* orders, order_items, reviews. *Ángulo IA:* clasificar el riesgo de una orden y explicar el porqué.

**10. Dashboard 360 del negocio**
Panorama ejecutivo con KPIs integrales (GMV, ticket promedio, satisfacción, entregas, top categorías). *Tablas:* todas. *Ángulo IA:* generar el "resumen para gerencia" del dashboard.

---

## Cómo crece el proyecto por unidad

| Unidad | Qué incluye el proyecto para entonces |
|---|---|
| **Unidad 1 (Clases 1–3)** | Script que lee ≥2 tablas/fuentes del dataset, valida la calidad de los datos y genera un reporte básico del tema elegido. |
| **Unidad 2 (Clases 4–6)** | Pipeline ETL con pandas: lee ≥2 tablas, limpia, combina (`merge`), resume (`groupby`) y guarda el resultado en SQLite o Parquet sin duplicar al repetir la ejecución. |
| **Unidad 3 (Clases 7–9)** | Programa robusto: funciones, manejo de errores, logging, tests con `pytest` y configuración externa; ≥2 fuentes (idealmente una API externa) y resultados en formato ejecutivo. Un componente de IA local suma valor. Presentación en la Clase 9. |

---

## Rúbrica de evaluación

| Criterio | Peso | Qué se evalúa |
|---|---|---|
| Funcionalidad del pipeline | 35% | Corre de principio a fin con un solo comando, integra ≥2 fuentes (ingesta + transformación + salida) y entrega resultados reproducibles. |
| Calidad del código | 30% | Código modular y legible (PEP 8, docstrings), `try/except` + logging, tests con `pytest` (≥3 por función de transformación) y dominio del propio código. |
| Buenas prácticas | 15% | Rutas relativas y configuración externalizada, `requirements.txt`, estructura clara con README, pipeline idempotente, sin credenciales en el código. |
| Presentación y valor de negocio | 20% | Problema → solución → valor, 15 minutos + 5 de preguntas, demo del pipeline funcionando. |

Aprobación: nota 4,0 · asistencia mínima de 70% a las sesiones sincrónicas.

La rúbrica se revisa en la Clase 3 (también está en [`rubrica_y_temas.html`](clases/clase-03/material/rubrica_y_temas.html), con el listado de temas). Un ejemplo completo de proyecto que la cumple se presenta en la Clase 7, y en la Clase 8 hay un taller para ordenar tu entrega.

---

## Checklist de entrega

- [ ] Carpeta del proyecto con el pipeline en Python (scripts organizados).
- [ ] Corre localmente en VS Code, de principio a fin, con un comando.
- [ ] Al menos 2 fuentes/tablas de Olist integradas.
- [ ] Validación de datos + manejo de errores con logging.
- [ ] Tests con `pytest` (incluye la salida de `pytest -v` en el README).
- [ ] `requirements.txt` con las dependencias.
- [ ] README claro: qué hace, cómo instalarlo y cómo ejecutarlo.
- [ ] Presentación final (15 min) basada en el template del curso (`clases/clase-03/material/template_presentacion_proyecto.pptx`).

---

## Presentación final (Clase 9)

Formato demo ejecutiva: **problema de negocio → datos → arquitectura → demo del pipeline → resultados → valor generado**. **15 minutos por pareja + 5 de preguntas.** Ambos integrantes presentan.

---

## Template de la presentación

El archivo editable está en [`clases/clase-03/material/template_presentacion_proyecto.pptx`](clases/clase-03/material/template_presentacion_proyecto.pptx). Es solo de **formato**: cada slide indica qué debe ir y cuánto tiempo. Total: 15 minutos.

| # | Slide | Qué debe ir | Min |
|---|---|---|---|
| 1 | Portada | Título del proyecto, tema, nombres de la pareja | 0,5 |
| 2 | Problema de negocio | ¿Qué pregunta responde? ¿Para quién? ¿Por qué importa? | 2 |
| 3 | Los datos | Tablas o fuentes, tamaño, formatos y calidad | 2 |
| 4 | Arquitectura | Diagrama entrada → proceso → salida y herramientas | 2 |
| 5 | Demo | El pipeline corriendo en vivo, con un comando | 3 |
| 6 | Resultados | 2 o 3 hallazgos con tabla o gráfico | 2 |
| 7 | Calidad y buenas prácticas | Validación, logging, tests, `.env`, README | 1 |
| 8 | Valor de negocio | Qué decisión permite y próximos pasos | 1,5 |
| 9 | Aprendizajes e IA | Cómo usaron la IA y qué aprendieron | 1 |

## Mapa: de cada clase a tu presentación

Esta tabla se completa a medida que avanza el curso: en cada clase conectamos lo aprendido con una slide de tu presentación.

| Clase | Qué aprendes | Dónde cae en tu presentación |
|---|---|---|
| 1–2 | Entorno, Git, leer y ejecutar un script | 7 · Calidad y buenas prácticas (entorno reproducible) |
| 3 | Lista, tupla, set y diccionario; rúbrica y formato | 3 · Los datos · 4 · Arquitectura · 5 · Demo |
| 4 | CSV, Excel, JSON, Parquet y API | 3 · Los datos · 4 · Arquitectura |
| 5 | pandas: DataFrame, filtrar, columnas nuevas y fechas, limpiar; `.env` y datos personales (PII) | 3 · Los datos · 4 · Arquitectura · 6 · Resultados · 7 · Calidad |
| 6 | `groupby`, `merge`, SQLite y cargas que no duplican | 3 · Los datos · 4 · Arquitectura · 6 · Resultados · 7 · Calidad |
| 7 | Funciones, errores, logging, tests, config; proyecto de ejemplo | 7 · Calidad y buenas prácticas · 5 · Demo |
| 8 | Paginación, dos fuentes en una tabla, IA local; taller de proyecto | 3 · Los datos · 4 · Arquitectura · 8 · Valor · 9 · Aprendizajes e IA |
| 9 | Presentaciones y cierre | Todas |
