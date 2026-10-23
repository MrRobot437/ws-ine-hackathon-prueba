"""
Reporte en PDF con estilo de infografía (una hoja A4; el nacional agrega una segunda con los 32 estados).

Todo se dibuja con figuras de fpdf2 (rectángulos, líneas, círculos y texto), sin convertir las
gráficas de plotly a imagen: así no hace falta Chrome/kaleido y el PDF queda nítido (vectorial).
Medidas en milímetros. Hoja A4 = 210 × 297 mm.
"""

from datetime import date

from fpdf import FPDF

from src.constants import COLORS_MAP
from src.utils import pct

# ================== Estilo ==================

def _rgb(hex_color):
    """'#460BBD' → (70, 11, 189)"""
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


MORADO = _rgb(COLORS_MAP[-1])        # el más oscuro de tu paleta
MORADO_MEDIO = _rgb(COLORS_MAP[3])
MORADO_CLARO = _rgb(COLORS_MAP[0])   # fondo de tarjetas
LILA = _rgb(COLORS_MAP[1])
GRIS_TEXTO = (90, 90, 105)
GRIS_SUAVE = (225, 225, 232)
BLANCO = (255, 255, 255)
NEGRO = (30, 25, 45)

MARGEN = 12
ANCHO = 210 - 2 * MARGEN             # 186 mm de área útil


def _t(texto):
    """Las fuentes básicas del PDF solo tienen caracteres latinos: cambia los que no existen."""
    texto = str(texto).replace("−", "-").replace("–", "-").replace("…", "...")
    return texto.encode("latin-1", "replace").decode("latin-1")


# ================== Piezas reutilizables ==================

class Infografia(FPDF):
    """FPDF con atajos para las piezas que se repiten."""

    def texto(self, x, y, w, contenido, size=9, estilo="", color=NEGRO, align="L", h=None):
        self.set_xy(x, y)
        self.set_font("Helvetica", estilo, size)
        self.set_text_color(*color)
        self.cell(w, h or size * 0.45, _t(contenido), align=align)

    def caja(self, x, y, w, h, color, radio=3):
        self.set_fill_color(*color)
        self.rect(x, y, w, h, style="F", round_corners=True, corner_radius=radio)

    def titulo_seccion(self, x, y, texto):
        self.set_fill_color(*MORADO)
        self.rect(x, y + 0.6, 1.4, 4.2, style="F")
        self.texto(x + 3.5, y, 150, texto, size=10.5, estilo="B", color=MORADO)

    def pie_de_pagina(self):
        self.set_draw_color(*GRIS_SUAVE)
        self.line(MARGEN, 282, MARGEN + ANCHO, 282)
        self.texto(MARGEN, 284, ANCHO,
                   "Participación = Sí votó / (Sí votó + No votó). Los no especificados no entran en el cálculo. "
                   "No incluye casillas especiales ni voto desde el extranjero.", size=6.5, color=GRIS_TEXTO)
        self.texto(MARGEN, 288, ANCHO,
                   f"Fuente: INE, Conteos Censales de Participación Ciudadana · Generado el "
                   f"{date.today().strftime('%d/%m/%Y')}", size=6.5, color=GRIS_TEXTO)


def _encabezado(pdf, datos):
    pdf.set_fill_color(*MORADO)
    pdf.rect(0, 0, 210, 34, style="F")
    pdf.texto(MARGEN, 8, ANCHO, datos["titulo"], size=19, estilo="B", color=BLANCO)
    pdf.texto(MARGEN, 18.5, ANCHO, datos["subtitulo"], size=10.5, color=LILA)
    pdf.texto(MARGEN, 25.5, ANCHO, f"Reporte {datos['nivel'].lower()} · Conteos censales 2009-2024",
              size=8, color=LILA)


