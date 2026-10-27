"""Primer ETL comercial de Dashboard 360."""

import sqlite3

import pandas as pd


def validar_clave(datos, columnas, nombre):
    """Exige una clave completa y única."""
    if datos[columnas].isna().any().any():
        raise ValueError(f"{nombre}: hay claves nulas.")

    if datos.duplicated(subset=columnas).any():
        raise ValueError(f"{nombre}: hay claves duplicadas.")


def transformar_pedidos(pedidos, items):
    """Construye una tabla con una fila por pedido entregado."""
    validar_clave(pedidos, ["order_id"], "orders")
    validar_clave(items, ["order_id", "order_item_id"], "order_items")

    # Todos los ítems deben pertenecer a un pedido existente.
    if not items["order_id"].isin(pedidos["order_id"]).all():
        raise ValueError("Hay ítems asociados a pedidos inexistentes.")

    # Trabajamos sobre copias para conservar las tablas de entrada.
    pedidos = pedidos.copy()
    items = items.copy()

    # Convertimos las fechas de compra a un tipo adecuado.
    pedidos["order_purchase_timestamp"] = pd.to_datetime(
        pedidos["order_purchase_timestamp"],
        errors="raise",
    )

    if pedidos["order_purchase_timestamp"].isna().any():
        raise ValueError("Hay pedidos sin fecha de compra.")

    # Los importes deben ser numéricos, completos y no negativos.
    for columna in ["price", "freight_value"]:
        items[columna] = pd.to_numeric(items[columna], errors="raise")

        if items[columna].isna().any():
            raise ValueError(f"{columna}: hay importes nulos.")

        if (items[columna] < 0).any():
            raise ValueError(f"{columna}: hay importes negativos.")

    # Alcance comercial inicial: solo pedidos entregados.
    entregados = pedidos.loc[
        pedidos["order_status"].eq("delivered"),
        ["order_id", "order_purchase_timestamp"],
    ].copy()

    if entregados.empty:
        raise ValueError("No hay pedidos entregados para analizar.")

    # Sumamos los ítems antes de unir: una fila por pedido.
    importes = (
        items.groupby("order_id", as_index=False)
        .agg(
            cantidad_items=("order_item_id", "count"),
            gmv=("price", "sum"),
            flete=("freight_value", "sum"),
        )
    )

    # La unión debe conservar una sola fila por pedido.
    resultado = entregados.merge(
        importes,
        on="order_id",
        how="left",
        validate="one_to_one",
    )

    if resultado["cantidad_items"].isna().any():
        raise ValueError("Hay pedidos entregados sin ítems.")

    resultado["cantidad_items"] = resultado["cantidad_items"].astype(int)
    resultado[["gmv", "flete"]] = resultado[["gmv", "flete"]].round(2)

    # El mes corresponde a la fecha de compra del pedido.
    resultado["mes_compra"] = (
        resultado["order_purchase_timestamp"]
        .dt.to_period("M")
        .astype(str)
    )

    return resultado


def resumir_por_mes(pedidos):
    """Calcula indicadores mensuales sobre los pedidos preparados."""
    resumen = (
        pedidos.groupby("mes_compra", as_index=False)
        .agg(
            cantidad_pedidos=("order_id", "nunique"),
            cantidad_items=("cantidad_items", "sum"),
            gmv=("gmv", "sum"),
            flete=("flete", "sum"),
        )
    )

    # Numerador y denominador pertenecen a la misma población.
    resumen["ticket_promedio"] = (
        resumen["gmv"] / resumen["cantidad_pedidos"]
    )

    columnas_importes = ["gmv", "flete", "ticket_promedio"]
    resumen[columnas_importes] = resumen[columnas_importes].round(2)

    return resumen


def ejecutar_etl(raiz):
    """Lee los CSV, transforma y guarda resultados en SQLite."""
    carpeta_raw = raiz / "data" / "raw"

    # Solo leemos las columnas necesarias para este primer ETL.
    pedidos = pd.read_csv(
        carpeta_raw / "olist_orders_dataset.csv",
        usecols=["order_id", "order_status", "order_purchase_timestamp"],
        dtype={"order_id": "string"},
    )

    items = pd.read_csv(
        carpeta_raw / "olist_order_items_dataset.csv",
        usecols=["order_id", "order_item_id", "price", "freight_value"],
        dtype={"order_id": "string"},
    )

    pedidos_preparados = transformar_pedidos(pedidos, items)
    resumen_mensual = resumir_por_mes(pedidos_preparados)

    carpeta_salida = raiz / "data" / "processed"
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    ruta_base = carpeta_salida / "dashboard360.sqlite"

    # Cada ejecución reemplaza las tablas de resultados.
    # No agregamos nuevamente los mismos pedidos.
    with sqlite3.connect(ruta_base) as conexion:
        pedidos_preparados.to_sql(
            "pedidos_entregados",
            conexion,
            if_exists="replace",
            index=False,
        )

        resumen_mensual.to_sql(
            "resumen_mensual",
            conexion,
            if_exists="replace",
            index=False,
        )

    print("\nETL completado.")
    print(f"Pedidos entregados: {len(pedidos_preparados):,}")
    print(f"GMV sin flete: {pedidos_preparados['gmv'].sum():,.2f}")
    print(f"Base SQLite: {ruta_base}")
    print("\nResumen mensual:")
    print(resumen_mensual.to_string(index=False))