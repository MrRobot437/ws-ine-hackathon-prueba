"""
Vista de evolución 2009–2024:
  - sparkline(): línea pequeña dentro del panel del estado (clic → abre el detalle)
  - detail_view(): pantalla completa con la gráfica a la derecha y los datos del año a la izquierda
"""

import plotly.graph_objects as go
import streamlit as st

from src.constants import PRESIDENTIAL_YEARS, LINE_COLOR
from src.evolution_data import state_series, state_year
from src.utils import num, pct
from src.evolution_data import (state_series, state_year, municipality_options, municipality_series, municipality_year)
from src.report_data import build_report_data
from src.report_pdf import build_pdf

# En pantallas angostas (celular) Streamlit apila las columnas; con esto la gráfica queda arriba
# y los datos abajo. Solo afecta a los bloques de columnas dentro del contenedor "detalle".
CSS_MOVIL = """
<style>
@media (max-width: 640px) {
  .st-key-detalle [data-testid="stHorizontalBlock"] { flex-direction: column-reverse; }
}
</style>
"""

# Ícono ⓘ compacto: por defecto el botón mide 40 px de alto; aquí se reduce a 22 px.
# Solo afecta a los contenedores cuyo key empieza con "info_" (los de _titulo_con_info).
CSS_INFO = """
<style>
/* Botón ⓘ compacto (por defecto mide 40 px de alto) */
[class*="st-key-info_"] button { min-height: 0; height: 20px; padding: 0; }
[class*="st-key-info_"] button span { font-size: 1rem; }
/* Oculta la flecha "⌄" que el popover agrega después del ícono */
[class*="st-key-info_"] button > div > div:last-child { display: none; }
/* Margen inferior negativo de Streamlit fuera (alinea) + espacio entre el ícono y el texto */
[class*="st-key-info_"] [data-testid="stMarkdownContainer"] { margin-bottom: 0; margin-left: 10px; }
/* Más aire ARRIBA del título y menos ABAJO: así queda pegado a la sección que explica */
[class*="st-key-info_"] { margin-top: 8px; margin-bottom: -6px; }
</style>
"""

# Solo en escritorio: sube el contenido a la altura de la barra de "Deploy".
# La barra (y su toolbar, que ocupa todo el ancho) se vuelven "transparentes al mouse"
# (pointer-events:none) para que no tapen el botón "Volver al mapa"; solo "Deploy" y el menú ⋮
# siguen recibiendo clics (pointer-events:auto).
CSS_ENCABEZADO = """
<style>
@media (min-width: 641px) {
  [data-testid="stMainBlockContainer"] { padding-top: 0.9rem !important; }
  [data-testid="stHeader"], [data-testid="stToolbar"] { pointer-events: none; }
  [data-testid="stHeader"] { background: transparent; }
  [data-testid="stAppDeployButton"], [data-testid="stMainMenu"] { pointer-events: auto; }
}
/* Los bloques que solo contienen <style> no se ven, pero Streamlit les deja separación: se ocultan */
[data-testid="stElementContainer"]:has(style) { display: none; }
/* Separación entre el encabezado (Volver al mapa + estado) y la tabla/gráfica */
.st-key-detalle { margin-top: 1rem; }
/* Separación entre el encabezado (Volver al mapa + estado) y la tabla/gráfica */
.st-key-detalle { margin-top: 1rem; }
/* La tarjeta se alarga hasta casi el final de la pantalla (solo escritorio) */
@media (min-width: 641px) {
  .st-key-tarjeta { min-height: calc(100vh - 210px); }
}
</style>
"""

# ================== Navegación ==================

def open_detail(anio=None):
    """Cambia a la vista de detalle (opcionalmente en un año concreto)."""
    st.session_state["vista"] = "evolucion"
    if anio is not None:
        st.session_state["anio"] = anio


def close_detail():
    st.session_state["vista"] = "mapa"


def _on_sparkline_click(key):
    puntos = st.session_state[key].selection.points
    if puntos:
        open_detail(int(puntos[0]["x"]))


