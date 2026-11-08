"""
DPL1046 · Proyecto integrador · transformar.py  (Dashboard 360 de Olist)

PASO 2 del pipeline: TRANSFORMAR. Aquí se limpian, combinan (merge) y
resumen (groupby) las tablas para responder la pregunta de negocio:

    ¿Cómo va el negocio y dónde conviene actuar primero?

Cada función responde una parte de esa pregunta:

    preparar_pedidos         -> limpia: solo pedidos entregados y su atraso
    calcular_indicadores     -> hallazgo 1: ventas, ticket, satisfacción...
    top_categorias           -> qué categorías venden más
    satisfaccion_por_atraso  -> hallazgo 2: ¿los atrasos bajan las notas?
    entregas_por_estado      -> hallazgo 3: ¿en qué estados se atrasa más?

Estas funciones reciben tablas y devuelven tablas: no leen ni guardan
archivos (eso lo hace pipeline.py). Por eso se pueden probar con tablas
pequeñas, como se ve en test_pipeline.py.
"""

import logging

import pandas as pd

# ---------------------------------------------------------------
# Parámetros de esta etapa
# ---------------------------------------------------------------
TOP_CATEGORIAS = 10          # cuántas categorías mostrar en el ranking
ORDEN_TRAMOS = {             # orden en que se muestran los tramos de atraso
    "A tiempo": 1,
    "1 a 3 días": 2,
    "4 a 10 días": 3,
    "Más de 10 días": 4,
}


def preparar_pedidos(pedidos):
    """Deja solo los pedidos entregados, con su fecha y días de atraso.

    Negocio: solo lo que ya se entregó cuenta como venta y puede tener una
    reseña confiable; los cancelados o en camino distorsionan los números.
    """
    # Limpiar: nos quedamos con los pedidos entregados
    entregados = pedidos[pedidos["order_status"] == "delivered"].copy()

    # Fechas: de texto a fecha. Sin la hora, para comparar días calendario
    entregados["fecha_compra"] = pd.to_datetime(
        entregados["order_purchase_timestamp"]
    )
    real = pd.to_datetime(
        entregados["order_delivered_customer_date"]
    ).dt.normalize()
    prometida = pd.to_datetime(
        entregados["order_estimated_delivery_date"]
    ).dt.normalize()

    # Columna nueva: días de atraso (negativo = llegó antes de lo prometido).
    # Si no hay fecha de entrega, queda vacío (NaN): no se inventa un dato
    entregados["dias_atraso"] = (real - prometida).dt.days

    logging.info(
        "Pedidos entregados: %s de %s", len(entregados), len(pedidos)
    )
    columnas = ["order_id", "customer_id", "fecha_compra", "dias_atraso"]
    return entregados[columnas]


def calcular_indicadores(pedidos, items, resenas, real_en_clp):
    """Hallazgo 1: ventas, ticket, satisfacción y entregas a tiempo.

    Negocio: es el panorama de un vistazo que pide el gerente comercial.
    Tablas: pedidos + ítems (order_id) y pedidos + reseñas (order_id).
    """
    # Combinar: los ítems de cada pedido entregado
    ventas = items.merge(pedidos[["order_id"]], on="order_id", how="inner")
    logging.info(
        "merge ítems + pedidos: %s -> %s filas", len(items), len(ventas)
    )

    ventas_totales = ventas["price"].sum()
    ticket = ventas_totales / ventas["order_id"].nunique()

    # Un pedido puede tener varias reseñas: promediamos por pedido
    nota = resenas.groupby("order_id")["review_score"].mean().reset_index()

    # Combinar: la nota de cada pedido (los que no tienen reseña no cuentan)
    con_nota = pedidos.merge(nota, on="order_id", how="inner")
    logging.info(
        "merge pedidos + reseñas: %s -> %s filas", len(pedidos), len(con_nota)
    )

    # Entregas a tiempo: solo donde se conoce la fecha de entrega
    con_fecha = pedidos["dias_atraso"].dropna()
    a_tiempo = (con_fecha <= 0).mean() * 100

    return pd.DataFrame({
        "indicador": [
            "pedidos_entregados", "ventas_totales_brl", "ventas_totales_clp",
            "ticket_promedio_brl", "satisfaccion_promedio",
            "entregas_a_tiempo_pct",
        ],
        "valor": [
            len(pedidos), ventas_totales, ventas_totales * real_en_clp,
            ticket, con_nota["review_score"].mean(), a_tiempo,
        ],
    }).round(2)