def _tarjetas(pdf, y, kpis):
    n = len(kpis)
    hueco = 4
    w = (ANCHO - hueco * (n - 1)) / n
    for i, (etiqueta, valor, nota) in enumerate(kpis):
        x = MARGEN + i * (w + hueco)
        pdf.caja(x, y, w, 26, MORADO_CLARO)
        pdf.texto(x + 4, y + 3.5, w - 8, etiqueta.upper(), size=7, estilo="B", color=MORADO_MEDIO)
        pdf.texto(x + 4, y + 9.5, w - 8, valor, size=17 if len(valor) < 10 else 14, estilo="B", color=MORADO)
        pdf.texto(x + 4, y + 19.5, w - 8, nota, size=7, color=GRIS_TEXTO)


def _grafica_linea(pdf, x, y, w, h, serie, ref_serie, etiqueta, ref_etiqueta, anio):
    """Línea morada del lugar + línea gris punteada de referencia, con los valores en cada punto."""
    anios = list(serie.index)
    valores = [v for v in serie.values if v == v]
    if ref_serie is not None:
        valores += [v for v in ref_serie.values if v == v]
    vmin, vmax = min(valores) - 6, max(valores) + 6

    izq, abajo = x + 10, y + h - 8                  # espacio para las etiquetas de los ejes
    ancho_util, alto_util = w - 14, h - 16

    def px(i):
        return izq + ancho_util * (i / (len(anios) - 1))

    def py(v):
        return abajo - alto_util * (v - vmin) / (vmax - vmin)

    # Líneas guía horizontales con su porcentaje
    pdf.set_draw_color(*GRIS_SUAVE)
    pdf.set_line_width(0.2)
    for k in range(4):
        v = vmin + (vmax - vmin) * k / 3
        pdf.line(izq, py(v), izq + ancho_util, py(v))
        pdf.texto(x, py(v) - 1.5, 9, f"{v:.0f}%", size=6.5, color=GRIS_TEXTO, align="R")

    # Años debajo
    for i, a in enumerate(anios):
        pdf.texto(px(i) - 6, abajo + 2, 12, a, size=7, estilo="B" if a == anio else "",
                  color=MORADO if a == anio else GRIS_TEXTO, align="C")

    # Referencia: gris punteada
    if ref_serie is not None:
        pdf.set_draw_color(150, 150, 160)
        pdf.set_line_width(0.4)
        pdf.set_dash_pattern(dash=1.2, gap=1.2)
        puntos = [(px(anios.index(a)), py(v)) for a, v in ref_serie.items() if a in anios and v == v]
        for (x1, y1), (x2, y2) in zip(puntos, puntos[1:]):
            pdf.line(x1, y1, x2, y2)
        pdf.set_dash_pattern()

    # Lugar: morada gruesa, con círculos y valores
    pdf.set_draw_color(*MORADO)
    pdf.set_line_width(1)
    puntos = [(px(i), py(v), a, v) for i, (a, v) in enumerate(serie.items()) if v == v]
    for (x1, y1, _, _), (x2, y2, _, _) in zip(puntos, puntos[1:]):
        pdf.line(x1, y1, x2, y2)
    pdf.set_line_width(0.6)
    for cx, cy, a, v in puntos:
        r = 1.9 if a == anio else 1.3
        pdf.set_fill_color(*(MORADO if a == anio else BLANCO))
        pdf.ellipse(cx - r, cy - r, 2 * r, 2 * r, style="FD")
        pdf.texto(cx - 8, cy - 6.2, 16, pct(v), size=7, estilo="B" if a == anio else "",
                  color=MORADO if a == anio else GRIS_TEXTO, align="C")

    # Leyenda
    pdf.set_draw_color(*MORADO)
    pdf.set_line_width(1)
    pdf.line(izq, y + 2, izq + 6, y + 2)
    pdf.texto(izq + 7.5, y + 0.4, 60, etiqueta, size=7.5, estilo="B", color=MORADO)
    if ref_serie is not None:
        x2 = izq + 10 + pdf.get_string_width(_t(etiqueta)) + 6
        pdf.set_draw_color(150, 150, 160)
        pdf.set_line_width(0.4)
        pdf.set_dash_pattern(dash=1.2, gap=1.2)
        pdf.line(x2, y + 2, x2 + 6, y + 2)
        pdf.set_dash_pattern()
        pdf.texto(x2 + 7.5, y + 0.4, 60, ref_etiqueta, size=7.5, color=GRIS_TEXTO)


