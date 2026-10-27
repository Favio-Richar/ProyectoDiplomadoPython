"""Pruebas de las validaciones y transformaciones del ETL."""

import pandas as pd
import pytest

from src.etl import (
    resumir_por_mes,
    transformar_pedidos,
    validar_clave,
)


def pedidos_ejemplo():
    """Crea dos pedidos pequeños para probar sin leer los CSV reales."""
    return pd.DataFrame({
        "order_id": ["pedido-1", "pedido-2"],
        "order_status": ["delivered", "shipped"],
        "order_purchase_timestamp": [
            "2020-01-10 10:00:00",
            "2020-02-05 12:00:00",
        ],
    })


def items_ejemplo():
    """Crea dos ítems pequeños asociados a los pedidos de ejemplo."""
    return pd.DataFrame({
        "order_id": ["pedido-1", "pedido-2"],
        "order_item_id": [1, 1],
        "price": [100.00, 50.00],
        "freight_value": [10.00, 5.00],
    })


# Tres casos para validar claves: correcta, nula y repetida.
def test_validar_clave_acepta_clave_unica():
    datos = pd.DataFrame({"id": ["a", "b"]})

    validar_clave(datos, ["id"], "prueba")


def test_validar_clave_rechaza_nulos():
    datos = pd.DataFrame({"id": ["a", None]})

    with pytest.raises(ValueError, match="nulas"):
        validar_clave(datos, ["id"], "prueba")


def test_validar_clave_rechaza_duplicados():
    datos = pd.DataFrame({"id": ["a", "a"]})

    with pytest.raises(ValueError, match="duplicadas"):
        validar_clave(datos, ["id"], "prueba")


# Tres casos para transformar_pedidos.
def test_transformar_pedidos_incluye_solo_entregados():
    resultado = transformar_pedidos(
        pedidos_ejemplo(),
        items_ejemplo(),
    )

    assert resultado["order_id"].tolist() == ["pedido-1"]
    assert resultado.iloc[0]["gmv"] == 100.00


def test_transformar_pedidos_rechaza_item_sin_pedido():
    items = items_ejemplo()
    items.loc[0, "order_id"] = "pedido-inexistente"

    with pytest.raises(ValueError, match="inexistentes"):
        transformar_pedidos(pedidos_ejemplo(), items)


def test_transformar_pedidos_rechaza_precio_negativo():
    items = items_ejemplo()
    items.loc[0, "price"] = -1.00

    with pytest.raises(ValueError, match="negativos"):
        transformar_pedidos(pedidos_ejemplo(), items)


# Tres casos para resumir_por_mes.
def pedidos_preparados_ejemplo():
    """Crea pedidos ya agregados, con las columnas que usa el resumen."""
    return pd.DataFrame({
        "order_id": ["a", "b", "c"],
        "mes_compra": ["2020-01", "2020-01", "2020-02"],
        "cantidad_items": [1, 2, 1],
        "gmv": [100.00, 50.00, 90.00],
        "flete": [10.00, 5.00, 9.00],
    })


def test_resumir_por_mes_crea_un_registro_por_mes():
    resultado = resumir_por_mes(pedidos_preparados_ejemplo())

    assert resultado["mes_compra"].tolist() == ["2020-01", "2020-02"]


def test_resumir_por_mes_suma_pedidos_items_y_gmv():
    resultado = resumir_por_mes(pedidos_preparados_ejemplo())
    enero = resultado.loc[
        resultado["mes_compra"].eq("2020-01")
    ].iloc[0]

    assert enero["cantidad_pedidos"] == 2
    assert enero["cantidad_items"] == 3
    assert enero["gmv"] == 150.00


def test_resumir_por_mes_calcula_ticket_del_mismo_periodo():
    resultado = resumir_por_mes(pedidos_preparados_ejemplo())
    enero = resultado.loc[
        resultado["mes_compra"].eq("2020-01")
    ].iloc[0]

    assert enero["ticket_promedio"] == 75.00