def _on_chart_click():
    puntos = st.session_state["grafica_evolucion"].selection.points
    if puntos:
        st.session_state["anio"] = int(puntos[0]["x"])


# ================== Línea pequeña dentro del panel ==================

def sparkline(evol, estado):
    serie = state_series(evol, estado)
    fig = go.Figure(go.Scatter(
        x=serie.index, y=serie.values, mode="lines+markers",
        line=dict(color=LINE_COLOR, width=2), marker=dict(size=7, color=LINE_COLOR),
        hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        height=90, margin=dict(l=6, r=6, t=6, b=6), dragmode=False, showlegend=False,
        xaxis=dict(visible=False, fixedrange=True), yaxis=dict(visible=False, fixedrange=True),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )

    st.caption("Elecciones federales 2009–2024")
    key = f"spark_{estado}"
    st.plotly_chart(
        fig, use_container_width=True, key=key,
        config={"displayModeBar": False},
        on_select=lambda: _on_sparkline_click(key), selection_mode="points",
    )
    ultimo = serie.index.max()
    # st.caption(f"{ultimo}: {pct(serie[ultimo])} · mín. {pct(serie.min())} ({serie.idxmin()})")
    st.button("Ver evolución →", on_click=open_detail, args=(ultimo,), use_container_width=True)

# ================== Vista de detalle ==================
def _fila(etiqueta, valor):
    return (f"<div style='display:flex;justify-content:space-between;padding:4px 0;"
            f"border-bottom:1px solid rgba(128,128,128,.15)'>"
            f"<span style='opacity:.75'>{etiqueta}</span><b>{valor}</b></div>")


def _barras(filas):
    """Devuelve el HTML de las barras (sin título: el título lo pone _titulo_con_info)."""
    html = ""
    for etiqueta, valor in filas:
        html += (
            "<div style='display:grid;grid-template-columns:72px 1fr 52px;gap:8px;align-items:center;"
            "font-size:0.85rem;margin:1px 0'>"
            f"<span style='opacity:.75'>{etiqueta}</span>"
            "<span style='height:8px;border-radius:4px;background:rgba(128,128,128,.18);overflow:hidden'>"
            f"<span style='display:block;height:100%;width:{valor:.1f}%;background:{LINE_COLOR}'></span></span>"
            f"<b style='text-align:right'>{pct(valor)}</b></div>"
        )
    return html


def _nota_no_binario(filas):
    """Aclara cuántas personas hay detrás del % de no binario (son muy pocas)."""
    nb = filas[(filas["Dimension"] == "Sexo") & (filas["Categoria"] == "No binario")]
    if nb.empty:
        return ""          # años sin la categoría: no se agrega nada
    n = int(nb["LN"].iloc[0])
    persona = "persona" if n == 1 else "personas"
    return (f"<div style='font-size:0.75rem;opacity:.55;margin-top:2px'>"
            f"No binario: {n} {persona} en la lista nominal</div>")


def _titulo_con_info(titulo, ayuda, key):
    """Ícono ⓘ a la IZQUIERDA del título; al hacer clic abre una ventanita con el contexto."""
    with st.container(horizontal=True, vertical_alignment="center", gap=None, key=f"info_{key}"):
        with st.popover("", icon=":material/info:", type="tertiary"):
            st.markdown(ayuda)
        st.markdown(f"<div style='font-size:0.8rem;opacity:.6'>{titulo}</div>", unsafe_allow_html=True)


def _titulo(titulo):
    """Título pequeño sin ícono (para las secciones que no llevan ⓘ)."""
    st.markdown(f"<div style='font-size:0.8rem;opacity:.6'>{titulo}</div>", unsafe_allow_html=True)


# ================== Textos de ayuda (ⓘ) ==================
# Algunos son funciones porque usan los números del estado y año elegidos: así el ejemplo es real.

def _ayuda_participacion(nombre, anio, tipo, total, ref_nombre, ref_valor):
    revisables = total["SV"] + total["NV"]
    return f"""
**¿Qué es este porcentaje?**
De las personas de {nombre} cuyo registro se pudo revisar, cuántas votaron en la elección
**federal {anio}** ({tipo.lower()}).

**¿Cómo se calcula?**
Votaron ÷ (Votaron + No votaron)
= {num(total["SV"])} ÷ {num(revisables)} = **{pct(total["pct"])}**

Los *no especificados* no entran en la cuenta porque no se sabe si votaron.

**Para comparar:** en {ref_nombre} fue {pct(ref_valor)}. En las elecciones *intermedias*
(2009, 2015, 2021) se vota menos que en las *presidenciales* (2012, 2018, 2024).
"""


AYUDA_REGISTROS = """
**Lista nominal:** personas registradas y con credencial vigente que podían votar en su casilla ese día.

**Votaron:** su registro en el cuadernillo de la casilla tiene marca de voto.

**No votaron:** su registro está, pero sin marca de voto.

**No especificados:** su cuadernillo o página no estaba disponible, así que no se sabe si votaron.

Siempre: Lista nominal = Votaron + No votaron + No especificados.
"""


def _ayuda_sexo(filas):
    texto = """
**¿Qué muestra cada barra?**
La participación **dentro de cada grupo**: de cada 100 personas de ese sexo, cuántas votaron.

Por eso las barras **no suman 100%**: cada una se compara solo con su propio grupo.
"""
    sexo = filas[filas["Dimension"] == "Sexo"].set_index("Categoria")
    if "Mujeres" in sexo.index:
        m = sexo.loc["Mujeres"]
        texto += (f"\n**Ejemplo:** votaron {num(m['SV'])} de {num(m['SV'] + m['NV'])} mujeres "
                  f"→ {pct(m['pct'])}.\n")
    if "No binario" in sexo.index:
        texto += ("\n**No binario:** la opción aparece desde 2024 y son muy pocas personas por estado. "
                  "Con grupos tan pequeños, una sola persona cambia mucho el porcentaje: "
                  "léelo como número de personas, no como tendencia.\n")
    return texto


AYUDA_EDAD = """
**¿Qué muestra cada barra?**
La participación dentro de cada grupo de edad (años cumplidos el día de la elección):
de cada 100 personas de ese grupo, cuántas votaron.

Como en sexo, las barras **no suman 100%**. Sirven para comparar qué edades votan más.
"""

AYUDA_SECCION = """
**¿Qué es el tipo de sección?**
El INE clasifica cada sección electoral (el área donde vive la persona, según su credencial)
como **urbana**, **mixta** o **rural**.

Cada barra es la participación de las personas que viven en ese tipo de sección.
Las barras **no suman 100%**.
"""

AYUDA_GRAFICA = """
**Línea morada:** participación del estado en cada elección federal.

**Línea punteada gris:** participación **nacional**, como referencia. Si la morada está arriba,
el estado votó más que el país ese año.

**Haz clic en un punto** para ver el detalle de ese año a la izquierda.

Las intermedias (2009, 2015, 2021) suelen tener menos participación que las presidenciales
(2012, 2018, 2024).

*Fuente: INE, Conteos Censales de Participación Ciudadana. No incluye casillas especiales
ni voto desde el extranjero.*
"""


def _info_anio(filas, serie, nombre, anio, ref_serie, ref_nombre):
    """
    Tarjeta de la izquierda. Sirve igual para un estado o un municipio:
      filas:     filas de ese lugar y año (total, sexo, edad, tipo de sección)
      serie:     participación de ese lugar por año (para calcular el cambio vs la elección anterior)
      ref_serie: serie con la que se compara (nacional si es estado; el estado si es municipio)
    """
    tipo = "Presidencial" if anio in PRESIDENTIAL_YEARS else "Intermedia"
    total = filas[filas["Dimension"] == "Total"]

    # Sin datos: el municipio no existía ese año, o no hubo registros revisables
    if total.empty or total["pct"].isna().all():
        _titulo(f"{nombre} · {anio} · {tipo}")
        st.info(f"No hay datos de participación de {nombre} en {anio}. "
                "Puede ser un municipio creado después, o que sus cuadernillos no estuvieran disponibles.")
        return
    total = total.iloc[0]

    # Cambio contra la elección anterior que sí tenga dato
    anteriores = serie[(serie.index < anio)].dropna()
    ref_valor = ref_serie.get(anio)
    if not anteriores.empty:
        prev = anteriores.index[-1]
        cambio = total["pct"] - anteriores.iloc[-1]
        puntos = f"{'+' if cambio >= 0 else '−'}{abs(cambio):.1f}".replace(".", ",")
        comparacion = f"{puntos} puntos vs {prev} · {ref_nombre} {pct(ref_valor)}"
    else:
        comparacion = f"Primera elección con datos · {ref_nombre} {pct(ref_valor)}"

    def por(dimension, orden):
        d = filas[filas["Dimension"] == dimension].set_index("Categoria")["pct"].dropna()
        return [(c, d[c]) for c in orden if c in d]

    # gap="xsmall": los bloques quedan juntos, como antes, aunque ahora sean varios elementos
    with st.container(gap="xsmall"):
        _titulo_con_info(f"{nombre} · {anio} · {tipo}",
                         _ayuda_participacion(nombre, anio, tipo, total, ref_nombre, ref_valor), "part")
        st.markdown(
            f"<div style='font-size:2.4rem;font-weight:700;line-height:1.15'>{pct(total['pct'])}</div>"
            f"<div style='font-size:0.8rem;opacity:.6;margin-bottom:4px'>{comparacion}</div>",
            unsafe_allow_html=True,
        )

        _titulo("Registros")
        st.markdown(
            _fila("Lista nominal", num(total["LN"])) + _fila("Votaron", num(total["SV"]))
            + _fila("No votaron", num(total["NV"])) + _fila("No especificados", num(total["NS"])),
            unsafe_allow_html=True,
        )

        _titulo_con_info("Por sexo", _ayuda_sexo(filas), "sexo")
        st.markdown(_barras(por("Sexo", ["Mujeres", "Hombres", "No binario"])) + _nota_no_binario(filas),
                    unsafe_allow_html=True)

        _titulo_con_info("Por edad", AYUDA_EDAD, "edad")
        st.markdown(_barras(por("Edad", ["18 a 29", "30 a 59", "60 y más"])), unsafe_allow_html=True)

        _titulo_con_info("Por tipo de sección", AYUDA_SECCION, "secc")
        st.markdown(_barras(por("Tipo de sección", ["Urbana", "Mixta", "Rural"])), unsafe_allow_html=True)


def _grafica(serie, nombre, anio, ref_serie, ref_nombre):
    """Línea del lugar elegido (morada) + línea de referencia (gris punteada)."""
    elegido = [a == anio for a in serie.index]
    ref_titulo = ref_nombre[0].upper() + ref_nombre[1:]      # "nacional" → "Nacional", sin tocar el resto

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ref_serie.index, y=ref_serie.values, name=ref_titulo, mode="lines",
        line=dict(color="rgba(128,128,128,.6)", width=1.5, dash="dot"),
        hovertemplate=f"{ref_titulo} " + "%{x}: %{y:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=serie.index, y=serie.values, name=nombre, mode="lines+markers+text",
        line=dict(color=LINE_COLOR, width=3),
        marker=dict(size=[18 if e else 11 for e in elegido],
                    color=[LINE_COLOR if e else "white" for e in elegido],
                    line=dict(color=LINE_COLOR, width=3)),
        text=[pct(v) if v == v else "" for v in serie.values],   # v == v es False solo si v es NaN
        # Etiqueta abajo en los "valles" y arriba en los "picos", para no encimarse con la línea
        textposition=["bottom center" if v < serie.mean() else "top center" for v in serie.values],
        textfont=dict(size=12),
        hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
    ))
    minimo = min(serie.min(), ref_serie.min())
    maximo = max(serie.max(), ref_serie.max())
    fig.update_layout(
        height=400, margin=dict(l=10, r=10, t=30, b=10), dragmode=False,
        legend=dict(orientation="h", y=1.08, x=0),
        xaxis=dict(tickmode="array", tickvals=list(ref_serie.index), fixedrange=True),
        yaxis=dict(ticksuffix="%", fixedrange=True, range=[minimo - 8, maximo + 8]),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(
        fig, use_container_width=True, key="grafica_evolucion",
        config={"displayModeBar": False},
        on_select=_on_chart_click, selection_mode="points",
    )
    st.caption("Haz clic en un nodo para ver su detalle.")




# ================== Reporte PDF ==================

def _boton_reporte(evol, mun, nacional, judicial, estado, anio):
    """Botón 'Descargar PDF' con una ventanita para elegir el nivel del reporte."""
    clave = st.session_state.get(f"municipio_{estado}", 0)          # el municipio elegido en el selector
    nombre_mun = municipality_options(mun, estado).get(clave) if clave else None

    with st.popover("Descargar PDF", icon=":material/download:"):
        opciones = ["Nacional", "Estado"] + (["Municipio"] if clave else [])
        etiquetas = {"Nacional": "Nacional", "Estado": f"Estado: {estado}", "Municipio": f"Municipio: {nombre_mun}"}
        nivel = st.radio("Nivel del reporte", opciones, index=len(opciones) - 1,
                         format_func=etiquetas.get, key=f"nivel_pdf_{estado}")
        st.caption(f"Elección federal {anio} · infografía en PDF")

        datos = build_report_data(nivel, anio, evol, mun, nacional, judicial, estado, clave or None)
        if datos is None:
            st.warning(f"No hay datos de {nombre_mun} en {anio}. Elige otro año en la gráfica.")
            return

        archivo = {"Nacional": "mexico", "Estado": estado, "Municipio": f"{nombre_mun}_{estado}"}[nivel]
        st.download_button(
            "Descargar",
            data=lambda: build_pdf(datos),           # se genera SOLO al hacer clic
            file_name=f"participacion_{archivo}_{anio}.pdf".replace(" ", "_").lower(),
            mime="application/pdf",
            on_click="ignore",                       # descargar no recarga la página
            type="primary",
            icon=":material/picture_as_pdf:",
        )



def detail_view(evol, estado, nacional, mun, judicial):
    anio = st.session_state.get("anio", int(state_series(evol, estado).index.max()))

    st.markdown(CSS_MOVIL + CSS_INFO + CSS_ENCABEZADO, unsafe_allow_html=True)

    # Encabezado en un solo renglón: botón a la izquierda, estado y fuente a la derecha
    with st.container(horizontal=True, vertical_alignment="center", gap="medium"):
        st.button("← Volver al mapa", on_click=close_detail)
        st.markdown(
            f"<div style='font-size:1.5rem;font-weight:700;line-height:1.2'>{estado}</div>"
            "<div style='font-size:0.8rem;opacity:.6'>Participación en elecciones federales 2009–2024 · "
            "Fuente: INE, Conteos Censales de Participación Ciudadana</div>",
            unsafe_allow_html=True,
        )
        _boton_reporte(evol, mun, nacional, judicial, estado, anio)

    with st.container(key="detalle"):
        izq, der = st.columns([1, 1.5], gap="large", vertical_alignment="center")

        # El selector va en la columna derecha (arriba de la gráfica), pero se dibuja PRIMERO
        # porque su valor decide qué se muestra en las dos columnas.
        with der:
            municipios = municipality_options(mun, estado)
            clave = st.selectbox(
                "Municipio",
                options=[0] + list(municipios),                       # 0 = todo el estado
                format_func=lambda c: "Todo el estado" if c == 0 else municipios[c],
                key=f"municipio_{estado}",                           # un selector por estado
                placeholder="Busca un municipio…",
                width=320,
            )

        if clave == 0:
            nombre = estado
            serie = state_series(evol, estado)
            filas = state_year(evol, estado, anio)
            ref_serie, ref_nombre = nacional, "nacional"
        else:
            nombre = municipios[clave]
            serie = municipality_series(mun, estado, clave)
            filas = municipality_year(mun, estado, clave, anio)
            ref_serie, ref_nombre = state_series(evol, estado), estado

        with izq:
            with st.container(border=True, key="tarjeta"):
                _info_anio(filas, serie, nombre, anio, ref_serie, ref_nombre)
        with der:
            _grafica(serie, nombre, anio, ref_serie, ref_nombre)