def _barras(pdf, x, y, w, titulo, filas, nota=None):
    """Bloque de barras horizontales (sexo, edad o tipo de sección)."""
    pdf.texto(x, y, w, titulo, size=8.5, estilo="B", color=NEGRO)
    y += 6
    for etiqueta, valor in filas:
        pdf.texto(x, y, 19, etiqueta, size=7.5, color=GRIS_TEXTO)
        riel_x, riel_w = x + 19, w - 33
        pdf.caja(riel_x, y + 0.6, riel_w, 3, GRIS_SUAVE, radio=1.5)
        pdf.caja(riel_x, y + 0.6, max(riel_w * valor / 100, 1.5), 3, MORADO, radio=1.5)
        pdf.texto(riel_x + riel_w + 1, y, 13, pct(valor), size=7.5, estilo="B", color=NEGRO, align="R")
        y += 6.5
    if nota:
        pdf.texto(x, y, w, nota, size=6.5, color=GRIS_TEXTO)


def _hallazgos(pdf, x, y, w, frases, alto_min=0):
    """Caja "Lo más importante". Mide primero el texto para que la caja quede a la medida."""
    pdf.set_font("Helvetica", "", 8.3)
    alturas = [pdf.multi_cell(w - 14, 4.2, _t(f), dry_run=True, output="HEIGHT") for f in frases]
    alto = max(11 + sum(alturas) + 1.8 * len(frases) + 3, alto_min)
    pdf.caja(x, y, w, alto, MORADO_CLARO)
    pdf.texto(x + 5, y + 4, w - 10, "Lo más importante", size=10, estilo="B", color=MORADO)
    pdf.set_y(y + 11)
    for frase in frases:
        pdf.set_fill_color(*MORADO)
        pdf.ellipse(x + 5, pdf.get_y() + 1.4, 1.6, 1.6, style="F")
        pdf.set_x(x + 9)
        pdf.set_font("Helvetica", "", 8.3)
        pdf.set_text_color(*NEGRO)
        pdf.multi_cell(w - 14, 4.2, _t(frase))
        pdf.ln(1.8)
    return alto


def _ranking(pdf, x, y, w, titulo, filas, resaltar, corte=None, separar_en=None, tope=None):
    """
    Lista con barra: nombre · barra · %. El lugar del reporte va resaltado.
    corte:      barras con valor >= corte van en morado oscuro; las demás en lila.
                Si es None, la primera mitad va oscura (los más altos) y la segunda lila (los más bajos).
    separar_en: deja un pequeño espacio antes de esa posición (separa "más altos" de "más bajos").
    tope:       valor que equivale a la barra completa. Si dos columnas comparten tope, sus barras se comparan bien.
    Devuelve la altura usada.
    """
    pdf.texto(x, y, w, titulo, size=8.5, estilo="B", color=NEGRO)
    y0 = y
    y += 6.5
    tope = tope or (max(v for _, v in filas) if filas else 100)
    for i, (nombre, valor) in enumerate(filas):
        if separar_en is not None and i == separar_en:
            pdf.texto(x, y - 1.2, 30, "· · ·", size=7, color=GRIS_TEXTO)
            y += 3
        es_el_lugar = nombre == resaltar
        alto = valor >= corte if corte is not None else i < len(filas) / 2
        color = MORADO if (es_el_lugar or alto) else LILA
        pdf.texto(x, y, 30, nombre[:22], size=7, estilo="B" if es_el_lugar else "",
                  color=MORADO if es_el_lugar else GRIS_TEXTO)
        riel_x, riel_w = x + 31, w - 45
        pdf.caja(riel_x, y + 0.7, max(riel_w * valor / tope, 1.5), 2.6, color, radio=1.3)
        pdf.texto(riel_x + riel_w + 1, y, 13, pct(valor), size=7, estilo="B", color=NEGRO, align="R")
        y += 5.4
    return y - y0


