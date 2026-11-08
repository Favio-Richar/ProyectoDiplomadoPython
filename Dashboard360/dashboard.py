"""
Dashboard 360 interactivo (archivo salida/dashboard.html).

Negocio: el gerente comercial necesita ver en una sola pantalla cómo va el
negocio y dónde actuar primero. Pasando el mouse ve el detalle de cada
barra, puede hacer zoom y elegir cuántos estados mostrar.

Es una página web que se abre con doble clic: no necesita servidor, ni
internet, ni otro comando. La crea pipeline.py al terminar.
"""

import logging

import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Colores: gris para lo normal, color para lo que importa
GRIS, AZUL, ROJO = "#c5cbd3", "#2b6cb0", "#d1495b"
TRAMOS_COLOR = ["#2f9e6f", "#e9c46a", "#f4a261", "#d1495b"]
TEXTO = "#1f2a44"


def tarjeta(titulo, valor, sufijo, formato):
    """Una tarjeta de indicador: un número grande con su título."""
    return go.Indicator(
        mode="number", value=valor,
        title={"text": titulo, "font": {"size": 16}},
        number={"font": {"size": 38}, "suffix": sufijo,
                "valueformat": formato},
    )


def tarjetas(indicadores):
    """Las 4 tarjetas de arriba: los indicadores principales."""
    kpi = dict(zip(indicadores["indicador"], indicadores["valor"]))
    return [
        tarjeta("Ventas", kpi["ventas_totales_brl"] / 1e6, " M BRL", ",.1f"),
        tarjeta("Ticket promedio", kpi["ticket_promedio_brl"], " BRL", ",.0f"),
        tarjeta("Satisfacción", kpi["satisfaccion_promedio"], " de 5", ".2f"),
        tarjeta("Entregas a tiempo", kpi["entregas_a_tiempo_pct"], " %",
                ".1f"),
    ]


def barras_estados(por_estado, cuantos):
    """Barras de los estados con peor puntualidad (los 3 peores en rojo)."""
    datos = por_estado.head(cuantos)
    colores = [ROJO] * 3 + [GRIS] * (len(datos) - 3)
    return go.Bar(
        x=datos["a_tiempo_pct"], y=datos["customer_state"],
        orientation="h", marker_color=colores, visible=False,
        text=datos["a_tiempo_pct"].map("{:.1f} %".format),
        customdata=datos[["pedidos", "atrasados"]],
        hovertemplate=("<b>%{y}</b><br>A tiempo: %{x:.1f} %<br>"
                       "Pedidos: %{customdata[0]}<br>"
                       "Atrasados: %{customdata[1]}<extra></extra>"),
    )


def recuadro(texto, y, color_fondo):
    """Un recuadro de texto ocupando todo el ancho (arriba o abajo)."""
    return {
        "text": texto, "xref": "paper", "yref": "paper", "x": 0, "y": y,
        "xanchor": "left", "yanchor": "top", "showarrow": False,
        "align": "left", "bgcolor": color_fondo, "borderpad": 10,
        "font": {"size": 14, "color": TEXTO},
    }


def texto_decision(por_atraso, por_estado):
    """La decisión para el gerente, calculada con los resultados."""
    peores = ", ".join(por_estado.head(3)["customer_state"])
    mejor = por_atraso["nota_promedio"].iloc[0]
    peor = por_atraso["nota_promedio"].iloc[-1]
    return (
        "<b>Decisión que permite:</b> "
        f"1) Atacar primero los atrasos de más de 10 días: la nota baja de "
        f"{mejor} a {peor}.  "
        f"2) Revisar primero la logística en <b>{peores}</b>, los estados "
        "con peor puntualidad."
    )


