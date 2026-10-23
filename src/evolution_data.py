"""
Datos de evolución: participación por estado y por municipio en las elecciones federales 2009–2024.
Lee los resúmenes que genera src/summarize_counts.py.
"""

from src.constants import CSV_EVOLUTION, CSV_MUNICIPALITIES
from src.utils import read_csv


def _participacion(df):
    """Sí votó ÷ (Sí votó + No votó). Si no hay registros revisables (0 ÷ 0), queda vacío (NaN)."""
    revisables = df["SV"] + df["NV"]
    return (df["SV"] / revisables * 100).where(revisables > 0)


# ================== Estados ==================

def read_evolution(nombres, ruta=CSV_EVOLUTION):
    """
    nombres: diccionario {clave INE: nombre del estado}, para usar los mismos nombres que el mapa.
    Participación = sí votó ÷ (sí votó + no votó), el mismo criterio que la elección judicial.
    """
    df = read_csv(ruta)
    df["Estado"] = df["EDOCVE"].map(nombres)
    df["pct"] = _participacion(df)
    return df


def national_series(evol):
    """Participación nacional por año."""
    total = evol[evol["Dimension"] == "Total"].groupby("Anio")[["SV", "NV"]].sum()
    return (total["SV"] / (total["SV"] + total["NV"]) * 100).round(1)


def state_series(evol, estado):
    """Participación total de un estado por año (para la línea)."""
    s = evol[(evol["Estado"] == estado) & (evol["Dimension"] == "Total")]
    return s.set_index("Anio")["pct"].sort_index()


def state_year(evol, estado, anio):
    """Todas las filas (total, sexo, edad, tipo de sección) de un estado en un año."""
    return evol[(evol["Estado"] == estado) & (evol["Anio"] == anio)]


# ================== Municipios ==================

def read_municipalities(nombres, ruta=CSV_MUNICIPALITIES):
    """Mismo formato que read_evolution, con dos columnas más: MPIOCVE (clave) y MPIONOM (nombre)."""
    df = read_csv(ruta)
    df["Estado"] = df["EDOCVE"].map(nombres)
    df["pct"] = _participacion(df)
    return df


def municipality_options(mun, estado):
    """{clave: nombre} de los municipios del estado, ordenados alfabéticamente por nombre."""
    m = mun[mun["Estado"] == estado][["MPIOCVE", "MPIONOM"]].drop_duplicates("MPIOCVE")
    m = m.sort_values("MPIONOM")
    return dict(zip(m["MPIOCVE"], m["MPIONOM"]))


def municipality_series(mun, estado, clave):
    """Participación total de un municipio por año."""
    s = mun[(mun["Estado"] == estado) & (mun["MPIOCVE"] == clave) & (mun["Dimension"] == "Total")]
    return s.set_index("Anio")["pct"].sort_index()


def municipality_year(mun, estado, clave, anio):
    """Todas las filas (total, sexo, edad, tipo de sección) de un municipio en un año."""
    return mun[(mun["Estado"] == estado) & (mun["MPIOCVE"] == clave) & (mun["Anio"] == anio)]