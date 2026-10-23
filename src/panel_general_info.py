"""
This file reads the map data and general data in order to display them as a response to the interaction.
"""

import streamlit as st
from src.evolution_view import sparkline
from src.constants import LOW, HIGH
from src.utils import num, pct

# def renglon(etiqueta, texto):
#     izq, der = st.columns([3, 2])
#     izq.write(etiqueta)
#     der.markdown(f"<div style='text-align:right'><b>{texto}</b></div>", unsafe_allow_html=True)

def renglones(filas):
    """Todas las filas (texto a la izquierda, valor a la derecha) en un solo bloque HTML compacto."""
    html = "".join(
        f"<div style='display:flex;justify-content:space-between;padding:4px 0;"
        f"border-bottom:1px solid rgba(128,128,128,.15)'>"
        f"<span>{etiqueta}</span><b>{valor}</b></div>"
        for etiqueta, valor in filas
    )
    st.markdown(html, unsafe_allow_html=True)


def status_panel(df, estado, nacional, circuitos, evol):
    d = df[df["Estado"] == estado].iloc[0] # Busca la fila del estado
    lugar = int((df["pct"] > d["pct"]).sum()) + 1  # Cuántos estados tienen más participación (ranking)

    # Tarjeta con borde (engloba todo en el contenedor con with)
    with st.container(border=True):
        st.markdown(
            f"<div style='font-size:1.6rem;color: #151EE6;font-weight:800;line-height:1.2'>{estado}</div>"
            f"<div style='font-size:3rem;font-weight:700;line-height:1.1;margin-top:8px'>{pct(d['pct'])}</div>",
            unsafe_allow_html=True,
        )

        st.caption(f"Lugar {lugar} de {len(df)} en participación") # Texto pequeño

        # Validation - Aviso
        if d["pct"] >= HIGH:
            st.warning(f"Alcanza o supera la referencia alta ({pct(HIGH)}).")
        elif d["pct"] <= LOW:
            st.warning(f"Está en o por debajo de la referencia baja ({pct(LOW)}).")

        # Tendencia en elecciones federales (clic → vista de detalle)
        with st.container(border=True, gap="xsmall"):
            sparkline(evol, estado)

        # renglon("Lista nominal", num(d["Lista nominal"]))
        # renglon("Registros totales", num(d["Registros totales"]))
        # renglon("Sí votó", num(d["Si votó"]))
        # renglon("No votó", num(d["No votó"]))
        # renglon("% Abstención", pct(d["% Abstención"]))
        # renglon("Registros no disponibles", num(d["Votos no disponibles"]))
        # renglon("% Registros no disponibles", pct(d["% Registros no disponibles"]))

        renglones([
            ("Lista nominal", num(d["Lista nominal"])),
            ("Registros totales", num(d["Registros totales"])),
            ("Sí votó", num(d["Si votó"])),
            ("No votó", num(d["No votó"])),
            ("% Abstención", pct(d["% Abstención"])),
            ("Registros no disponibles", num(d["Votos no disponibles"])),
            ("% Registros no disponibles", pct(d["% Registros no disponibles"])),
        ])

        st.divider()
        st.markdown(
            f"<div style='text-align:center; font-size:0.85rem; opacity:0.7'>"
            f"Nacional: {pct(nacional)} ({num(df['Si votó'].sum())} de "
            f"{num(df['Registros totales'].sum())} registros totales)"
            f"</div>",
            unsafe_allow_html=True,
        )