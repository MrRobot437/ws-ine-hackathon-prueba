import pandas as pd
import json

# ================== Format ==================

# Cambia el formato de un número a miles con punto
def num(n):
    return f"{n:,}".replace(",", ".")

# Cambia el formato de un porcentaje a 1 decimal con coma
def pct(v):
    return f"{v:.1f}".replace(".", ",") + "%"

# Cambia el formato de decimal con coma
def dec(v):
    return f"{v:.1f}".replace(".", ",")

# ================== Transformations ==================
"""
Convert the text-format columns to numbers '%' 
"""
def convert_percentages(df):
    for col in df.columns:
        if df[col].dtype == "object" and df[col].astype(str).str.endswith("%").all():
            df[col] = (df[col].str.replace("%", "")
                              .str.replace(",", ".")
                              .astype(float))
    return df

def long_to_wide(df, index, medida="Nombres de medidas", valor="Valores de medidas"):
    df = df.copy()
    df[medida] = df[medida].str.replace(r"^\d+\s+", "", regex=True).str.strip()   # "12   IMV" → "IMV"
    ancho = df.pivot_table(index=index, columns=medida, values=valor, aggfunc="first").reset_index()
    ancho.columns.name = None
    return ancho

# ================== Read Files ==================
"""
Reads the CSV and converts it into a table: DataFrame. DF
"""
def read_csv(ruta, sep=";", decimal=",", **kwargs):
    try:
        df = pd.read_csv(ruta, sep=sep, decimal=decimal, encoding="utf-8-sig", **kwargs)
    except UnicodeDecodeError:
        df = pd.read_csv(ruta, sep=sep, decimal=decimal, encoding="latin-1", **kwargs)

    df.columns = df.columns.str.strip()   # remove space in headers
    return df

"""
Convert GeoJSON to dictionary python
"""
def convert_geojson_to_structure(ruta):
    with open(ruta, encoding="utf-8") as f:
        geojson = json.load(f)
    return geojson
