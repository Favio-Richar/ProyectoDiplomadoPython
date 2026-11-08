"""
Pruebas del Dashboard 360 (se ejecutan con:  pytest -v).

Cada prueba usa tablas pequeñas creadas en memoria, con resultados que se
pueden calcular a mano. Hay al menos 3 pruebas por función.
"""

import pandas as pd
import pytest

from pipeline import cargar, validar_tabla
from transformar import (
    calcular_indicadores,
    clasificar_atraso,
    entregas_por_estado,
    preparar_pedidos,
    satisfaccion_por_atraso,
    top_categorias,
)


# ---------------------------------------------------------------
# Tablas de ejemplo
# ---------------------------------------------------------------
def pedidos_crudos():
    """3 pedidos: A llega 2 días tarde, B a tiempo, C cancelado."""
    return pd.DataFrame({
        "order_id": ["A", "B", "C"],
        "customer_id": ["c1", "c2", "c3"],
        "order_status": ["delivered", "delivered", "canceled"],
        "order_purchase_timestamp": ["2018-01-01 10:00:00"] * 3,
        "order_delivered_customer_date": [
            "2018-01-12 15:00:00", "2018-01-08 09:00:00", None],
        "order_estimated_delivery_date": ["2018-01-10 00:00:00"] * 3,
    })


def pedidos_listos(atrasos):
    """Pedidos ya preparados, con los días de atraso que se indiquen."""
    n = len(atrasos)
    return pd.DataFrame({
        "order_id": [f"p{i}" for i in range(n)],
        "customer_id": [f"c{i}" for i in range(n)],
        "fecha_compra": pd.Timestamp("2018-01-01"),
        "dias_atraso": atrasos,
    })


# ---------------------------------------------------------------
# validar_tabla (extraer)
# ---------------------------------------------------------------
def test_validar_tabla_acepta_tabla_correcta():
    tabla = pd.DataFrame({"a": [1], "b": [2]})
    validar_tabla(tabla, "demo", ["a", "b"])  # no debe fallar


def test_validar_tabla_rechaza_tabla_vacia():
    tabla = pd.DataFrame({"a": []})
    with pytest.raises(ValueError):
        validar_tabla(tabla, "demo", ["a"])


def test_validar_tabla_rechaza_columna_faltante():
    tabla = pd.DataFrame({"a": [1]})
    with pytest.raises(ValueError, match="b"):
        validar_tabla(tabla, "demo", ["a", "b"])


# ---------------------------------------------------------------
# preparar_pedidos
# ---------------------------------------------------------------
def test_preparar_pedidos_ignora_no_entregados():
    resultado = preparar_pedidos(pedidos_crudos())
    assert list(resultado["order_id"]) == ["A", "B"]


def test_preparar_pedidos_calcula_dias_de_atraso():
    resultado = preparar_pedidos(pedidos_crudos())
    assert list(resultado["dias_atraso"]) == [2, -2]


def test_preparar_pedidos_sin_fecha_de_entrega_queda_vacio():
    crudos = pedidos_crudos()
    crudos.loc[0, "order_delivered_customer_date"] = None
    resultado = preparar_pedidos(crudos)
    assert pd.isna(resultado.loc[0, "dias_atraso"])


# ---------------------------------------------------------------
# calcular_indicadores
# ---------------------------------------------------------------
def indicador(tabla, nombre):
    return tabla.set_index("indicador").loc[nombre, "valor"]


def test_indicadores_ignora_items_de_pedidos_no_entregados():
    pedidos = pedidos_listos([0, 0])  # p0 y p1 entregados
    items = pd.DataFrame({
        "order_id": ["p0", "p1", "otro"], "price": [100, 200, 999],
    })
    resenas = pd.DataFrame({"order_id": ["p0"], "review_score": [5]})
    resultado = calcular_indicadores(pedidos, items, resenas, 100)
    assert indicador(resultado, "ventas_totales_brl") == 300
    assert indicador(resultado, "ticket_promedio_brl") == 150
    assert indicador(resultado, "ventas_totales_clp") == 30000


def test_indicadores_promedia_resenas_y_excluye_sin_resena():
    pedidos = pedidos_listos([0, 0, 0])
    items = pd.DataFrame({"order_id": ["p0", "p1", "p2"], "price": [1] * 3})
    # p0 tiene dos reseñas (5 y 3 -> 4); p1 tiene 2; p2 no tiene reseña
    resenas = pd.DataFrame({
        "order_id": ["p0", "p0", "p1"], "review_score": [5, 3, 2],
    })
    resultado = calcular_indicadores(pedidos, items, resenas, 1)
    assert indicador(resultado, "satisfaccion_promedio") == 3.0


def test_indicadores_entregas_a_tiempo_ignora_sin_fecha():
    pedidos = pedidos_listos([0, 5, None])  # a tiempo, tarde, sin fecha
    items = pd.DataFrame({"order_id": ["p0", "p1", "p2"], "price": [1] * 3})
    resenas = pd.DataFrame({"order_id": ["p0"], "review_score": [5]})
    resultado = calcular_indicadores(pedidos, items, resenas, 1)
    assert indicador(resultado, "entregas_a_tiempo_pct") == 50.0


