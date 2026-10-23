"""
Datos del reporte PDF (infografía): junta en un diccionario todo lo que se dibuja para
un nivel (Nacional, Estado o Municipio) y un año.

No dibuja nada: solo prepara números y textos. El dibujo está en src/report_pdf.py.
"""

from src.constants import PRESIDENTIAL_YEARS
from src.evolution_data import (state_series, state_year, municipality_options,
                                municipality_series, municipality_year)
from src.utils import num, pct

ORDEN_SEXO = ["Mujeres", "Hombres", "No binario"]
ORDEN_EDAD = ["18 a 29", "30 a 59", "60 y más"]
ORDEN_SECCION = ["Urbana", "Mixta", "Rural"]
PLURAL_SECCION = {"Urbana": "urbanas", "Mixta": "mixtas", "Rural": "rurales"}


def _puntos(d):
    """6.84 → '6,8' (siempre positivo; el texto dice si es 'más' o 'menos')."""
    return f"{abs(d):.1f}".replace(".", ",")


def _participacion(df):
    revisables = df["SV"] + df["NV"]
    return (df["SV"] / revisables * 100).where(revisables > 0)


def national_year(evol, anio):
    """Filas nacionales de un año (total, sexo, edad, tipo de sección): suma de los 32 estados."""
    filas = (evol[evol["Anio"] == anio]
             .groupby(["Dimension", "Categoria"], as_index=False)[["LN", "SV", "NV", "NS"]].sum())
    filas["pct"] = _participacion(filas)
    return filas


def _por(filas, dimension, orden):
    """[(categoría, %), ...] en el orden dado, solo las que existen y tienen dato."""
    d = filas[filas["Dimension"] == dimension].set_index("Categoria")["pct"].dropna()
    return [(c, float(d[c])) for c in orden if c in d]


def _hallazgos(nombre, total, sexo, edad, seccion, serie, anio, ref_serie, ref_nombre):
    """Frases cortas calculadas con los datos: lo más importante sin leer tablas."""
    frases = []
    s, e, t = dict(sexo), dict(edad), dict(seccion)

    ref = ref_serie.get(anio)
    if ref is not None and ref == ref:
        d = total["pct"] - ref
        de_ref = "del " + ref_nombre[3:] if ref_nombre.startswith("el ") else "de " + ref_nombre
        frases.append(f"La participación de {nombre} estuvo {_puntos(d)} puntos "
                      f"{'por encima' if d >= 0 else 'por debajo'} {de_ref} ({pct(ref)}).")

    if "Mujeres" in s and "Hombres" in s:
        d = s["Mujeres"] - s["Hombres"]
        frases.append(f"Las mujeres votaron {_puntos(d)} puntos {'más' if d >= 0 else 'menos'} que los hombres.")

    if "60 y más" in e and "18 a 29" in e:
        d = e["60 y más"] - e["18 a 29"]
        frases.append(f"Las personas de 60 años y más votaron {_puntos(d)} puntos "
                      f"{'más' if d >= 0 else 'menos'} que las de 18 a 29.")

    if len(t) >= 2:
        alto = max(t, key=t.get)
        bajo = min(t, key=t.get)
        frases.append(f"En secciones {PLURAL_SECCION[alto]} se votó {_puntos(t[alto] - t[bajo])} puntos más "
                      f"que en las {PLURAL_SECCION[bajo]}.")

    anteriores = serie[serie.index < anio].dropna()
    if not anteriores.empty:
        prev = anteriores.index[-1]
        d = total["pct"] - anteriores.iloc[-1]
        frases.append(f"Frente a {prev}, la participación {'subió' if d >= 0 else 'bajó'} {_puntos(d)} puntos.")

    no_esp = total["NS"] / total["LN"] * 100 if total["LN"] else 0
    if no_esp >= 10:
        frases.append(f"El {pct(no_esp)} de la lista nominal no se pudo revisar (no especificados): "
                      "toma los porcentajes con cautela.")
    return frases[:5]


