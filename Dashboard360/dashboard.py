"""Dashboard ejecutivo sobre los resultados preparados en SQLite."""

import sqlite3
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


# Configuración general de la página.
st.set_page_config(
    page_title="Dashboard 360 | Olist",
    layout="wide",
)

RAIZ = Path(__file__).resolve().parent
RUTA_BASE = RAIZ / "data" / "processed" / "dashboard360.sqlite"


def numero(valor, decimales=0):
    """Presenta números con separadores habituales en español."""
    if pd.isna(valor):
        return "Sin datos"

    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


@st.cache_data(max_entries=2, show_spinner="Cargando resultados...")
def cargar_datos(ruta, version):
    """Lee una instantánea de resultados sin modificar SQLite."""
    # version contiene la fecha de modificación del archivo:
    # cuando cambia la base, cambia la clave de la caché.
    tablas = [
        "pedidos_dashboard",
        "resumen_mensual",
        "ventas_categorias",
        "vendedores_dashboard",
    ]

    with sqlite3.connect(
        Path(ruta).resolve().as_uri() + "?mode=ro",
        uri=True,
    ) as conexion:
        # Las consultas comparten una misma instantánea de lectura.
        conexion.execute("BEGIN")

        resultados = {
            tabla: pd.read_sql_query(
                f"SELECT * FROM {tabla}",
                conexion,
            )
            for tabla in tablas
        }

    return resultados


def mostrar_indicadores(pedidos):
    """Muestra métricas calculadas sobre la población recibida."""
    cantidad = len(pedidos)
    gmv = pedidos["gmv"].sum()
    satisfaccion = pedidos["satisfaccion"].mean()

    # Los valores nulos se excluyen del denominador de entregas.
    entregas = pedidos["entrega_a_tiempo"].dropna()
    porcentaje = entregas.mean() * 100 if len(entregas) else None

    columnas = st.columns(5)

    columnas[0].metric(
        "GMV sin flete",
        numero(gmv),
        help=f"Importe completo: {numero(gmv, 2)}",
        border=True,
    )
    columnas[1].metric(
        "Ticket promedio",
        numero(gmv / cantidad, 2),
        help="GMV dividido por pedidos de esta selección.",
        border=True,
    )
    columnas[2].metric(
        "Satisfacción",
        f"{numero(satisfaccion, 2)} / 5"
        if pd.notna(satisfaccion)
        else "Sin datos",
        border=True,
    )
    columnas[3].metric(
        "Entregas a tiempo",
        f"{numero(porcentaje, 2)} %"
        if porcentaje is not None
        else "Sin datos",
        border=True,
    )
    columnas[4].metric(
        "Pedidos entregados",
        numero(cantidad),
        border=True,
    )

    con_resena = int(pedidos["satisfaccion"].notna().sum())

    st.caption(
        f"Satisfacción: {numero(con_resena)} pedidos con reseña. "
        f"Entregas a tiempo: {numero(len(entregas))} pedidos evaluables."
    )


def grafico_barras(datos, categoria, valor, titulo_valor):
    """Construye barras horizontales ordenadas por valor."""
    return (
        alt.Chart(datos)
        .mark_bar(color="#1E40AF")
        .encode(
            x=alt.X(f"{valor}:Q", title=titulo_valor),
            y=alt.Y(
                f"{categoria}:N",
                sort="-x",
                title=None,
            ),
            tooltip=[
                alt.Tooltip(f"{categoria}:N", title="Grupo"),
                alt.Tooltip(
                    f"{valor}:Q",
                    title=titulo_valor,
                    format=",.2f",
                ),
            ],
        )
        .properties(height=340)
    )


