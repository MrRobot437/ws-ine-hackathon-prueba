"""
Summarizes the 2009–2024 census counts into two small CSV files:
  - conteos_estado.csv     → by state and year
  - conteos_municipio.csv  → by municipality and year

This is run only ONCE (or whenever the data changes)—not from within Streamlit.
From the ws_ine_hackathon folder:
    python -m src.summarize_counts
"""

import sys
import pandas as pd
from pathlib import Path
from src.utils import read_csv
from src.constants import (ORIGIN_DATA, DESTINO, DESTINO_MUNICIPIOS, YEARS, COLUMNS, COUNTS,
                           GENDER_CATEGORIES, TYPES, AGES, NAME_AGE)

DIMENSIONES = [("Total", "total"), ("Sexo", "sexo"), ("Edad", "edad"), ("Tipo de sección", "tipo")]


def read_file(ruta):
    return read_csv(ruta, sep=",", decimal=".", usecols=COLUMNS)


def summarize(df, claves):
    """
    Suma los conteos por cada dimensión (total, sexo, edad, tipo de sección).
    claves: columnas que identifican cada fila del resumen.
      - por estado:    ["EDOCVE"]
      - por municipio: ["EDOCVE", "MPIOCVE"]
    """
    partes = []
    for dimension, columna in DIMENSIONES:
        g = df.groupby(claves + [columna], observed=True)[COUNTS].sum().reset_index()
        g = g.rename(columns={columna: "Categoria"})
        g["Dimension"] = dimension
        partes.append(g)
    return pd.concat(partes, ignore_index=True)


def summary_of_years(anio, origen):
    """Lee los 32 estados de un año UNA vez y devuelve los dos resúmenes: (estatal, municipal)."""
    carpeta = origen / f"DatosAbiertos_DECEyEC_ConteosCensales{anio}"
    df = pd.concat([read_file(f) for f in sorted(carpeta.glob("*.csv"))], ignore_index=True)

    df["sexo"] = df["SEXO"].map(GENDER_CATEGORIES)
    df["edad"] = pd.cut(df["EDAD"], AGES, labels=NAME_AGE).astype(str)
    df["tipo"] = df["TIPOSEC"].map(TYPES)
    df["total"] = "Total"

    estatal = summarize(df, ["EDOCVE"])
    municipal = summarize(df, ["EDOCVE", "MPIOCVE"])

    # Nombre de cada municipio en este año (un municipio puede escribirse distinto entre años)
    nombres = df[["EDOCVE", "MPIOCVE", "MPIONOM"]].drop_duplicates(["EDOCVE", "MPIOCVE"])

    estatal["Anio"] = anio
    municipal["Anio"] = anio
    nombres["Anio"] = anio
    return estatal, municipal, nombres


def main(origen=ORIGIN_DATA, destino=DESTINO, destino_mun=DESTINO_MUNICIPIOS):
    estatales, municipales, nombres = [], [], []
    for anio in YEARS:
        print(f"Resumiendo {anio}...")
        e, m, n = summary_of_years(anio, origen)
        estatales.append(e)
        municipales.append(m)
        nombres.append(n)

    # ---- Por estado (igual que antes) ----
    final = pd.concat(estatales, ignore_index=True)
    final = final[["Anio", "EDOCVE", "Dimension", "Categoria"] + COUNTS]
    destino.parent.mkdir(parents=True, exist_ok=True)
    final.to_csv(destino, sep=";", index=False, encoding="utf-8-sig")
    print(f"Listo: {len(final)} filas en {destino}")

    # ---- Por municipio ----
    mun = pd.concat(municipales, ignore_index=True)
    # Un solo nombre por municipio: el del año más reciente en que aparece
    nombres = (pd.concat(nombres, ignore_index=True)
                 .sort_values("Anio")
                 .drop_duplicates(["EDOCVE", "MPIOCVE"], keep="last")
                 .drop(columns="Anio"))
    mun = mun.merge(nombres, on=["EDOCVE", "MPIOCVE"], how="left")
    mun = mun[["Anio", "EDOCVE", "MPIOCVE", "MPIONOM", "Dimension", "Categoria"] + COUNTS]
    mun.to_csv(destino_mun, sep=";", index=False, encoding="utf-8-sig")
    print(f"Listo: {len(mun)} filas en {destino_mun}")


if __name__ == "__main__":
    if len(sys.argv) == 4:
        main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    else:
        main()