def top_categorias(pedidos, items, productos, traduccion):
    """Qué categorías venden más (nombre en inglés).

    Negocio: muestra dónde se concentran las ventas.
    Tablas: ítems + pedidos (order_id), + productos (product_id) y
    + traducción (product_category_name).
    """
    # Combinar: ítems entregados + producto + traducción de su categoría
    tabla = items.merge(pedidos[["order_id"]], on="order_id", how="inner")
    tabla = tabla.merge(
        productos[["product_id", "product_category_name"]],
        on="product_id", how="left",
    )
    tabla = tabla.merge(traduccion, on="product_category_name", how="left")
    logging.info(
        "merge de categorías: %s ítems -> %s filas", len(items), len(tabla)
    )

    # Nulos: si no hay traducción usamos el nombre original; si tampoco,
    # "sin_categoria"
    tabla["categoria"] = (
        tabla["product_category_name_english"]
        .fillna(tabla["product_category_name"])
        .fillna("sin_categoria")
    )

    # Resumir: ventas y unidades de cada categoría, las mayores primero
    ranking = tabla.groupby("categoria", as_index=False).agg(
        unidades=("order_id", "count"),
        ventas_brl=("price", "sum"),
    )
    ranking = ranking.sort_values("ventas_brl", ascending=False)
    return ranking.head(TOP_CATEGORIAS).round(2).reset_index(drop=True)


def clasificar_atraso(dias):
    """Clasifica los días de atraso de un pedido en un tramo."""
    if dias <= 0:
        return "A tiempo"
    elif dias <= 3:
        return "1 a 3 días"
    elif dias <= 10:
        return "4 a 10 días"
    else:
        return "Más de 10 días"


def satisfaccion_por_atraso(pedidos, resenas):
    """Hallazgo 2: ¿bajan las notas cuando la entrega se atrasa?

    Negocio: si el atraso hace caer la satisfacción, mejorar la entrega
    mejora la reputación. Tablas: pedidos + reseñas (order_id).
    """
    # Un pedido puede tener varias reseñas: promediamos por pedido
    nota = resenas.groupby("order_id")["review_score"].mean().reset_index()

    # Combinar: la nota de cada pedido. Solo pedidos con reseña y con
    # fecha de entrega conocida
    tabla = pedidos.merge(nota, on="order_id", how="inner")
    logging.info(
        "merge pedidos + reseñas: %s -> %s filas", len(pedidos), len(tabla)
    )
    tabla = tabla.dropna(subset=["dias_atraso"])

    # Columna nueva: el tramo de atraso de cada pedido
    tabla["tramo"] = tabla["dias_atraso"].apply(clasificar_atraso)

    # Resumir: pedidos y nota promedio de cada tramo
    resumen = tabla.groupby("tramo", as_index=False).agg(
        pedidos=("order_id", "count"),
        nota_promedio=("review_score", "mean"),
    )

    # Ordenar los tramos de menor a mayor atraso
    resumen["orden"] = resumen["tramo"].map(ORDEN_TRAMOS)
    resumen = resumen.sort_values("orden").drop(columns="orden")
    return resumen.round(2).reset_index(drop=True)


def entregas_por_estado(pedidos, clientes):
    """Hallazgo 3: ¿en qué estados se atrasan más las entregas?

    Negocio: indica dónde conviene actuar primero en la logística.
    Tablas: pedidos + clientes (customer_id).
    """
    # Combinar: el estado de cada cliente. Solo entregas con fecha conocida
    tabla = pedidos.merge(
        clientes[["customer_id", "customer_state"]],
        on="customer_id", how="inner",
    )
    logging.info(
        "merge pedidos + clientes: %s -> %s filas", len(pedidos), len(tabla)
    )
    tabla = tabla.dropna(subset=["dias_atraso"])

    # Columna nueva: True si el pedido llegó después de lo prometido
    tabla["atrasado"] = tabla["dias_atraso"] > 0

    # Resumir: pedidos y atrasos de cada estado
    resumen = tabla.groupby("customer_state", as_index=False).agg(
        pedidos=("order_id", "count"),
        atrasados=("atrasado", "sum"),
    )
    resumen["a_tiempo_pct"] = (
        1 - resumen["atrasados"] / resumen["pedidos"]
    ) * 100

    # Los estados con peor puntualidad primero
    resumen = resumen.sort_values("a_tiempo_pct")
    return resumen.round(2).reset_index(drop=True)
