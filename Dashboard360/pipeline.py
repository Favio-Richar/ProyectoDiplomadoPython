"""
DPL1046 · Proyecto integrador · pipeline.py  (Dashboard 360 de Olist)

Problema de negocio:
    El gerente comercial de Olist (un marketplace brasileño) no ve en un
    solo lugar cuánto se vende, si se entrega a tiempo y si los clientes
    quedan contentos: los datos están repartidos en tablas separadas.

Pregunta de negocio:
    ¿Cómo va el negocio y dónde conviene actuar primero?

Para quién:
    El gerente comercial.

Por qué importa:
    Sin una vista única, los problemas de entrega se descubren tarde,
    cuando el cliente ya dejó una mala reseña.

Decisión que permite:
    Priorizar la logística en los estados con peor puntualidad y atacar
    primero los atrasos de más de 10 días (lo calcula mostrar_resumen).

El pipeline tiene 3 pasos (como una cocina):
    1) EXTRAER     -> traer los datos: 6 tablas de Olist + el dólar (API)
    2) TRANSFORMAR -> limpiar, combinar (merge) y resumir (groupby);
                      esas funciones están en transformar.py
    3) CARGAR      -> guardar en SQLite y CSV, y crear el dashboard
                      interactivo (dashboard.py)

Córrelo desde la carpeta del proyecto, con el entorno activo:
    python pipeline.py

Los tests se ejecutan con:
    pytest -v
"""

import logging
import os
import sqlite3
import webbrowser

import pandas as pd
import requests
from dotenv import load_dotenv

from dashboard import crear_dashboard
from transformar import (
    calcular_indicadores,
    entregas_por_estado,
    preparar_pedidos,
    satisfaccion_por_atraso,
    top_categorias,
)

# ---------------------------------------------------------------
# Parámetros del proyecto (los que podrías cambiar sin tocar la lógica)
# ---------------------------------------------------------------
load_dotenv()  # lee el archivo .env (configuración fuera del código)

RUTA_DATOS = "data/raw/"
CARPETA_SALIDA = "salida/"
URL_DOLAR = os.getenv("URL_DOLAR", "https://mindicador.cl/api/dolar")
REAL_EN_DOLARES = 0.19       # 1 real brasileño vale ~0,19 dólares
REAL_EN_CLP_RESPALDO = 180   # si la API falla, usamos este valor
ABRIR_DASHBOARD = True       # abre el dashboard en el navegador al terminar


# ===============================================================
# PASO 1 · EXTRAER
# ===============================================================
def validar_tabla(tabla, nombre, columnas):
    """Revisa que la tabla no esté vacía y traiga las columnas esperadas."""
    faltan = [c for c in columnas if c not in tabla.columns]
    if tabla.empty or faltan:
        raise ValueError(
            f"La tabla '{nombre}' no es válida: vacía o le faltan {faltan}."
        )


def extraer_olist():
    """Lee las 6 tablas de Olist que necesitamos y las valida."""
    pedidos = pd.read_csv(RUTA_DATOS + "olist_orders_dataset.csv")
    items = pd.read_csv(RUTA_DATOS + "olist_order_items_dataset.csv")
    resenas = pd.read_csv(RUTA_DATOS + "olist_order_reviews_dataset.csv")
    clientes = pd.read_csv(RUTA_DATOS + "olist_customers_dataset.csv")
    productos = pd.read_csv(RUTA_DATOS + "olist_products_dataset.csv")
    traduccion = pd.read_csv(
        RUTA_DATOS + "product_category_name_translation.csv"
    )

    # Validar: cada tabla debe traer las columnas que usaremos después
    validar_tabla(pedidos, "pedidos", [
        "order_id", "customer_id", "order_status", "order_purchase_timestamp",
        "order_delivered_customer_date", "order_estimated_delivery_date",
    ])
    validar_tabla(items, "ítems", ["order_id", "product_id", "price"])
    validar_tabla(resenas, "reseñas", ["order_id", "review_score"])
    validar_tabla(clientes, "clientes", ["customer_id", "customer_state"])
    validar_tabla(productos, "productos", [
        "product_id", "product_category_name",
    ])
    validar_tabla(traduccion, "traducción", [
        "product_category_name", "product_category_name_english",
    ])

    logging.info(
        "Olist leído: %s pedidos, %s ítems, %s reseñas y %s clientes",
        len(pedidos), len(items), len(resenas), len(clientes),
    )
    return pedidos, items, resenas, clientes, productos, traduccion


