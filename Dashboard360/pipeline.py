"""Punto de entrada del pipeline de Dashboard 360."""

import json
import logging
from pathlib import Path

from src.contexto import incorporar_contexto
from src.etl import ejecutar_etl
from src.indicadores import generar_indicadores


RAIZ = Path(__file__).resolve().parent
RUTA_CONFIGURACION = RAIZ / "config" / "settings.json"


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