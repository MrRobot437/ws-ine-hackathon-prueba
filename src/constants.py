# src/config.py
from pathlib import Path

# Paths
ROOT_PATH = Path(__file__).resolve().parents[1] # /src
ORIGIN_DATA = ROOT_PATH / "data"
DESTINO = ROOT_PATH / "data" / "resumen" / "conteos_estado.csv"
DESTINO_MUNICIPIOS = ROOT_PATH / "data" / "resumen" / "conteos_municipio.csv"
CSV_MAP_DATA = ORIGIN_DATA / "explorar_mapa" / "MapaEnt_data.csv"
CSV_GENERAL_DATA = ORIGIN_DATA / "datos_generales" / "tabla_general_data.csv"

# 460BBD - Oscuro, 7948CE - Medio Oscuro, AC85DF - Medio, D1B2EF - Medio Claro, F6E5FF - Claro
# Colors
COLORS_MAP = ["#F6E5FF", "#D1B2EF", "#AC85DF", "#7948CE", "#460BBD"]

# References - Explore map
LOW, CENTER, HIGH = 6.6, 15.0, 23.4
GEOJSON = ORIGIN_DATA / "explorar_mapa" / "mexico_estados.geojson"
# Resumir conteos
YEARS = [2009, 2012, 2015, 2018, 2021, 2024]

# COLUMNS = ["EDOCVE", "SEXO", "EDAD", "TIPOSEC", "LN", "SV", "NV", "NS"]
COLUMNS = ["EDOCVE", "MPIOCVE", "MPIONOM", "SEXO", "EDAD", "TIPOSEC", "LN", "SV", "NV", "NS"]
COUNTS = ["LN", "SV", "NV", "NS"]
GENDER_CATEGORIES = {0: "Hombres", 1: "Mujeres", 2: "No binario"}
TYPES = {"U": "Urbana", "M": "Mixta", "R": "Rural"}
AGES = [17, 29, 59, 200] # cortes: 18–29, 30–59, 60 y más
NAME_AGE = ["18 a 29", "30 a 59", "60 y más"]

# Evolución - Conteos censales de elecciones federales (resumen generado por scripts/summarize_counts.py)
CSV_EVOLUTION = ORIGIN_DATA / "resumen" / "conteos_estado.csv"
CSV_MUNICIPALITIES = DESTINO_MUNICIPIOS
PRESIDENTIAL_YEARS = [2012, 2018, 2024]
LINE_COLOR = COLORS_MAP[-1]