def extraer_dolar():
    """Pide el dólar a una API (mindicador.cl) y lo pasa a pesos por real."""
    try:
        respuesta = requests.get(URL_DOLAR, timeout=10)
        respuesta.raise_for_status()
        dolar_en_clp = respuesta.json()["serie"][0]["valor"]
        real_en_clp = dolar_en_clp * REAL_EN_DOLARES
        logging.info(
            "Dólar de la API: %s CLP -> 1 real = %.1f CLP",
            dolar_en_clp, real_en_clp,
        )
        return real_en_clp
    except requests.RequestException:
        logging.warning(
            "La API del dólar no respondió: uso el valor de respaldo (%s)",
            REAL_EN_CLP_RESPALDO,
        )
        return REAL_EN_CLP_RESPALDO


# ===============================================================
# PASO 3 · CARGAR
# ===============================================================
def cargar(tablas, carpeta):
    """Guarda cada tabla en SQLite y en un CSV.

    Usa if_exists="replace": si corres el pipeline dos veces, la tabla se
    reescribe y queda igual (no se duplica).
    """
    conexion = sqlite3.connect(carpeta + "dashboard360.db")
    for nombre, tabla in tablas.items():
        tabla.to_sql(nombre, conexion, if_exists="replace", index=False)
        tabla.to_csv(carpeta + nombre + ".csv", index=False)
        logging.info("Guardada la tabla '%s' (%s filas)", nombre, len(tabla))
    conexion.close()


def mostrar_resumen(indicadores, por_atraso, por_estado):
    """Imprime el resumen para la gerencia: cifras y decisión."""
    print()
    print("=== RESUMEN PARA LA GERENCIA ===")
    print("\n1) Cómo va el negocio")
    for nombre, valor in zip(indicadores["indicador"], indicadores["valor"]):
        print(f"  {nombre:<24}{valor:>18,.2f}")
    print("\n2) ¿Bajan las notas cuando la entrega se atrasa?")
    print(por_atraso.to_string(index=False))
    print("\n3) Estados con peor puntualidad (los 5 primeros)")
    print(por_estado.head(5).to_string(index=False))

    # Decisión de negocio, calculada con los resultados
    peores = ", ".join(por_estado.head(3)["customer_state"])
    nota_a_tiempo = por_atraso["nota_promedio"].iloc[0]
    nota_muy_tarde = por_atraso["nota_promedio"].iloc[-1]
    print("\nDecisión que permite:")
    print(f"  - Un atraso de más de 10 días baja la nota de "
          f"{nota_a_tiempo} a {nota_muy_tarde}: atacar primero esos casos.")
    print(f"  - Revisar primero la logística en: {peores}.")


# ===============================================================
# EL PIPELINE COMPLETO
# ===============================================================
def main():
    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(
                CARPETA_SALIDA + "pipeline.log", encoding="utf-8"
            ),
            logging.StreamHandler(),
        ],
    )
    logging.info("Dashboard 360: inicio")

    try:
        # 1) EXTRAER
        (pedidos, items, resenas, clientes,
         productos, traduccion) = extraer_olist()
        real_en_clp = extraer_dolar()
    except FileNotFoundError:
        logging.error(
            "No encontré los CSV de Olist en '%s'. "
            "¿Corriste el pipeline desde la carpeta del proyecto?",
            RUTA_DATOS,
        )
        return
    except ValueError as error:
        logging.error("Los datos no pasaron la validación: %s", error)
        return

    # 2) TRANSFORMAR (funciones de transformar.py)
    pedidos = preparar_pedidos(pedidos)
    indicadores = calcular_indicadores(pedidos, items, resenas, real_en_clp)
    categorias = top_categorias(pedidos, items, productos, traduccion)
    por_atraso = satisfaccion_por_atraso(pedidos, resenas)
    por_estado = entregas_por_estado(pedidos, clientes)

    # 3) CARGAR
    cargar(
        {
            "indicadores": indicadores,
            "top_categorias": categorias,
            "satisfaccion_por_atraso": por_atraso,
            "entregas_por_estado": por_estado,
        },
        CARPETA_SALIDA,
    )
    ruta = crear_dashboard(
        indicadores, categorias, por_atraso, por_estado, CARPETA_SALIDA
    )

    mostrar_resumen(indicadores, por_atraso, por_estado)
    if ABRIR_DASHBOARD:
        webbrowser.open("file://" + os.path.abspath(ruta))
    logging.info("Dashboard 360: terminado")


if __name__ == "__main__":
    main()
