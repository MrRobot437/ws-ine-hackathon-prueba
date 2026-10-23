"""
Census counts of civic participation
Create the map with a gradient
"""

import plotly.express as px # Graficos interactivos en python
from src.constants import CSV_MAP_DATA, GEOJSON, COLORS_MAP, LOW, HIGH
from src.utils import read_csv, convert_percentages, convert_geojson_to_structure

"""
Read the Map Data
"""
def read_data(ruta=CSV_MAP_DATA):
    df = convert_percentages(read_csv(ruta))
    df["pct"] = df["Si votó"] / df["Registros totales"] * 100
    df["% Abstención"] = df["No votó"] / df["Registros totales"] * 100
    df["% Registros no disponibles"] = df["Votos no disponibles"] / df["Lista nominal"] * 100
    return df

"""
Util Function - Open a GeoJSON file, read, and convert it into a Python data structure
"""
# geojson = convert_geojson_to_structure(GEOJSON)
def read_map(ruta=GEOJSON):
    return convert_geojson_to_structure(ruta)

"""
Generate the colored map
"""
def create_figure_map(df, geojson):
        fig = px.choropleth(
            df,
            geojson=geojson, # Estructura de datos Python
            locations="Estado",  # Columna del CSV con el nombre del estado
            featureidkey="properties.name",  # Dónde viene el nombre dentro del GeoJSON con el que lo emparejara
            color="pct", # El color depende de la columna pct.
            range_color=(LOW, HIGH), # Rango color claro, oscuro
            color_continuous_scale=COLORS_MAP,
            # Configuran el recuadro que aparece al pasar el mouse
            hover_name="Estado", # Titulo en negritas
            hover_data={"Estado": False, "pct": ":.1f", "Si votó": ":,", "Registros totales": ":,"}, # Que mas mostrar y con que formato
            labels={"pct": "% Participación"},
        )

        # Acerca a México y oculta el resto del mundo
        fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")

        # Porcentaje total de los que si votaron
        nacional = df["Si votó"].sum() / df["Registros totales"].sum() * 100

        fig.update_layout(
            # title=f"Participación en la elección judicial (nacional: {nacional:.1f}%)",
            margin=dict(l=0, r=0, t=50, b=0),
            dragmode=False,
            height=450,
            coloraxis_colorbar=dict(
                orientation="h", # Horizontal
                lenmode="fraction", len=0.35, # Ancho automatico
                thickness=12, # Grososr pixeles
                x=0.5, xanchor="center", #Centrada
                y=1.0, yanchor="bottom", # Arriba del mapa
                title=dict(text="% Participación", side="top"), # Titulo encima de la barra
                ticksuffix="%", # 10%, 15%, 20%
            ),
        )

        return fig