def build_report_data(nivel, anio, evol, mun, nacional, judicial, estado=None, clave=None):
    """
    nivel:    "Nacional", "Estado" o "Municipio"
    evol/mun: resúmenes por estado y por municipio (read_evolution / read_municipalities)
    nacional: participación nacional por año (national_series)
    judicial: tabla de la elección judicial por estado (read_data, la del mapa)
    Devuelve un diccionario con todo lo que dibuja report_pdf, o None si no hay datos ese año.
    """
    tipo = "Presidencial" if anio in PRESIDENTIAL_YEARS else "Intermedia"

    if nivel == "Nacional":
        nombre = "México"
        filas = national_year(evol, anio)
        serie, ref_serie, ref_nombre = nacional, None, None
        titulo, subtitulo = "Participación ciudadana en México", f"Elección federal {anio} ({tipo.lower()})"
    elif nivel == "Estado":
        nombre = estado
        filas = state_year(evol, estado, anio)
        serie, ref_serie, ref_nombre = state_series(evol, estado), nacional, "el promedio nacional"
        titulo, subtitulo = f"Participación ciudadana en {estado}", f"Elección federal {anio} ({tipo.lower()})"
    else:
        nombre = municipality_options(mun, estado)[clave]
        filas = municipality_year(mun, estado, clave, anio)
        serie = municipality_series(mun, estado, clave)
        ref_serie, ref_nombre = state_series(evol, estado), estado
        titulo, subtitulo = f"Participación ciudadana en {nombre}", f"{estado} · Elección federal {anio} ({tipo.lower()})"

    total = filas[filas["Dimension"] == "Total"]
    if total.empty or total["pct"].isna().all():
        return None
    total = total.iloc[0]

    sexo = _por(filas, "Sexo", ORDEN_SEXO)
    edad = _por(filas, "Edad", ORDEN_EDAD)
    seccion = _por(filas, "Tipo de sección", ORDEN_SECCION)
    nb = filas[(filas["Dimension"] == "Sexo") & (filas["Categoria"] == "No binario")]
    no_binario_n = int(nb["LN"].iloc[0]) if not nb.empty else None

    # ---- Indicadores (tarjetas de arriba) ----
    kpis = [
        ("Participación", pct(total["pct"]), f"federal {anio}"),
        ("Votaron", num(int(total["SV"])), f"de {num(int(total['SV'] + total['NV']))} revisables"),
        ("Lista nominal", num(int(total["LN"])), f"{num(int(total['NS']))} no especificados"),
    ]

    # ---- Ranking (bloque de abajo a la derecha) ----
    estados_anio = evol[(evol["Anio"] == anio) & (evol["Dimension"] == "Total")].sort_values("pct", ascending=False)
    if nivel == "Nacional":
        jud = judicial["Si votó"].sum() / judicial["Registros totales"].sum() * 100
        kpis.append(("Elección judicial", pct(jud), "2024-2025, nacional"))
        ranking_titulo = f"Estados con mayor y menor participación ({anio})"
        lista = list(zip(estados_anio["Estado"], estados_anio["pct"]))
        ranking = lista[:5] + lista[-5:]
        ranking_completo = lista
        jud_orden = judicial.sort_values("pct", ascending=False)
        extra = {"ranking_judicial": list(zip(jud_orden["Estado"], jud_orden["pct"])),
                 "promedio_judicial": jud, "promedio_federal": float(total["pct"]), "separar_en": 5}
    elif nivel == "Estado":
        j = judicial.set_index("Estado").loc[estado]
        lugar_jud = int((judicial["pct"] > j["pct"]).sum()) + 1
        kpis.append(("Elección judicial", pct(j["pct"]), f"lugar {lugar_jud} de 32"))
        ranking_titulo = f"Municipios con mayor y menor participación ({anio})"
        m = mun[(mun["Estado"] == estado) & (mun["Anio"] == anio) & (mun["Dimension"] == "Total")]
        m = m.dropna(subset=["pct"]).sort_values("pct", ascending=False)
        lista = list(zip(m["MPIONOM"], m["pct"]))
        ranking = lista if len(lista) <= 10 else lista[:5] + lista[-5:]
        ranking_completo = None
        extra = {"separar_en": 5 if len(lista) > 10 else None}
    else:
        m = mun[(mun["Estado"] == estado) & (mun["Anio"] == anio) & (mun["Dimension"] == "Total")]
        m = m.dropna(subset=["pct"]).sort_values("pct", ascending=False).reset_index(drop=True)
        lugar = int(m.index[m["MPIOCVE"] == clave][0]) + 1
        kpis.append(("Lugar en el estado", f"{lugar} de {len(m)}", f"municipios de {estado}"))
        ranking_titulo = f"Municipios de {estado} ({anio})"
        lista = list(zip(m["MPIONOM"], m["pct"]))
        ranking = lista[:3] + ([(nombre, total["pct"])] if lugar > 3 else []) + lista[-3:]
        ranking = list(dict.fromkeys(ranking))          # quita repetidos si el municipio está en el top/bottom
        ranking_completo = None
        extra = {"separar_en": 3 if len(ranking) > 6 else None}

    return {
        "nivel": nivel, "nombre": nombre, "anio": anio, "tipo": tipo,
        "titulo": titulo, "subtitulo": subtitulo,
        "kpis": kpis,
        "serie": serie, "ref_serie": ref_serie,
        "ref_etiqueta": None if ref_serie is None else ("Nacional" if nivel == "Estado" else estado),
        "sexo": sexo, "edad": edad, "seccion": seccion, "no_binario_n": no_binario_n,
        "hallazgos": _hallazgos(nombre, total, sexo, edad, seccion, serie, anio,
                                ref_serie if ref_serie is not None else {}, ref_nombre),
        "ranking_titulo": ranking_titulo, "ranking": ranking, "ranking_completo": ranking_completo,
        # Solo se resalta en el reporte municipal (si no, "Colima" o "México" se confundirían con el estado)
        "resaltar": nombre if nivel == "Municipio" else None,
        **extra,                                      # datos que solo usa un nivel (ver arriba)
    }