# ---------------------------------------------------------------
# top_categorias
# ---------------------------------------------------------------
def tablas_categorias():
    pedidos = pedidos_listos([0, 0, 0])
    items = pd.DataFrame({
        "order_id": ["p0", "p1", "p2", "fuera"],
        "product_id": ["x", "y", "x", "x"],
        "price": [10, 50, 30, 999],
    })
    productos = pd.DataFrame({
        "product_id": ["x", "y"],
        "product_category_name": ["cama", "juguetes"],
    })
    traduccion = pd.DataFrame({
        "product_category_name": ["cama"],
        "product_category_name_english": ["bed"],
    })
    return pedidos, items, productos, traduccion


def test_top_categorias_suma_ventas_y_ordena():
    resultado = top_categorias(*tablas_categorias())
    assert list(resultado["ventas_brl"]) == [50, 40]


def test_top_categorias_traduce_y_usa_original_si_no_hay_traduccion():
    resultado = top_categorias(*tablas_categorias())
    assert list(resultado["categoria"]) == ["juguetes", "bed"]


def test_top_categorias_no_cuenta_pedidos_no_entregados():
    resultado = top_categorias(*tablas_categorias())
    assert resultado["ventas_brl"].sum() == 90  # sin los 999 de "fuera"


# ---------------------------------------------------------------
# clasificar_atraso
# ---------------------------------------------------------------
def test_clasificar_atraso_a_tiempo():
    assert clasificar_atraso(-3) == "A tiempo"
    assert clasificar_atraso(0) == "A tiempo"


def test_clasificar_atraso_tramos_intermedios():
    assert clasificar_atraso(1) == "1 a 3 días"
    assert clasificar_atraso(3) == "1 a 3 días"
    assert clasificar_atraso(4) == "4 a 10 días"
    assert clasificar_atraso(10) == "4 a 10 días"


def test_clasificar_atraso_mas_de_10():
    assert clasificar_atraso(11) == "Más de 10 días"


# ---------------------------------------------------------------
# satisfaccion_por_atraso
# ---------------------------------------------------------------
def test_satisfaccion_por_atraso_calcula_nota_de_cada_tramo():
    pedidos = pedidos_listos([0, 0, 15])
    resenas = pd.DataFrame({
        "order_id": ["p0", "p1", "p2"], "review_score": [5, 4, 1],
    })
    resultado = satisfaccion_por_atraso(pedidos, resenas)
    notas = dict(zip(resultado["tramo"], resultado["nota_promedio"]))
    assert notas == {"A tiempo": 4.5, "Más de 10 días": 1.0}


def test_satisfaccion_por_atraso_ordena_de_menor_a_mayor_atraso():
    pedidos = pedidos_listos([20, 0, 2])
    resenas = pd.DataFrame({
        "order_id": ["p0", "p1", "p2"], "review_score": [1, 5, 3],
    })
    resultado = satisfaccion_por_atraso(pedidos, resenas)
    assert list(resultado["tramo"]) == [
        "A tiempo", "1 a 3 días", "Más de 10 días",
    ]


def test_satisfaccion_por_atraso_ignora_sin_resena_ni_fecha():
    pedidos = pedidos_listos([0, None, 0])
    resenas = pd.DataFrame({
        "order_id": ["p0", "p1"], "review_score": [5, 1],
    })  # p1 sin fecha, p2 sin reseña
    resultado = satisfaccion_por_atraso(pedidos, resenas)
    assert resultado["pedidos"].sum() == 1


# ---------------------------------------------------------------
# entregas_por_estado
# ---------------------------------------------------------------
def tablas_estados():
    pedidos = pedidos_listos([0, 3, 5, 0])
    pedidos["customer_id"] = ["c1", "c2", "c3", "c4"]
    clientes = pd.DataFrame({
        "customer_id": ["c1", "c2", "c3", "c4"],
        "customer_state": ["SP", "SP", "RJ", "SP"],
    })
    return pedidos, clientes


def test_entregas_por_estado_calcula_porcentaje_a_tiempo():
    resultado = entregas_por_estado(*tablas_estados())
    sp = resultado[resultado["customer_state"] == "SP"].iloc[0]
    assert sp["pedidos"] == 3
    assert sp["a_tiempo_pct"] == 66.67


def test_entregas_por_estado_pone_primero_el_peor():
    resultado = entregas_por_estado(*tablas_estados())
    assert resultado.loc[0, "customer_state"] == "RJ"
    assert resultado.loc[0, "a_tiempo_pct"] == 0.0


def test_entregas_por_estado_ignora_pedidos_sin_fecha():
    pedidos, clientes = tablas_estados()
    pedidos.loc[0, "dias_atraso"] = None
    resultado = entregas_por_estado(pedidos, clientes)
    assert resultado["pedidos"].sum() == 3


# ---------------------------------------------------------------
# cargar
# ---------------------------------------------------------------
def test_cargar_dos_veces_no_duplica_filas(tmp_path):
    import sqlite3
    tablas = {"demo": pd.DataFrame({"x": [1, 2, 3]})}
    carpeta = str(tmp_path) + "/"
    cargar(tablas, carpeta)
    cargar(tablas, carpeta)  # segunda corrida
    conexion = sqlite3.connect(carpeta + "dashboard360.db")
    filas = pd.read_sql("SELECT * FROM demo", conexion)
    conexion.close()
    assert len(filas) == 3
    assert (tmp_path / "demo.csv").exists()
