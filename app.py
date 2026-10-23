import streamlit as st

from src.map_participation import read_data, read_map, create_figure_map
from src.general_data import read_general_data
from src.panel_general_info import status_panel
from src.evolution_data import read_evolution, national_series
from src.evolution_view import detail_view
from src.evolution_data import read_evolution, national_series, read_municipalities

# Use the full width of the screen
st.set_page_config(layout="wide")
# Reduce the top margin of the page (Streamlit leaves ~96px by default)
st.markdown(
    "<style>[data-testid='stMainBlockContainer']{padding-top:3rem;padding-bottom:1rem}</style>",
    unsafe_allow_html=True,
)
# ================== load function ==================
@st.cache_data
def load():
    df = read_data() # Read the information
    nacional = df["Si votó"].sum() / df["Registros totales"].sum() * 100 # Percentage of the national total

    # Evolution - Federal 2009–2024
    nombres = dict(zip(df["Entidad"], df["Estado"]))
    evol = read_evolution(nombres)
    mun = read_municipalities(nombres)
    return df, read_map(), nacional, read_general_data(), evol, national_series(evol), mun

# ================== Callbacks ==================
def on_selecting():
    """It executes only when the user clicks on the map"""
    puntos = st.session_state["mapa"].selection.points
    st.session_state["estado"] = puntos[0]["location"] if puntos else None

# ================== Page ==================
datos, mapa, nacional, circuitos, evol, nacional_federal, mun = load()
estado = st.session_state.get("estado") # Dictionary that survives Streamlit executions
vista = st.session_state.get("vista", "mapa")

if vista == "evolucion" and estado:
    detail_view(evol, estado, nacional_federal, mun, datos)
    st.stop()

fig = create_figure_map(datos, mapa)

# If there is a selected state, show the map and the panel; otherwise, show only the map.
if estado:
    col_mapa, col_panel = st.columns([2, 1])
else:
    col_mapa, col_panel = st.container(), None

with col_mapa:
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False, # Hide the top-right bar
            "scrollZoom": True, # Mouse wheel zoom
        },
        on_select=on_selecting,  # Reload the page - clic
        selection_mode="points",  # Select with clic
        key="mapa",  # A permanent name, so the national team doesn't lose its identity
    )

if col_panel is not None:
    with col_panel:
        status_panel(datos, estado, nacional, circuitos, evol)