# ================== Armado de la página ==================

def build_pdf(datos):
    """Recibe el diccionario de report_data.build_report_data y devuelve el PDF en bytes."""
    pdf = Infografia(format="A4")
    pdf.set_auto_page_break(False)
    pdf.add_page()

    _encabezado(pdf, datos)
    _tarjetas(pdf, 40, datos["kpis"])

    # Evolución
    pdf.titulo_seccion(MARGEN, 73, "Evolución de la participación 2009-2024")
    _grafica_linea(pdf, MARGEN, 81, ANCHO, 62, datos["serie"], datos["ref_serie"],
                   datos["nombre"], datos["ref_etiqueta"], datos["anio"])

    # Desgloses en tres columnas
    pdf.titulo_seccion(MARGEN, 150, f"¿Quién votó en {datos['anio']}?")
    col = (ANCHO - 8) / 3
    nota_nb = (f"No binario: {datos['no_binario_n']} personas en la lista nominal"
               if datos["no_binario_n"] else None)
    _barras(pdf, MARGEN, 158, col, "Por sexo", datos["sexo"], nota_nb)
    _barras(pdf, MARGEN + col + 4, 158, col, "Por edad", datos["edad"])
    _barras(pdf, MARGEN + 2 * (col + 4), 158, col, "Por tipo de sección", datos["seccion"])
    pdf.texto(MARGEN, 186.5, ANCHO, "Cada barra es la participación dentro de su grupo: por eso no suman 100%.",
              size=6.5, color=GRIS_TEXTO)

    # Hallazgos (izquierda) y ranking (derecha)
    alto_ranking = _ranking(pdf, MARGEN + 110, 196, ANCHO - 110, datos["ranking_titulo"], datos["ranking"],
                            datos["resaltar"], separar_en=datos.get("separar_en"))
    _hallazgos(pdf, MARGEN, 194, 104, datos["hallazgos"], alto_min=alto_ranking + 4)

    pdf.pie_de_pagina()

    # Nacional: segunda hoja con los 32 estados (federal y judicial)
    if datos["ranking_completo"]:
        pdf.add_page()
        pdf.set_fill_color(*MORADO)
        pdf.rect(0, 0, 210, 20, style="F")
        pdf.texto(MARGEN, 6.5, ANCHO, "Participación por estado", size=14, estilo="B", color=BLANCO)

        def dos_columnas(y, titulo, lista, promedio):
            pdf.titulo_seccion(MARGEN, y, titulo)
            pdf.texto(MARGEN + 3.5, y + 6, ANCHO, f"Morado: arriba del promedio nacional ({pct(promedio)}) · "
                      "Lila: abajo del promedio", size=7, color=GRIS_TEXTO)
            mitad = (len(lista) + 1) // 2
            tope = max(v for _, v in lista)          # misma escala en las dos columnas
            _ranking(pdf, MARGEN, y + 12, ANCHO / 2 - 4, f"Lugares 1 a {mitad}", lista[:mitad], None,
                     corte=promedio, tope=tope)
            _ranking(pdf, MARGEN + ANCHO / 2 + 4, y + 12, ANCHO / 2 - 4, f"Lugares {mitad + 1} a {len(lista)}",
                     lista[mitad:], None, corte=promedio, tope=tope)

        dos_columnas(28, f"Elección federal {datos['anio']}", datos["ranking_completo"], datos["promedio_federal"])
        dos_columnas(150, "Elección judicial 2024-2025", datos["ranking_judicial"], datos["promedio_judicial"])
        pdf.pie_de_pagina()

    return bytes(pdf.output())