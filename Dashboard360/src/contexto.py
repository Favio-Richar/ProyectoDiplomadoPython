"""Integra clientes, pagos, vendedores y geolocalización."""

import sqlite3

import pandas as pd

from src.etl import validar_clave


def incorporar_contexto(raiz):
    """Enriquece los pedidos conservando una fila por pedido."""
    carpeta_raw = raiz / "data" / "raw"
    ruta_base = raiz / "data" / "processed" / "dashboard360.sqlite"

    with sqlite3.connect(ruta_base) as conexion:
        base = pd.read_sql_query(
            "SELECT * FROM pedidos_dashboard",
            conexion,
        )

    cantidad_original = len(base)
    gmv_original = round(float(base["gmv"].sum()), 2)

    # Recuperamos la relación entre pedido y cliente.
    pedidos_clientes = pd.read_csv(
        carpeta_raw / "olist_orders_dataset.csv",
        usecols=["order_id", "customer_id"],
    )

    clientes = pd.read_csv(
        carpeta_raw / "olist_customers_dataset.csv",
        dtype={"customer_zip_code_prefix": "string"},
    )

    vendedores = pd.read_csv(
        carpeta_raw / "olist_sellers_dataset.csv",
        dtype={"seller_zip_code_prefix": "string"},
    )

    pagos = pd.read_csv(
        carpeta_raw / "olist_order_payments_dataset.csv",
        usecols=["order_id", "payment_sequential", "payment_value"],
    )

    geografia = pd.read_csv(
        carpeta_raw / "olist_geolocation_dataset.csv",
        usecols=[
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
        ],
        dtype={"geolocation_zip_code_prefix": "string"},
    )

    items = pd.read_csv(
        carpeta_raw / "olist_order_items_dataset.csv",
        usecols=["order_id", "seller_id", "price", "freight_value"],
    )

    validar_clave(pedidos_clientes, ["order_id"], "pedidos_clientes")
    validar_clave(clientes, ["customer_id"], "clientes")
    validar_clave(vendedores, ["seller_id"], "vendedores")
    validar_clave(
        pagos,
        ["order_id", "payment_sequential"],
        "pagos",
    )

    # Los prefijos postales se tratan como texto de cinco posiciones.
    geografia["prefijo_postal"] = (
        geografia["geolocation_zip_code_prefix"].str.zfill(5)
    )

    clientes["customer_zip_code_prefix"] = (
        clientes["customer_zip_code_prefix"].str.zfill(5)
    )

    vendedores["seller_zip_code_prefix"] = (
        vendedores["seller_zip_code_prefix"].str.zfill(5)
    )

    # Excluimos coordenadas ausentes o fuera del rango mundial.
    latitud = pd.to_numeric(
        geografia["geolocation_lat"],
        errors="coerce",
    )
    longitud = pd.to_numeric(
        geografia["geolocation_lng"],
        errors="coerce",
    )

    coordenadas_validas = (
        latitud.between(-90, 90)
        & longitud.between(-180, 180)
    )

    geografia["geolocation_lat"] = latitud
    geografia["geolocation_lng"] = longitud

    # Varias coordenadas pueden corresponder al mismo prefijo.
    # Obtenemos un punto aproximado por prefijo antes de unir.
    puntos = (
        geografia.loc[
            coordenadas_validas,
            ["prefijo_postal", "geolocation_lat", "geolocation_lng"],
        ]
        .drop_duplicates()
        .groupby("prefijo_postal", as_index=False)
        .agg(
            latitud=("geolocation_lat", "mean"),
            longitud=("geolocation_lng", "mean"),
        )
    )

    clientes_geo = clientes.merge(
        puntos,
        left_on="customer_zip_code_prefix",
        right_on="prefijo_postal",
        how="left",
        validate="many_to_one",
    ).drop(columns="prefijo_postal")

    vendedores_geo = vendedores.merge(
        puntos,
        left_on="seller_zip_code_prefix",
        right_on="prefijo_postal",
        how="left",
        validate="many_to_one",
    ).drop(columns="prefijo_postal")

    # Primero agregamos pagos: nunca unimos sus filas directamente
    # con ítems, porque eso podría multiplicar importes.
    pagos["payment_value"] = pd.to_numeric(
        pagos["payment_value"],
        errors="raise",
    )

    if pagos["payment_value"].isna().any():
        raise ValueError("Hay pagos con importe nulo.")

    if (pagos["payment_value"] < 0).any():
        raise ValueError("Hay pagos con importe negativo.")

    pagos_por_pedido = (
        pagos.groupby("order_id", as_index=False)
        .agg(
            total_pagado=("payment_value", "sum"),
            registros_pago=("payment_sequential", "count"),
        )
    )

    base = base.merge(
        pedidos_clientes,
        on="order_id",
        how="left",
        validate="one_to_one",
    )

    base = base.merge(
        clientes_geo,
        on="customer_id",
        how="left",
        validate="many_to_one",
    )

    if base["customer_unique_id"].isna().any():
        raise ValueError("Hay pedidos sin correspondencia en clientes.")

    base = base.merge(
        pagos_por_pedido,
        on="order_id",
        how="left",
        validate="one_to_one",
    )

    # Un pago ausente se conserva como nulo, no como cero.
    base["diferencia_pago"] = (
        base["total_pagado"] - base["gmv"] - base["flete"]
    ).round(2)

    # Ranking comercial de vendedores para pedidos entregados.
    if not items["seller_id"].isin(vendedores["seller_id"]).all():
        raise ValueError("Hay ítems con vendedores inexistentes.")

    items_entregados = items.loc[
        items["order_id"].isin(base["order_id"])
    ].copy()

    ventas_vendedores = (
        items_entregados.groupby("seller_id", as_index=False)
        .agg(
            gmv=("price", "sum"),
            flete=("freight_value", "sum"),
            cantidad_items=("order_id", "size"),
            cantidad_pedidos=("order_id", "nunique"),
        )
    )

    vendedores_dashboard = vendedores_geo.merge(
        ventas_vendedores,
        on="seller_id",
        how="left",
        validate="one_to_one",
    )

    # Un vendedor sin pedidos entregados tiene ventas elegibles cero.
    columnas_ventas = [
        "gmv",
        "flete",
        "cantidad_items",
        "cantidad_pedidos",
    ]

    vendedores_dashboard[columnas_ventas] = (
        vendedores_dashboard[columnas_ventas].fillna(0)
    )

    vendedores_dashboard[["gmv", "flete"]] = (
        vendedores_dashboard[["gmv", "flete"]].round(2)
    )

    for columna in ["cantidad_items", "cantidad_pedidos"]:
        vendedores_dashboard[columna] = (
            vendedores_dashboard[columna].astype(int)
        )

    # Las uniones deben conservar los pedidos y su GMV.
    validar_clave(base, ["order_id"], "pedidos_dashboard")

    if len(base) != cantidad_original:
        raise ValueError("Cambió la cantidad de pedidos al integrar.")

    if abs(float(base["gmv"].sum()) - gmv_original) > 0.005:
        raise ValueError("Cambió el GMV al integrar.")

    if abs(
        float(vendedores_dashboard["gmv"].sum()) - gmv_original
    ) > 0.005:
        raise ValueError("El GMV por vendedor no coincide con el total.")

    with sqlite3.connect(ruta_base) as conexion:
        base.to_sql(
            "pedidos_dashboard",
            conexion,
            if_exists="replace",
            index=False,
        )

        clientes_geo.to_sql(
            "clientes_geografia",
            conexion,
            if_exists="replace",
            index=False,
        )

        vendedores_dashboard.to_sql(
            "vendedores_dashboard",
            conexion,
            if_exists="replace",
            index=False,
        )

        puntos.to_sql(
            "geografia_postal",
            conexion,
            if_exists="replace",
            index=False,
        )

    print("\nContexto integrado: clientes, pagos, vendedores y geografia.")
    print(f"Pedidos conservados: {len(base):,}")
    print(f"Vendedores: {len(vendedores_dashboard):,}")
    print(f"Prefijos postales con coordenadas: {len(puntos):,}")
    print(f"Pedidos sin pago registrado: {base['total_pagado'].isna().sum()}")
    print(f"Pedidos sin coordenadas: {base['latitud'].isna().sum()}")
    print(
        "Pedidos con diferencia de pago superior a un centavo:",
        base["diferencia_pago"].abs().gt(0.01).sum(),
    )