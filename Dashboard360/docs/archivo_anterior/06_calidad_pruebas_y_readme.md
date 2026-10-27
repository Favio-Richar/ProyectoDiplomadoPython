# Unidad 3 Calidad, pruebas y README

## Estado

Configuración externa, logging, pipeline completo, pruebas y README implementados. La evidencia de ejecución proviene de la salida compartida por el estudiante el 27 de octubre de 2026.

## Configuración externa

La configuración se encuentra en `config/settings.json`:

```json
{
  "logging": {
    "level": "INFO",
    "file": "reports/pipeline.log"
  }
}
```

El archivo se carga al iniciar `pipeline.py`. El nivel se valida contra DEBUG, INFO, WARNING, ERROR y CRITICAL; también se requiere la ruta del registro.

Al principio se creó un archivo llamado `config`, cuando el pipeline esperaba una carpeta con `settings.json`. Se conservó el contenido y se movió a `config/settings.json`.

## Logging y errores

El pipeline registra el inicio, las etapas, la finalización y las excepciones en la terminal y en `reports/pipeline.log`. Si falla una etapa, registra el error y vuelve a lanzarlo para que la ejecución indique fallo.

Comando ejecutado:

```bash
python pipeline.py
```

La salida compartida termina con `Pipeline completado correctamente`, después de procesar pedidos, indicadores y contexto de las nueve tablas.

## Pruebas automatizadas

El estudiante ejecutó:

```bash
python -m pytest -v
```

Salida compartida:

```text
collected 9 items
9 passed in 0.72s
```

Las nueve pruebas cubren claves válidas, nulas y duplicadas; selección de pedidos entregados; ítems huérfanos; precios negativos; agrupación mensual; sumas; y ticket promedio. Utilizan tablas pequeñas en memoria y no modifican los CSV originales ni la base del proyecto.

## README

Se creó `README.md` en la raíz del proyecto. Describe el propósito, las fórmulas, las fuentes, la instalación, la ejecución, las salidas SQLite, las pruebas con el resultado real, las limitaciones y la presentación solicitada.

## Cierre técnico de la Unidad 3

La evidencia disponible cubre funciones y módulos, configuración externa, logging, manejo de errores, pytest, README, rutas relativas y ejecución completa con un comando. La repetición del pipeline se comprobó previamente sin duplicaciones.

## Entrega académica pendiente

Completar los nombres de los integrantes, revisar el medio de entrega indicado por el profesor y preparar la presentación con la plantilla oficial. Ensayar la demo mostrando el pipeline y el dashboard. Conservar una captura o video como respaldo. La presentación dura 15 minutos y luego hay 5 minutos de preguntas; ambos integrantes deben presentar.
