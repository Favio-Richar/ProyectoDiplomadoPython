"""Indicadores comerciales, satisfacción y entregas de Dashboard 360."""

import sqlite3

import pandas as pd

from src.etl import validar_clave


def generar_indicadores(raiz):
    """Amplía los resultados comerciales con los indicadores del tema."""
    carpeta_raw = raiz / "data" / "raw"
    ruta_base = raiz / "data" / "processed" / "dashboard360.sqlite"

    # Recuperamos los pedidos entregados preparados por el primer ETL.
    with sqlite3.connect(ruta_base) as conexion:
        base = pd.read_sql_query(
            "SELECT * FROM pedidos_entregados",
            conexion,
        )

    # Leemos las columnas necesarias de los archivos originales.
    fechas = pd.read_csv(
        carpeta_raw / "olist_orders_dataset.csv",
        usecols=[
            "order_id",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    )

    resenas = pd.read_csv(
        carpeta_raw / "olist_order_reviews_dataset.csv",
        usecols=["order_id", "review_score"],
    )

    items = pd.read_csv(
        carpeta_raw / "olist_order_items_dataset.csv",
        usecols=["order_id", "product_id", "price", "freight_value"],
    )

    productos = pd.read_csv(
        carpeta_raw / "olist_products_dataset.csv",
        usecols=["product_id", "product_category_name"],
    )

    traducciones = pd.read_csv(
        carpeta_raw / "product_category_name_translation.csv"
    )

    validar_clave(fechas, ["order_id"], "fechas de pedidos")
    validar_clave(productos, ["product_id"], "productos")
    validar_clave(
        traducciones,
        ["product_category_name"],
        "traducciones",
    )

    # Las reseñas deben tener una puntuación válida entre 1 y 5.
    resenas["review_score"] = pd.to_numeric(
        resenas["review_score"],
        errors="raise",
    )

    if not resenas["review_score"].isin([1, 2, 3, 4, 5]).all():
        raise ValueError("Hay puntuaciones de reseña nulas o inválidas.")

    # Puede haber varias reseñas por pedido.
    # Primero calculamos una puntuación media por pedido.
    puntuaciones = (
        resenas.groupby("order_id", as_index=False)
        .agg(
            satisfaccion=("review_score", "mean"),
            cantidad_resenas=("review_score", "count"),
        )
    )

    # Cada unión mantiene exactamente una fila por pedido.
    base = base.merge(
        fechas,
        on="order_id",
        how="left",
        validate="one_to_one",
    )

    base = base.merge(
        puntuaciones,
        on="order_id",
        how="left",
        validate="one_to_one",
    )

    # Los pedidos sin reseña se conservan sin inventar una puntuación.
    base["cantidad_resenas"] = base["cantidad_resenas"].fillna(0).astype(int)

    columnas_fecha = [
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]

    for columna in columnas_fecha:
        base[columna] = pd.to_datetime(base[columna], errors="raise")

    # Comparamos días calendario: la fecha estimada viene a medianoche.
    real = base["order_delivered_customer_date"].dt.normalize()
    estimada = base["order_estimated_delivery_date"].dt.normalize()
    compra = base["order_purchase_timestamp"].dt.normalize()

    base["entrega_evaluable"] = (
        real.notna()
        & estimada.notna()
        & compra.notna()
        & real.ge(compra)
        & estimada.ge(compra)
    )

    # NaN significa no evaluable; no se registra como entrega atrasada.
    base["entrega_a_tiempo"] = float("nan")
    evaluables = base["entrega_evaluable"]

    base.loc[evaluables, "entrega_a_tiempo"] = (
        real.loc[evaluables]
        .le(estimada.loc[evaluables])
        .astype(float)
    )

    # Conservamos categorías originales sin traducción.
    productos = productos.merge(
        traducciones,
        on="product_category_name",
        how="left",
        validate="many_to_one",
    )

    productos["categoria"] = (
        productos["product_category_name_english"]
        .fillna(productos["product_category_name"])
        .fillna("sin_categoria")
    )

    # Solo incluimos ítems de la misma población de pedidos entregados.
    items_entregados = items.merge(
        base[["order_id", "mes_compra"]],
        on="order_id",
        how="inner",
        validate="many_to_one",
    )

    items_entregados = items_entregados.merge(
        productos[["product_id", "categoria"]],
        on="product_id",
        how="left",
        validate="many_to_one",
    )

    if items_entregados["categoria"].isna().any():
        raise ValueError("Hay ítems sin correspondencia en productos.")

    categorias = (
        items_entregados.groupby("categoria", as_index=False)
        .agg(
            gmv=("price", "sum"),
            flete=("freight_value", "sum"),
            cantidad_items=("order_id", "size"),
            cantidad_pedidos=("order_id", "nunique"),
        )
        .sort_values("gmv", ascending=False)
        .reset_index(drop=True)
    )

    categorias[["gmv", "flete"]] = categorias[["gmv", "flete"]].round(2)

    # Las ventas por categoría deben reconciliar con las ventas por pedido.
    gmv_total = round(float(base["gmv"].sum()), 2)
    gmv_categorias = round(float(categorias["gmv"].sum()), 2)

    if abs(gmv_total - gmv_categorias) > 0.005:
        raise ValueError("El GMV por categoría no coincide con el total.")

    cantidad_pedidos = len(base)
    cantidad_evaluable = int(evaluables.sum())

    porcentaje_a_tiempo = None
    if cantidad_evaluable:
        porcentaje_a_tiempo = round(
            base.loc[evaluables, "entrega_a_tiempo"].mean() * 100,
            2,
        )

    # Satisfacción: media de las puntuaciones medias por pedido.
    # Cada pedido con reseña tiene el mismo peso.
    satisfaccion = base["satisfaccion"].mean()

    kpis = pd.DataFrame([{
        "cantidad_pedidos": cantidad_pedidos,
        "gmv": gmv_total,
        "flete": round(float(base["flete"].sum()), 2),
        "ticket_promedio": round(gmv_total / cantidad_pedidos, 2),
        "satisfaccion_promedio": (
            round(float(satisfaccion), 2)
            if pd.notna(satisfaccion)
            else None
        ),
        "pedidos_con_resena": int(base["satisfaccion"].notna().sum()),
        "entregas_evaluables": cantidad_evaluable,
        "entregas_no_evaluables": cantidad_pedidos - cantidad_evaluable,
        "porcentaje_entregas_a_tiempo": porcentaje_a_tiempo,
    }])

    # Estas tablas servirán como entradas del dashboard.
    with sqlite3.connect(ruta_base) as conexion:
        base.to_sql(
            "pedidos_dashboard",
            conexion,
            if_exists="replace",
            index=False,
        )

        categorias.to_sql(
            "ventas_categorias",
            conexion,
            if_exists="replace",
            index=False,
        )

        kpis.to_sql(
            "kpis_generales",
            conexion,
            if_exists="replace",
            index=False,
        )

    print("\nIndicadores generales:")
    print(kpis.to_string(index=False))

    print("\nCinco categorias con mayor GMV:")
    print(categorias.head(5).to_string(index=False))