from src.constants import CSV_GENERAL_DATA
from src.utils import read_csv, long_to_wide


def read_general_data(ruta=CSV_GENERAL_DATA):
    """Una fila por (Estado, Circuito) y una columna por medida."""
    g = read_csv(ruta)
    g.columns = ["Entidad", "Estado", "Abrev", "Circuito", "Nombres de medidas", "i", "Valores de medidas"]
    return long_to_wide(g, index=["Estado", "Circuito"])

"""
Util Function - Read the General Data Information
"""
# df_general = read_csv(CSV_GENERAL_DATA)