def crear_dashboard(indicadores, categorias, por_atraso, por_estado, carpeta):
    """Arma el dashboard (tarjetas + 3 gráficos) y lo guarda como HTML."""
    columnas = [{"type": "domain", "colspan": 3}, None, None] * 4
    figura = make_subplots(
        rows=2, cols=12, row_heights=[0.16, 0.84],
        vertical_spacing=0.16, horizontal_spacing=0.04,
        specs=[columnas, [{"colspan": 4}, None, None, None,
                          {"colspan": 4}, None, None, None,
                          {"colspan": 4}, None, None, None]],
        subplot_titles=[""] * 4 + [
            f"<b>1 · {categorias['categoria'].iloc[0]} lidera las ventas</b>",
            "<b>2 · Más atraso en la entrega, más baja la nota</b>",
            "<b>3 · Estados con peor puntualidad</b>",
        ],
    )
    for i, tarjeta in enumerate(tarjetas(indicadores)):
        figura.add_trace(tarjeta, row=1, col=1 + i * 3)

    # Gráfico 1: categorías que más venden (las 3 primeras en azul)
    colores = [AZUL] * 3 + [GRIS] * (len(categorias) - 3)
    figura.add_trace(go.Bar(
        x=categorias["ventas_brl"], y=categorias["categoria"],
        orientation="h", marker_color=colores,
        customdata=categorias["unidades"],
        hovertemplate=("<b>%{y}</b><br>Ventas: %{x:,.0f} BRL<br>"
                       "Unidades: %{customdata:,}<extra></extra>"),
    ), row=2, col=1)

    # Gráfico 2 (hallazgo 2): la nota según los días de atraso
    figura.add_trace(go.Bar(
        x=por_atraso["tramo"], y=por_atraso["nota_promedio"],
        marker_color=TRAMOS_COLOR, text=por_atraso["nota_promedio"],
        customdata=por_atraso["pedidos"],
        hovertemplate=("<b>%{x}</b><br>Nota: %{y}<br>"
                       "Pedidos: %{customdata:,}<extra></extra>"),
    ), row=2, col=5)

    # Gráfico 3 (hallazgo 3): estados; el botón elige cuántos mostrar
    opciones = [("Peores 5", 5), ("Peores 10", 10), ("Todos", len(por_estado))]
    for _, cuantos in opciones:
        figura.add_trace(barras_estados(por_estado, cuantos), row=2, col=9)
    total = len(figura.data)
    botones = []
    for i, (nombre, _) in enumerate(opciones):
        visibles = [True] * (total - 3) + [j == i for j in range(3)]
        botones.append({"label": nombre, "method": "update",
                        "args": [{"visible": visibles}]})
    figura.data[total - 2].visible = True  # empieza con "Peores 10"

    figura.update_yaxes(autorange="reversed", row=2, col=1)
    figura.update_yaxes(autorange="reversed", row=2, col=9)
    figura.update_yaxes(dtick=1, row=2, col=9)  # muestra todos los estados
    figura.update_yaxes(range=[0, 5], row=2, col=5)
    figura.update_xaxes(title_text="Ventas (BRL)", row=2, col=1)
    figura.update_xaxes(range=[0, 112], title_text="Entregas a tiempo (%)",
                        row=2, col=9)
    encabezado = (
        "<b>Pregunta:</b> ¿Cómo va el negocio y dónde conviene actuar "
        "primero?   <b>Para quién:</b> el gerente comercial.<br>"
        "<b>Por qué importa:</b> sin una vista única, los problemas de "
        "entrega se descubren tarde, cuando el cliente ya dejó una mala "
        "reseña."
    )
    figura.update_layout(
        title={"text": "<b>Dashboard 360 · Olist</b>", "x": 0.01, "y": 0.97},
        template="plotly_white", showlegend=False, height=860,
        margin={"t": 150, "l": 20, "r": 20, "b": 130},
        font={"color": TEXTO, "size": 13},
        annotations=list(figura.layout.annotations) + [
            recuadro(encabezado, 1.0 + 70 / 580, "#eef2f7"),
            recuadro(texto_decision(por_atraso, por_estado), -0.1,
                     "#fff4e5"),
        ],
        updatemenus=[{"buttons": botones, "active": 1, "x": 1, "y": 0.80,
                      "xanchor": "right", "yanchor": "bottom",
                      "direction": "down"}],
    )
    figura.update_traces(textposition="outside", selector={"type": "bar"})
    ruta = carpeta + "dashboard.html"
    figura.write_html(ruta, include_plotlyjs=True,
                      config={"displayModeBar": False})
    logging.info("Dashboard interactivo guardado: %s", ruta)
    return ruta