def main():
    """Organiza las vistas ejecutiva, exploratoria y de calidad."""
    st.title("Dashboard 360")
    st.write("Ventas, satisfacción y entregas de Olist.")

    if not RUTA_BASE.is_file():
        st.error(
            "No se encontró la base de resultados. "
            "Ejecuta primero: python pipeline.py"
        )
        st.stop()

    st.sidebar.header("Resultados del negocio")
    st.sidebar.caption(
        "Datos históricos. Los indicadores comerciales incluyen "
        "exclusivamente pedidos entregados."
    )

    if st.sidebar.button("Actualizar datos"):
        cargar_datos.clear()

    try:
        datos = cargar_datos(
            str(RUTA_BASE),
            RUTA_BASE.stat().st_mtime_ns,
        )
    except (sqlite3.Error, pd.errors.DatabaseError) as error:
        st.error(
            "No se pudieron leer las tablas. "
            "Ejecuta python pipeline.py para generar los resultados."
        )
        with st.expander("Detalle del error"):
            st.code(str(error))
        st.stop()

    pedidos = datos["pedidos_dashboard"]
    mensual = datos["resumen_mensual"].sort_values("mes_compra")
    categorias = datos["ventas_categorias"].sort_values(
        "gmv",
        ascending=False,
    )
    vendedores = datos["vendedores_dashboard"].sort_values(
        "gmv",
        ascending=False,
    )

    if pedidos.empty or mensual.empty:
        st.info("No hay pedidos entregados para mostrar.")
        st.stop()

    st.caption(
        f"Meses de compra: {mensual['mes_compra'].min()} "
        f"a {mensual['mes_compra'].max()}. "
        "Importes originales, sin conversión de moneda. "
        "El GMV excluye flete."
    )

    resumen, exploracion, calidad = st.tabs([
        "Resumen ejecutivo",
        "Explorar pedidos",
        "Calidad y definiciones",
    ])

    # Esta pestaña presenta el periodo completo.
    with resumen:
        mostrar_indicadores(pedidos)

        izquierda, derecha = st.columns(2)

        with izquierda:
            st.subheader("Evolución mensual del GMV")
            st.line_chart(
                mensual.set_index("mes_compra")[["gmv"]],
                height=340,
            )
            st.caption(
                "Agrupación por mes de compra. "
                "Los meses extremos tienen cobertura parcial."
            )

        with derecha:
            st.subheader("Categorías con mayores ventas")
            limite = st.selectbox(
                "Cantidad de categorías",
                options=[5, 10, 15],
                index=1,
            )
            st.altair_chart(
                grafico_barras(
                    categorias.head(limite),
                    "categoria",
                    "gmv",
                    "GMV sin flete",
                ),
                width="stretch",
            )

        izquierda_2, derecha_2 = st.columns(2)

        with izquierda_2:
            st.subheader("Distribución de la satisfacción")
            # Se redondea hacia arriba desde 0,5 para agrupar en 1 a 5.
            puntajes = (
                (pedidos["satisfaccion"].dropna() + 0.5)
                .astype(int)
                .value_counts()
                .reindex(range(1, 6), fill_value=0)
                .rename_axis("puntaje")
                .reset_index(name="pedidos")
            )
            st.altair_chart(
                alt.Chart(puntajes)
                .mark_bar(color="#1E40AF")
                .encode(
                    x=alt.X(
                        "puntaje:O",
                        title="Puntaje por pedido (redondeado)",
                        axis=alt.Axis(labelAngle=0),
                    ),
                    y=alt.Y("pedidos:Q", title="Pedidos con reseña"),
                    tooltip=[
                        alt.Tooltip("puntaje:O", title="Puntaje"),
                        alt.Tooltip(
                            "pedidos:Q",
                            title="Pedidos",
                            format=",.0f",
                        ),
                    ],
                )
                .properties(height=340),
                width="stretch",
            )
            st.caption(
                "Pedidos entregados con reseña, agrupados por puntaje "
                "medio del pedido."
            )

        with derecha_2:
            st.subheader("Entregas a tiempo por mes")
            evaluables = pedidos.dropna(subset=["entrega_a_tiempo"])
            puntualidad = evaluables.groupby("mes_compra").agg(
                evaluables=("entrega_a_tiempo", "size"),
                porcentaje=("entrega_a_tiempo", "mean"),
            )
            # Los meses con muy pocos pedidos distorsionan el porcentaje.
            puntualidad = puntualidad.loc[puntualidad["evaluables"] >= 30]
            puntualidad["porcentaje"] = puntualidad["porcentaje"] * 100
            st.line_chart(puntualidad[["porcentaje"]], height=340)
            st.caption(
                "Porcentaje de pedidos entregados en la fecha estimada o "
                "antes. Se omiten meses con menos de 30 pedidos evaluables."
            )

        st.subheader("Resumen mensual")
        st.dataframe(mensual, hide_index=True)

        st.download_button(
            "Descargar resumen mensual",
            data=mensual.to_csv(index=False).encode("utf-8-sig"),
            file_name="resumen_mensual.csv",
            mime="text/csv",
        )

        with st.expander("Vendedores con mayores ventas"):
            st.dataframe(
                vendedores[[
                    "seller_id",
                    "seller_state",
                    "cantidad_pedidos",
                    "gmv",
                    "flete",
                ]].head(10),
                hide_index=True,
            )
            st.caption(
                "Un pedido puede contener productos de varios vendedores. "
                "Sus cantidades de pedidos no son aditivas."
            )

    # Los filtros de esta pestaña afectan solo a su contenido.
    with exploracion:
        st.subheader("Analizar pedidos por periodo y región")
        st.caption(
            "Los indicadores siguientes se recalculan con esta selección. "
            "El resumen ejecutivo conserva el periodo completo."
        )

        meses = sorted(pedidos["mes_compra"].dropna().unique().tolist())
        estados = sorted(
            pedidos["customer_state"].dropna().unique().tolist()
        )

        inicio, fin = st.select_slider(
            "Meses de compra",
            options=meses,
            value=(meses[0], meses[-1]),
        )

        estado = st.selectbox(
            "Estado del cliente",
            options=["Todos"] + estados,
        )

        seleccion = pedidos.loc[
            pedidos["mes_compra"].between(inicio, fin)
        ].copy()

        if estado != "Todos":
            seleccion = seleccion.loc[
                seleccion["customer_state"].eq(estado)
            ]

        if seleccion.empty:
            st.info("No hay pedidos para esta selección.")
        else:
            mostrar_indicadores(seleccion)

            por_estado = (
                seleccion.groupby("customer_state", as_index=False)
                .agg(
                    pedidos=("order_id", "nunique"),
                    gmv=("gmv", "sum"),
                )
                .sort_values("gmv", ascending=False)
            )

            st.subheader("Ventas por estado del cliente")
            st.altair_chart(
                grafico_barras(
                    por_estado,
                    "customer_state",
                    "gmv",
                    "GMV sin flete",
                ),
                width="stretch",
            )

            st.dataframe(por_estado, hide_index=True)

            st.download_button(
                "Descargar selección por estado",
                data=por_estado.to_csv(index=False).encode("utf-8-sig"),
                file_name="ventas_por_estado.csv",
                mime="text/csv",
            )

    with calidad:
        st.subheader("Cobertura de los datos")

        controles = pd.DataFrame({
            "Control": [
                "Pedidos sin reseña",
                "Entregas no evaluables",
                "Pedidos sin pago registrado",
                "Pedidos sin coordenadas",
                "Diferencias de pago superiores a un centavo",
            ],
            "Cantidad": [
                int(pedidos["satisfaccion"].isna().sum()),
                int(pedidos["entrega_a_tiempo"].isna().sum()),
                int(pedidos["total_pagado"].isna().sum()),
                int(pedidos["latitud"].isna().sum()),
                int(pedidos["diferencia_pago"].abs().gt(0.01).sum()),
            ],
        })

        st.dataframe(controles, hide_index=True)

        st.subheader("Cómo se interpretan los indicadores")
        st.markdown(
            "- **GMV:** suma de precios de productos de pedidos entregados; "
            "no representa utilidad.\n"
            "- **Ticket:** GMV dividido por pedidos de la misma población.\n"
            "- **Satisfacción:** promedio de puntuaciones medias por pedido, "
            "excluyendo pedidos sin reseña.\n"
            "- **Entregas a tiempo:** fecha real igual o anterior al día "
            "estimado, entre pedidos con fechas evaluables.\n"
            "- **Categorías:** se conservan productos sin categoría "
            "bajo el grupo `sin_categoria`.\n"
            "- **Geografía:** coordenadas aproximadas por prefijo postal.\n"
            "- **Pagos:** una diferencia requiere investigación; "
            "no demuestra por sí sola fraude."
        )


if __name__ == "__main__":
    main()