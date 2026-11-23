# -*- coding: utf-8 -*-
"""
Generador único (una sola fuente de geometría) para:
  - Plano_Puente_Fase4.scr  (script AutoCAD)
  - Plano_Puente_Fase4.dxf  (DXF R12 editable)
  - Plano_Puente_Fase4.pdf  (lámina A3 de revisión)
Todas las coordenadas de Model Space están en milímetros a tamaño real.
"""
import math, random, json, sys, os

OUT = sys.argv[1] if len(sys.argv) > 1 else "out"
os.makedirs(OUT, exist_ok=True)
NAME = "Plano_Puente_Fase4"

# ------------------------------------------------------------------ datos
D_COL = 1200.0          # diámetro columna
H_COL = 7000.0          # altura libre
S_EJES = 6000.0         # separación entre ejes
L_CAB = 9600.0          # longitud cabezal
H_CAB = 1500.0          # peralte cabezal
VOL = 1800.0            # voladizo (eje-extremo)
N_BAR = 26
DB = 43.0               # No. 14
DH = 25.4               # No. 8
REC = 50.8              # recubrimiento libre
S_ARO = 127.0
LP = 851.0
L_CONF = 1800.0

R_COL = D_COL / 2                       # 600
R_ARO_EXT = R_COL - REC                 # 549.2  cara exterior del aro
R_ARO_INT = R_ARO_EXT - DH              # 523.8  cara interior del aro
R_ARO_EJE = R_ARO_EXT - DH / 2          # 536.5  eje del aro  (Ø 1073.0)
R_BAR = R_ARO_INT - DB / 2              # 502.3  eje de barras (barras tangentes al aro)
THETA = 360.0 / N_BAR                   # 13.846°
BAR_ANG = [90.0 + k * THETA for k in range(N_BAR)]

# distribución de aros @127 simétrica en la altura libre
N_ESP = int((H_COL) // S_ARO)           # 55 espacios caben? -> se ajusta abajo
N_ESP = int(math.floor((H_COL - 2 * 50) / S_ARO))   # 54 espacios
Y0_ARO = (H_COL - N_ESP * S_ARO) / 2.0               # 71.0
ARO_Y = [Y0_ARO + k * S_ARO for k in range(N_ESP + 1)]  # 55 aros

# ------------------------------------------------------------------ anotación
TXT = 2.0      # altura texto impreso (mm papel)
ASZ = 2.0      # flecha
EXO = 1.0
EXE = 1.25
GAP = 0.625

LAYERS = [  # nombre, color ACI, tipo de línea, grosor
    ("ESTRUCTURA", 7, "CONTINUOUS", 0.50),
    ("REF_LONGITUDINAL", 1, "CONTINUOUS", 0.35),
    ("REF_TRANSVERSAL", 3, "CONTINUOUS", 0.30),
    ("EJES", 4, "CENTER", 0.18),
    ("COTAS", 2, "CONTINUOUS", 0.18),
    ("TEXTOS", 7, "CONTINUOUS", 0.25),
    ("CONFINAMIENTO", 6, "DASHED", 0.35),
    ("HATCH_CONCRETO", 8, "CONTINUOUS", 0.13),
    ("MARCO_PLANO", 7, "CONTINUOUS", 0.50),
    ("VIEWPORTS", 9, "CONTINUOUS", 0.13),
]
LAYER = {l[0]: l for l in LAYERS}
# patrones acadiso.lin (mm) ; LTSCALE 0.25 con PSLTSCALE 1
LTYPES = {
    "CENTER": [31.75, -6.35, 6.35, -6.35],
    "DASHED": [12.7, -6.35],
    "PHANTOM": [31.75, -6.35, 6.35, -6.35, 6.35, -6.35],
}
LTSCALE = 0.25

# ------------------------------------------------------------------ modelo de entidades
ENTS = []          # en orden de creación
VPORTS = []        # (rect papel x1,y1,x2,y2 ; centro modelo ; escala)


class Ctx:
    space = "M"
    sc = 1.0      # factor anotación (=denominador de escala) en Model


def add(t, layer, **k):
    e = dict(t=t, layer=layer, sp=Ctx.space, sc=Ctx.sc)
    e.update(k)
    ENTS.append(e)
    return e


def line(p1, p2, layer, lt=None, lw=None):
    return add("line", layer, p1=p1, p2=p2, lt=lt, lw=lw)


def pline(pts, layer, closed=False, widths=None, lt=None, lw=None):
    return add("pline", layer, pts=pts, closed=closed, widths=widths, lt=lt, lw=lw)


def rect(x1, y1, x2, y2, layer, **k):
    return pline([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], layer, closed=True, **k)


def circle(c, r, layer, lt=None, lw=None):
    return add("circle", layer, c=c, r=r, lt=lt, lw=lw)


def arc(c, r, a1, a2, layer, lt=None, lw=None):
    return add("arc", layer, c=c, r=r, a1=a1, a2=a2, lt=lt, lw=lw)


def donut(c, din, dout, layer):
    return add("donut", layer, c=c, din=din, dout=dout)


def text(p, h, s, layer="TEXTOS", rot=0.0, j="BL"):
    """j: 2 letras  vertical(B=base,M,T) + horizontal(L,C,R) -> 'BL','MC','TR'..."""
    return add("text", layer, p=p, h=h, s=s, rot=rot, j=j)


def hatch_circle(c, r, layer_b, layer_h, pattern="AR-CONC", scale=0.5):
    return add("hatchcircle", layer_h, c=c, r=r, layer_b=layer_b, pattern=pattern, hscale=scale)


def dim(p1, p2, loc, orient, txt=None, tpos=None):
    if orient == "H":
        loc = ((p1[0] + p2[0]) / 2, loc[1])
    else:
        loc = (loc[0], (p1[1] + p2[1]) / 2)
    return add("dim", "COTAS", p1=p1, p2=p2, loc=loc, orient=orient, txt=txt, tpos=tpos)


def leader(tip, pts, layer="TEXTOS"):
    """tip = punta de flecha; pts = puntos siguientes (codo, aterrizaje)."""
    a = ASZ * Ctx.sc
    p1 = pts[0]
    L = math.hypot(p1[0] - tip[0], p1[1] - tip[1])
    ux, uy = (p1[0] - tip[0]) / L, (p1[1] - tip[1]) / L
    base = (tip[0] + ux * a, tip[1] + uy * a)
    allp = [tip, base] + list(pts)
    widths = [(0.0, a / 3.0)] + [(0.0, 0.0)] * (len(allp) - 2)
    return pline(allp, layer, widths=widths)


def label(tip, elbow, lines, side, h=None, layer="TEXTOS", dy=None):
    """llamada: flecha -> codo -> aterrizaje horizontal + bloque de texto."""
    h = h or TXT * Ctx.sc
    dy = dy or 1.6 * h
    land = 2.0 * Ctx.sc
    x_end = elbow[0] + (land if side == "R" else -land)
    leader(tip, [elbow, (x_end, elbow[1])], layer)
    n = len(lines)
    ytop = elbow[1] + (n - 1) * dy / 2.0
    xt = x_end + (0.8 * Ctx.sc if side == "R" else -0.8 * Ctx.sc)
    for i, s in enumerate(lines):
        text((xt, ytop - i * dy), h, s, layer, j="M" + ("L" if side == "R" else "R"))


def fmt(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def P(p):
    return f"{fmt(p[0])},{fmt(p[1])}"

# =========================================================================
#  MODEL SPACE
# =========================================================================
# ---------------- 1) ELEVACIÓN (origen: eje del marco, base de columnas) 1:50
Ctx.space, Ctx.sc = "M", 50.0
sc = Ctx.sc
xa, xb = -S_EJES / 2, S_EJES / 2
xc1, xc2 = -L_CAB / 2, L_CAB / 2
ytop = H_COL + H_CAB
# cabezal
rect(xc1, H_COL, xc2, ytop, "ESTRUCTURA")
# columnas
for xe in (xa, xb):
    rect(xe - R_COL, 0, xe + R_COL, H_COL, "ESTRUCTURA")
    # proyección de la columna dentro del cabezal (nudo) - oculta
    line((xe - R_COL, H_COL), (xe - R_COL, ytop), "ESTRUCTURA", lt="DASHED", lw=0.18)
    line((xe + R_COL, H_COL), (xe + R_COL, ytop), "ESTRUCTURA", lt="DASHED", lw=0.18)
    # barras extremas (proyección) prolongadas en el cabezal - esquemático
    for s_ in (-1, 1):
        xbx = xe + s_ * R_BAR * math.cos(math.radians(THETA / 2))
        line((xbx, 0), (xbx, ytop - 150), "REF_LONGITUDINAL")
    # base / apoyo: línea de cara superior de cimentación + achurado de apoyo
    line((xe - 1100, 0), (xe + 1100, 0), "ESTRUCTURA")
    x = xe - 1100
    while x <= xe + 1100 - 150 + 1e-6:
        line((x + 150, 0), (x, -150), "ESTRUCTURA", lw=0.18)
        x += 200
    # eje
    line((xe, -650), (xe, ytop + 300), "EJES")
    circle((xe, -850), 200, "EJES", lt="CONTINUOUS", lw=0.25)
    text((xe, -850), 2.5 * sc, "A" if xe < 0 else "B", j="MC")
    # límites de zonas confinadas en elevación
    for yz in (L_CONF, H_COL - L_CONF):
        line((xe - R_COL - 200, yz), (xe + R_COL + 200, yz), "CONFINAMIENTO")
# corte 1-1 (columna izquierda, h = 3500)
yc = 3500
for xs, sgn in ((xa - R_COL - 350, 1), (xa + R_COL + 350, -1)):
    pline([(xs, yc), (xs + sgn * 250, yc)], "TEXTOS", widths=[(25, 25)])
    leader((xs, yc - 300), [(xs, yc)], "TEXTOS")
    text((xs - sgn * 150, yc - 220), 2.5 * sc, "1", j="MC")
# textos de elevación
text((0, H_COL + H_CAB / 2 + 120), TXT * sc * 1.15, "VIGA CABEZAL 1500 x 1500 mm  (L = 9600 mm)", j="MC")
text((0, H_COL + H_CAB / 2 - 200), TXT * sc, "NUDO COLUMNA-CABEZAL MONOLÍTICO (ESQUEMÁTICO)", j="MC")
label((xa + R_COL, 4300), (xa + R_COL + 700, 4300),
      ["COLUMNA %%c 1,200 mm (TÍP.)", "ALTURA LIBRE 7000 mm"], "R")
label((xb - R_COL, 1800), (xb - R_COL - 700, 2500),
      ["LÍMITE ZONA DE CONFINAMIENTO", "ESPECIAL 1800 mm (TÍP.)"], "L")
xbar = xa + R_BAR * math.cos(math.radians(THETA / 2))
label((xbar, 7700), (xa + R_COL + 700, 6300),
      ["26 VARILLAS No. 14 PROLONGADAS EN EL", "CABEZAL (ANCLAJE SEGÚN DISEÑO; ESQUEMÁTICO)"], "R")
text((0, -330), TXT * sc, "BASE DE COLUMNAS: CARA SUPERIOR DE CIMENTACIÓN", j="MC")
text((0, -580), TXT * sc, "(DIMENSIONES DE ZAPATA SEGÚN PLANO DE CIMENTACIÓN)", j="MC")
# cotas horizontales
yd1, yd2 = ytop + 500, ytop + 950
dim((xc1, ytop), (xa, ytop), (0, yd1), "H")
dim((xa, ytop), (xb, ytop), (0, yd1), "H")
dim((xb, ytop), (xc2, ytop), (0, yd1), "H")
dim((xc1, ytop), (xc2, ytop), (0, yd2), "H")
# cotas verticales (izquierda)
xl1, xl2 = xc1 - 450, xc1 - 900
dim((xa - R_COL, 0), (xc1, H_COL), (xl1, 0), "V")
dim((xc1, H_COL), (xc1, ytop), (xl1, 0), "V")
dim((xa - R_COL, 0), (xc1, ytop), (xl2, 0), "V")
# cotas verticales de zonas (derecha, bajo el voladizo)
xr = xb + R_COL + 700
dim((xb + R_COL, 0), (xb + R_COL, L_CONF), (xr, 0), "V")
dim((xb + R_COL, L_CONF), (xb + R_COL, H_COL - L_CONF), (xr, 0), "V")
dim((xb + R_COL, H_COL - L_CONF), (xb + R_COL, H_COL), (xr, 0), "V")
# cota de diámetro de columna (bajo la base, columna derecha)
dim((xb - R_COL, 0), (xb + R_COL, 0), (0, -330), "H")
VPORTS.append(dict(rect=(16, 66, 234, 286), c=(-425, 4125), s=50.0, name="ELEVACION"))

# ---------------- 2) SECCIÓN 1-1  1:10   centro (20000,0)
Ctx.sc = 10.0
sc = Ctx.sc
CX, CY = 20000.0, 0.0
hatch_circle((CX, CY), R_COL, "ESTRUCTURA", "HATCH_CONCRETO", "AR-CONC", 0.5)
donut((CX, CY), 2 * R_ARO_INT, 2 * R_ARO_EXT, "REF_TRANSVERSAL")
circle((CX, CY), R_BAR, "EJES")
line((CX - 690, CY), (CX + 690, CY), "EJES")
line((CX, CY - 640), (CX, CY + 640), "EJES")
BARS = []
for a in BAR_ANG:
    p = (CX + R_BAR * math.cos(math.radians(a)), CY + R_BAR * math.sin(math.radians(a)))
    BARS.append(p)
for p in BARS:
    donut(p, 0, DB, "REF_LONGITUDINAL")
# separación angular
a1, a2 = 90.0 - THETA, 90.0
for a in (a1, a2):
    line((CX, CY), (CX + 470 * math.cos(math.radians(a)), CY + 470 * math.sin(math.radians(a))), "EJES",
         lt="CONTINUOUS", lw=0.13)
arc((CX, CY), 300, a1, a2, "COTAS")
am = math.radians((a1 + a2) / 2)
text((CX + 345 * math.cos(am), CY + 345 * math.sin(am)), TXT * sc, "θ", "COTAS", j="MC")
# recubrimiento (cota horizontal a 180°)
dim((CX - R_COL, CY), (CX - R_ARO_EXT, CY), (CX, CY - 45), "H", txt="50.8",
    tpos=(CX - R_COL - 75, CY - 45 + GAP * sc + TXT * sc / 2))
# llamadas
pc = (CX + R_COL * math.cos(math.radians(145)), CY + R_COL * math.sin(math.radians(145)))
label(pc, (CX - 560, CY + 380), ["COLUMNA", "%%c 1,200 mm"], "L")
pr = (CX + (R_COL + R_ARO_EXT) / 2 * math.cos(math.radians(205)),
      CY + (R_COL + R_ARO_EXT) / 2 * math.sin(math.radians(205)))
label(pr, (CX - 400, CY - 560), ["RECUBRIMIENTO", "LIBRE 50.8 mm"], "L")
pb = BARS[23]   # barra a 90+23*13.846 = 408.46 -> 48.46°
label(pb, (CX + 470, CY + 420), ["26 VARILLAS", "No. 14 (%%c 43 mm)", "θ = 360%%d/26", "= 13.846%%d"], "R")
ph = (CX + R_ARO_EJE * math.cos(math.radians(-35)), CY + R_ARO_EJE * math.sin(math.radians(-35)))
label(ph, (CX + 470, CY - 430), ["ARO CIRCULAR", "No. 8 (%%c 25.4 mm)", "%%c EJE A EJE", "1,073.0 mm"], "R")
VPORTS.append(dict(rect=(236, 156, 409, 286), c=(CX + 0, CY + 0), s=10.0, name="SECCION"))

# ---------------- 3) DETALLE LONGITUDINAL 1:100   centro x0=30000
Ctx.sc = 100.0
sc = Ctx.sc
X0 = 30000.0
line((X0 - R_COL, 0), (X0 - R_COL, H_COL), "ESTRUCTURA")
line((X0 + R_COL, 0), (X0 + R_COL, H_COL), "ESTRUCTURA")
for yf in (0, H_COL):
    line((X0 - 1000, yf), (X0 + 1000, yf), "ESTRUCTURA")
text((X0, -170), TXT * sc, "CARA SUPERIOR DE CIMENTACIÓN", j="TC")
text((X0, H_COL + 170), TXT * sc, "CARA INFERIOR DEL CABEZAL", j="BC")
xbp = R_BAR * math.cos(math.radians(THETA / 2))
for dx in (-xbp, 0.0, xbp):
    line((X0 + dx, 0), (X0 + dx, H_COL), "REF_LONGITUDINAL")
for y in ARO_Y:
    pline([(X0 - R_ARO_EJE, y), (X0 + R_ARO_EJE, y)], "REF_TRANSVERSAL", widths=[(DH, DH)])
for yz in (L_CONF, H_COL - L_CONF):
    line((X0 - 900, yz), (X0 + 900, yz), "CONFINAMIENTO")
for yl in (LP, H_COL - LP):
    line((X0 - 1250, yl), (X0 + R_COL, yl), "CONFINAMIENTO", lt="PHANTOM", lw=0.25)
# cotas
xr1, xr2 = X0 + 1100, X0 + 1600
dim((X0 + R_COL, 0), (X0 + R_COL, L_CONF), (xr1, 0), "V")
dim((X0 + R_COL, L_CONF), (X0 + R_COL, H_COL - L_CONF), (xr1, 0), "V")
dim((X0 + R_COL, H_COL - L_CONF), (X0 + R_COL, H_COL), (xr1, 0), "V")
dim((X0 + R_COL, 0), (X0 + R_COL, H_COL), (xr2, 0), "V")
xl = X0 - 1050
dim((X0 - 1250, 0), (X0 - 1250, LP), (xl, 0), "V")
dim((X0 - 1250, H_COL - LP), (X0 - 1250, H_COL), (xl, 0), "V")
text((X0 - 1450, LP / 2), TXT * sc, "Lp", rot=90, j="MC")
text((X0 - 1450, H_COL - LP / 2), TXT * sc, "Lp", rot=90, j="MC")
# zonas
xt = X0 + 1950
def block(y, lines_, h=TXT * sc):
    n = len(lines_)
    for i, s in enumerate(lines_):
        text((xt, y + (n - 1) * 0.8 * h - i * 1.6 * h), h, s, j="ML")
block(900, ["ZONA DE CONFINAMIENTO", "ESPECIAL INFERIOR", "0 - 1800", "AROS No. 8 @ 127"])
block(3500, ["ZONA CENTRAL", "1800 - 5200", "AROS No. 8 @ 127", "(NO SE DEFINE OTRO", "ESPACIAMIENTO)"])
block(6150, ["ZONA DE CONFINAMIENTO", "ESPECIAL SUPERIOR", "5200 - 7000", "AROS No. 8 @ 127"])
# leyenda
yl1, yl2 = 2350, 1950
line((xt, yl1), (xt + 500, yl1), "CONFINAMIENTO")
text((xt + 600, yl1), 0.9 * TXT * sc, "LÍM. ZONA CONFINADA", j="ML")
line((xt, yl2), (xt + 500, yl2), "CONFINAMIENTO", lt="PHANTOM", lw=0.25)
text((xt + 600, yl2), 0.9 * TXT * sc, "Lp ANALÍTICA = 851", j="ML")
for i_, s_ in enumerate(["55 AROS No. 8 @ 127 (CROQUIS):", "1er ARO A 71 mm DE CADA CARA",
                         "SE MUESTRAN 3 DE 26 VARILLAS"]):
    text((xt, 5180 - i_ * 290), 0.9 * TXT * sc, s_, j="ML")
# llamada detalle A
rect(X0 - 800, -100, X0 + 800, 1100, "TEXTOS", lt="DASHED", lw=0.18)
circle((X0 - 750, 1250), 140, "TEXTOS", lw=0.25)
text((X0 - 750, 1250), 2.0 * sc, "A", j="MC")
VPORTS.append(dict(rect=(236, 56, 322, 143), c=(X0 + 1700, 3500), s=100.0, name="DETALLE"))

# ---------------- 4) DETALLE A 1:25  centro X1=45000
Ctx.sc = 25.0
sc = Ctx.sc
X1 = 45000.0
# quiebre cilíndrico (dos arcos)
sag = 80.0
rb = (300 ** 2 + sag ** 2) / (2 * sag)
YB = 1000.0
cb1 = (X1 - 300, YB + sag - rb)
cb2 = (X1 + 300, YB - sag + rb)
ang0 = math.degrees(math.atan2(YB - cb1[1], 300))
arc(cb1, rb, ang0, 180 - ang0, "ESTRUCTURA")
arc(cb2, rb, 180 + ang0, 360 - ang0, "ESTRUCTURA")


def y_break(x):
    dx = x - X1
    if dx <= 0:
        return cb1[1] + math.sqrt(rb ** 2 - (dx + 300) ** 2)
    return cb2[1] - math.sqrt(rb ** 2 - (dx - 300) ** 2)


line((X1 - R_COL, 0), (X1 - R_COL, YB), "ESTRUCTURA")
line((X1 + R_COL, 0), (X1 + R_COL, YB), "ESTRUCTURA")
line((X1 - 850, 0), (X1 + 850, 0), "ESTRUCTURA")
text((X1, -45), TXT * sc, "CARA SUPERIOR DE CIMENTACIÓN", j="TC")
for dx in (-xbp, 0.0, xbp):
    line((X1 + dx, 0), (X1 + dx, y_break(X1 + dx)), "REF_LONGITUDINAL")
ARO_A = [y for y in ARO_Y if y < 900]
for y in ARO_A:
    pline([(X1 - R_ARO_EJE, y), (X1 + R_ARO_EJE, y)], "REF_TRANSVERSAL", widths=[(DH, DH)])
line((X1 - 850, LP), (X1 + R_COL, LP), "CONFINAMIENTO", lt="PHANTOM", lw=0.25)
# cotas
xr = X1 + 850
dim((X1 + R_COL, 0), (X1 + R_COL, ARO_A[0]), (xr, 0), "V", tpos=(xr - GAP * sc - TXT * sc / 2, -95))
dim((X1 + R_COL, ARO_A[0]), (X1 + R_COL, ARO_A[-1]), (xr, 0), "V",
    txt=f"{len(ARO_A) - 1} @ 127 = {int((len(ARO_A) - 1) * 127)}")
dim((X1 - 850, 0), (X1 - 850, LP), (X1 - 850, 0), "V", txt="Lp = 851")
yc = (ARO_A[5] + ARO_A[6]) / 2
dim((X1 + R_ARO_EXT, yc), (X1 + R_COL, yc), (0, yc), "H", txt="50.8",
    tpos=(X1 + R_COL + 110, yc + GAP * sc + TXT * sc / 2))
# llamadas
def label_up(tip, xt, yb, lines_):
    h = TXT * sc
    leader(tip, [(xt, yb), (xt + 2 * sc, yb)])
    n = len(lines_)
    for i, s_ in enumerate(lines_):
        text((xt + 0.5 * sc, yb + 0.8 * sc + (n - 1 - i) * 1.6 * h), h, s_, j="BL")
label_up((X1 - 380, ARO_A[5]), X1 - 1060, 1230, ["AROS CIRCULARES", "No. 8 @ 127 mm"])
label_up((X1, 420), X1 - 330, 1230, ["VARILLA No. 14", "(26 EN TOTAL)"])
label_up((X1 + 380, LP), X1 + 380, 1230, ["LÍNEA Lp = 851", "(≠ ZONA CONF.)"])
VPORTS.append(dict(rect=(323, 56, 409, 143), c=(X1 - 50, 737.5), s=25.0, name="DETALLE_A"))

# =========================================================================
#  PAPER SPACE (lámina A3 420 x 297)
# =========================================================================
Ctx.space, Ctx.sc = "P", 1.0
UL = []
rect(0, 0, 420, 297, "MARCO_PLANO", lw=0.13)
rect(15, 10, 410, 287, "MARCO_PLANO", lw=0.70)
line((15, 55), (410, 55), "MARCO_PLANO", lw=0.50)
line((235, 55), (235, 287), "MARCO_PLANO", lw=0.25)
line((235, 155), (410, 155), "MARCO_PLANO", lw=0.25)
# títulos de vistas
text((125, 60.2), 3.0, "ELEVACIÓN PRINCIPAL DEL MARCO - PILA INTERMEDIA", j="BC")
UL.append(((125, 59.2), 3.0, "ELEVACIÓN PRINCIPAL DEL MARCO - PILA INTERMEDIA", "C"))
text((125, 56.6), 2.0, "ESC. 1:50", j="BC")
text((239, 281), 3.5, "SECCIÓN 1-1", j="BL")
UL.append(((239, 280), 3.5, "SECCIÓN 1-1", "L"))
text((239, 276), 2.0, "COLUMNA TÍPICA (EJES A Y B)", j="BL")
text((239, 272.6), 2.0, "ESC. 1:10", j="BL")
text((238, 150.5), 3.0, "DETALLE LONGITUDINAL - REFUERZO TRANSVERSAL Y CONFINAMIENTO", j="BL")
UL.append(((238, 149.5), 3.0, "DETALLE LONGITUDINAL - REFUERZO TRANSVERSAL Y CONFINAMIENTO", "L"))
text((238, 145.3), 2.0, "COLUMNA TÍPICA, ALTURA LIBRE 7000 mm - ESC. 1:100", j="BL")
text((325, 145.3), 2.0, "DETALLE A (BASE DE COLUMNA) - ESC. 1:25", j="BL")
line((322.5, 56), (322.5, 147.5), "MARCO_PLANO", lw=0.13)
# notas
text((18, 50.6), 2.5, "ESPECIFICACIONES Y NOTAS", j="BL")
UL.append(((18, 49.6), 2.5, "ESPECIFICACIONES Y NOTAS", "L"))
NOTAS = [
    "1. COTAS EN MILÍMETROS. GEOMETRÍA DE MODEL SPACE A TAMAÑO REAL; ESCALAS DE IMPRESIÓN EN LAS VENTANAS DE PRESENTACIÓN.",
    "2. PUENTE DE 3 TRAMOS 22.50 + 30.00 + 22.50 = 75.00 m; ANCHO DE SUPERESTRUCTURA 9.60 m; 4 VIGAS AASHTO TIPO IV.",
    "3. MARCO: 2 COLUMNAS %%c 1200 mm, ALTURA LIBRE 7000 mm, EJES A 6000 mm; CABEZAL 1500 x 1500 mm, L = 9600 mm, VOLADIZOS 1800 mm.",
    "4. REFUERZO LONGITUDINAL: 26 VARILLAS No. 14 (%%c 43 mm) EN DISTRIBUCIÓN POLAR, 360%%d/26 = 13.846%%d, R EJE BARRAS = 502.3 mm.",
    "5. REFUERZO TRANSVERSAL: AROS CIRCULARES No. 8 (%%c 25.4 mm) @ 127 mm (5 in); %%c EJE A EJE DEL ARO = 1073.0 mm.",
    "6. RECUBRIMIENTO LIBRE AL ARO: 50.8 mm. ZONA DE CONFINAMIENTO ESPECIAL: 1800 mm EN CADA EXTREMO DE LA COLUMNA.",
    "7. Lp ANALÍTICA (RÓTULA PLÁSTICA) = 851 mm: DATO DEL MODELO; NO ES LA LONGITUD DE CONFINAMIENTO (1800 mm).",
    "8. NO SE DEFINEN EN ESTA LÁMINA: ZAPATAS, ANCLAJES, TRASLAPES, GANCHOS NI MATERIALES (f'c, fy).",
    "9. DETALLADO ACADÉMICO DEL MODELO UTILIZADO. NO CONSTITUYE DECLARACIÓN DE CUMPLIMIENTO DE DISEÑO NI NORMATIVO.",
]
for i, s in enumerate(NOTAS):
    text((18, 45.6 - i * 3.75), 1.8, s, j="BL")
# cajetín
line((230, 10), (230, 55), "MARCO_PLANO", lw=0.50)
line((370, 10), (370, 55), "MARCO_PLANO", lw=0.50)
line((230, 39), (370, 39), "MARCO_PLANO", lw=0.25)
line((230, 30), (370, 30), "MARCO_PLANO", lw=0.25)
line((230, 21), (370, 21), "MARCO_PLANO", lw=0.25)
for xv in (262, 318, 342):
    line((xv, 10), (xv, 21), "MARCO_PLANO", lw=0.25)
line((370, 22), (410, 22), "MARCO_PLANO", lw=0.25)
text((300, 48.8), 3.2, "DETALLADO ESTRUCTURAL DE PILA INTERMEDIA", j="MC")
text((300, 43.2), 3.0, "PUENTE DE CONCRETO REFORZADO", j="MC")
def cell(x, y, lab, val, hv=1.8):
    text((x + 1.5, y - 2.6), 1.4, lab, j="BL")
    text((x + 1.5, y - 6.6), hv, val, j="BL")
cell(230, 39, "PROYECTO", "SUBESTRUCTURA - PUENTE DE 3 TRAMOS (22.50 + 30.00 + 22.50 m)")
cell(230, 30, "CONTENIDO", "ELEVACIÓN, SECCIÓN DE COLUMNA Y DETALLADO SÍSMICO")
cell(230, 21, "UNIDADES", "MILÍMETROS")
cell(262, 21, "ESCALAS", "1:50 / 1:10 / 1:100 / 1:25")
cell(318, 21, "FORMATO", "A3 (420x297)")
cell(342, 21, "FECHA", "2026-11-22")
text((372, 51.5), 1.4, "CÓDIGO", j="BL")
text((390, 36), 9.0, "E-01", j="MC")
text((372, 18.4), 1.4, "LÁMINA", j="BL")
text((390, 13.2), 3.0, "1 / 1", j="MC")

# =========================================================================
#  EMULACIÓN DE ENTIDADES COMPUESTAS (para DXF y PDF)
# =========================================================================
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
FP = FontProperties(family="Liberation Sans")
CAP = 0.716   # altura de mayúsculas / em (Arial)


def pretty(s):
    return s.replace("%%c", "Ø").replace("%%d", "°").replace("%%p", "±")


def text_w(s, h):
    tp = TextPath((0, 0), pretty(s), size=h / CAP, prop=FP)
    ext = tp.get_extents()
    return ext.width if len(s.strip()) else 0.0


def dim_prims(e):
    """devuelve primitivas: ('line',p1,p2) ('tri',a,b,c) ('text',p,h,s,rot,j)."""
    s = e["sc"]
    exo, exe, asz, gap, th = EXO * s, EXE * s, ASZ * s, GAP * s, TXT * s
    p1, p2, loc = e["p1"], e["p2"], e["loc"]
    out = []
    if e["orient"] == "H":
        yd = loc[1]
        a, b = (p1[0], yd), (p2[0], yd)
        meas = abs(p2[0] - p1[0])
        for p in (p1, p2):
            sg = 1 if yd >= p[1] else -1
            if abs(yd - p[1]) > exo:
                out.append(("line", (p[0], p[1] + sg * exo), (p[0], yd + sg * exe)))
        ux, uy = (1, 0) if b[0] >= a[0] else (-1, 0)
        rot = 0.0
        nrm = (0, 1)
    else:
        xd = loc[0]
        a, b = (xd, p1[1]), (xd, p2[1])
        meas = abs(p2[1] - p1[1])
        for p in (p1, p2):
            sg = 1 if xd >= p[0] else -1
            if abs(xd - p[0]) > exo:
                out.append(("line", (p[0] + sg * exo, p[1]), (xd + sg * exe, p[1])))
        ux, uy = (0, 1) if b[1] >= a[1] else (0, -1)
        rot = 90.0
        nrm = (-1, 0)
    t = e["txt"] if e["txt"] is not None else fmt(round(meas, 1))
    tw = text_w(t, th)
    span = meas
    text_in = tw + 2 * gap <= span
    arrows_in = span >= 2 * asz + (tw + 2 * gap if text_in else 0)
    if e["tpos"] is not None:
        text_in = False
    # línea de cota
    if e["tpos"] is not None:
        tp = e["tpos"]
        # prolongar línea hasta el texto
        if e["orient"] == "H":
            xs = [a[0], b[0], tp[0] - tw / 2 - gap, tp[0] + tw / 2 + gap]
            if abs(tp[1] - (a[1] + gap + th / 2)) < 1e-6 * s + 1:
                out.append(("line", (min(xs), a[1]), (max(xs), a[1])))
            else:
                out.append(("line", a, b))
        else:
            ys = [a[1], b[1], tp[1] - tw / 2 - gap, tp[1] + tw / 2 + gap]
            out.append(("line", (a[0], min(ys)), (a[0], max(ys))))
    else:
        out.append(("line", a, b))
    # flechas
    for pt, d in ((a, (ux, uy)), (b, (-ux, -uy))):
        dd = d if arrows_in else (-d[0], -d[1])
        tip = pt
        bx, by = tip[0] + dd[0] * asz, tip[1] + dd[1] * asz
        px, py = -dd[1] * asz / 6, dd[0] * asz / 6
        out.append(("tri", tip, (bx + px, by + py), (bx - px, by - py)))
        if not arrows_in:
            out.append(("line", (tip[0] + dd[0] * asz, tip[1] + dd[1] * asz),
                        (tip[0] + dd[0] * (asz + 0.8 * asz), tip[1] + dd[1] * (asz + 0.8 * asz))))
    # texto
    if e["tpos"] is not None:
        tp = e["tpos"]
    else:
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        tp = (mx + nrm[0] * (gap + th / 2), my + nrm[1] * (gap + th / 2))
        if not text_in:   # texto fuera, junto a la 2a línea de extensión
            off = asz * 1.8 + gap + tw / 2
            tp = (b[0] + ux * off + nrm[0] * (gap + th / 2), b[1] + uy * off + nrm[1] * (gap + th / 2))
    out.append(("text", tp, th, t, rot, "MC"))
    return out


def stipple(c, r, s):
    """emulación del patrón AR-CONC (puntos y pequeños triángulos)."""
    rnd = random.Random(7)
    out = []
    step = 3.2 * s
    n = int(2 * r / step) + 2
    for i in range(n):
        for j in range(n):
            x = c[0] - r + (i + rnd.random()) * step
            y = c[1] - r + (j + rnd.random()) * step
            if math.hypot(x - c[0], y - c[1]) > r - 0.6 * s:
                continue
            k = rnd.random()
            if k < 0.45:
                L = (0.5 + 0.5 * rnd.random()) * s
                a0 = rnd.random() * 2 * math.pi
                pts = [(x + L * math.cos(a0 + q * 2.1), y + L * math.sin(a0 + q * 2.1)) for q in range(3)]
                out += [("line", pts[0], pts[1]), ("line", pts[1], pts[2]), ("line", pts[2], pts[0])]
            else:
                out.append(("line", (x, y), (x + 0.12 * s, y)))
    return out


Ctx.space = "P"
for (p_, h_, s_, j_) in UL:
    w_ = text_w(s_, h_)
    x0_ = p_[0] - w_ / 2 if j_ == "C" else p_[0]
    line((x0_, p_[1]), (x0_ + w_, p_[1]), "TEXTOS", lw=0.35)

# =========================================================================
#  ESCRITOR SCR
# =========================================================================
def lisp_str(s):
    o = []
    for ch in s:
        if ch == '"':
            o.append('\\"')
        elif ch == "\\":
            o.append("\\\\")
        elif ord(ch) > 126:
            o.append("\\\\U+%04X" % ord(ch))
        else:
            o.append(ch)
    return '"' + "".join(o) + '"'


def write_scr(path):
    L = []
    w = L.append
    w("; =====================================================================")
    w("; Plano_Puente_Fase4.scr  -  Lamina E-01  Pila intermedia, puente de C.R.")
    w("; Ejecutar en un DIBUJO NUEVO (plantilla acadiso.dwt) con el comando SCRIPT.")
    w("; Model Space en milimetros a tamano real. Presentacion A3 'E-01' con")
    w("; ventanas a escala 1:50, 1:10, 1:100 y 1:25 (ZOOM nXP).")
    w("; Requiere AutoCAD para Windows (no LT anterior a 2024): usa expresiones")
    w("; AutoLISP en linea para textos y activacion de ventanas.")
    w("; Generado automaticamente; coordenadas precalculadas.")
    w("; =====================================================================")
    w("(setq PLN_SV (mapcar 'getvar '(\"OSMODE\" \"DYNMODE\" \"FILEDIA\" \"CMDDIA\" \"ORTHOMODE\" \"SNAPMODE\" \"PICKSTYLE\")))")
    sysv = [("CMDECHO", "0"), ("FILEDIA", "0"), ("CMDDIA", "0"), ("OSMODE", "0"), ("OSNAPCOORD", "1"),
            ("DYNMODE", "0"), ("ORTHOMODE", "0"), ("SNAPMODE", "0"), ("POLARMODE", "0"), ("PICKSTYLE", "0"),
            ("MEASUREMENT", "1"), ("INSUNITS", "4"), ("LUNITS", "2"), ("LUPREC", "1"), ("AUNITS", "0"),
            ("AUPREC", "3"), ("ANGBASE", "0"), ("ANGDIR", "0"), ("FILLMODE", "1"), ("LWDISPLAY", "1"),
            ("LTSCALE", fmt(LTSCALE)), ("PSLTSCALE", "1"), ("MSLTSCALE", "0"), ("CELTSCALE", "1"),
            ("HPASSOC", "1"), ("DIMASSOC", "2"), ("TILEMODE", "1"), ("LAYOUTCREATEVIEWPORT", "0"),
            ("PLINEWID", "0"), ("ELEVATION", "0"), ("THICKNESS", "0")]
    for k, v in sysv:
        w(k)
        w(v)
    w("_.UCS")
    w("_W")
    w("; ---------------- tipos de linea (acadiso.lin)")
    for lt in LTYPES:
        w(f'(if (not (tblsearch "LTYPE" "{lt}")) (command "_.-LINETYPE" "_L" "{lt}" "acadiso.lin" ""))')
    w("; ---------------- capas")
    w("_.-LAYER")
    for n, c, lt, lw in LAYERS:
        w("_M"); w(n)
        w("_C"); w(str(c)); w(n)
        w("_LW"); w(f"{lw:.2f}"); w(n)
    w("_P"); w("_N"); w("VIEWPORTS")
    w("")
    for n, c, lt, lw in LAYERS:
        if lt != "CONTINUOUS":
            w(f'(if (tblsearch "LTYPE" "{lt}") (command "_.-LAYER" "_LT" "{lt}" "{n}" ""))')
    w("; ---------------- estilo de texto")
    w('(if (not (tblsearch "STYLE" "PLANO")) (entmake (list (quote (0 . "STYLE")) (quote (100 . "AcDbSymbolTableRecord")) '
      '(quote (100 . "AcDbTextStyleTableRecord")) (quote (2 . "PLANO")) (quote (70 . 0)) (quote (40 . 0.0)) '
      '(quote (41 . 1.0)) (quote (50 . 0.0)) (quote (71 . 0)) (quote (42 . 2.5)) (quote (3 . "arial.ttf")) (quote (4 . "")))))')
    w('(defun PLN_TX (sp ly x y h r jh jv s) (entmake (list (cons 0 "TEXT") (cons 67 sp) '
      '(cons 410 (if (= sp 1) (getvar "CTAB") "Model")) (cons 8 ly) (cons 10 (list x y 0.0)) '
      '(cons 40 h) (cons 1 s) (cons 50 r) (cons 41 1.0) (cons 7 "PLANO") (cons 72 jh) (cons 11 (list x y 0.0)) (cons 73 jv))))')
    w('(defun PLN_DT (s / e) (setq e (entget (entlast))) (entmod (subst (cons 1 s) (assoc 1 e) e)) (entupd (entlast)) (princ))')
    w("; ---------------- estilos de cota (texto 2.0 mm impreso)")
    dv = [("DIMTXSTY", "PLANO"), ("DIMTXT", fmt(TXT)), ("DIMUPT", "0"), ("DIMASZ", fmt(ASZ)), ("DIMEXO", fmt(EXO)),
          ("DIMEXE", fmt(EXE)), ("DIMGAP", fmt(GAP)), ("DIMTAD", "1"), ("DIMJUST", "0"), ("DIMTIH", "0"),
          ("DIMTOH", "0"), ("DIMATFIT", "3"), ("DIMTMOVE", "0"), ("DIMTIX", "0"), ("DIMSOXD", "0"),
          ("DIMLUNIT", "2"), ("DIMDEC", "1"), ("DIMZIN", "8"), ("DIMDSEP", "."), ("DIMRND", "0"),
          ("DIMLFAC", "1"), ("DIMCEN", "0"), ("DIMADEC", "3"), ("DIMCLRD", "256"), ("DIMCLRE", "256"),
          ("DIMCLRT", "256")]
    for k, v in dv:
        w(k); w(v)
    for s_ in sorted({int(e["sc"]) for e in ENTS if e["t"] == "dim"}):
        w("DIMSCALE"); w(str(s_))
        nm = f"E-{s_}"
        w(f'(if (tblsearch "DIMSTYLE" "{nm}") (command "_.-DIMSTYLE" "_S" "{nm}" "_Y") (command "_.-DIMSTYLE" "_S" "{nm}"))')
    w("; =====================================================================")
    w("; MODEL SPACE")
    w("; =====================================================================")
    cur_layer = [None]
    cur_dim = [None]

    def setlayer(n):
        if cur_layer[0] != n:
            w("CLAYER"); w(n)
            cur_layer[0] = n

    def chprop(e):
        if e.get("lt"):
            w(f'(if (tblsearch "LTYPE" "{e["lt"]}") (command "_.CHPROP" "_L" "" "_LT" "{e["lt"]}" ""))')
        if e.get("lw") is not None:
            w("_.CHPROP"); w("_L"); w(""); w("_LW"); w(f"{e['lw']:.2f}"); w("")

    def emit(e):
        t = e["t"]
        sp = 1 if e["sp"] == "P" else 0
        if t == "text":
            jv = {"B": 0, "M": 2, "T": 3}[e["j"][0]]
            jh = {"L": 0, "C": 1, "R": 2}[e["j"][1]]
            w(f'(PLN_TX {sp} "{e["layer"]}" {fmt(e["p"][0])} {fmt(e["p"][1])} {fmt(e["h"])} '
              f'{math.radians(e["rot"]):.6f} {jh} {jv} {lisp_str(e["s"])})')
            return
        if t == "hatchcircle":
            setlayer(e["layer_b"])
            w("_.CIRCLE"); w(P(e["c"])); w(fmt(e["r"]))
            setlayer(e["layer"])
            w("_.-HATCH"); w("_P"); w(e["pattern"]); w(fmt(e["hscale"])); w("0")
            w("_S"); w("_L"); w(""); w("")
            return
        setlayer(e["layer"])
        if t == "line":
            w("_.LINE"); w(P(e["p1"])); w(P(e["p2"])); w("")
        elif t == "pline":
            pts = e["pts"]
            w("_.PLINE"); w(P(pts[0]))
            nseg = len(pts) - 1
            ws = e["widths"] or [(0.0, 0.0)] * nseg
            for i in range(nseg):
                w("_W"); w(fmt(ws[i][0])); w(fmt(ws[i][1]))
                w(P(pts[i + 1]))
            w("_C" if e["closed"] else "")
        elif t == "circle":
            w("_.CIRCLE"); w(P(e["c"])); w(fmt(e["r"]))
        elif t == "arc":
            c, r = e["c"], e["r"]
            ps = (c[0] + r * math.cos(math.radians(e["a1"])), c[1] + r * math.sin(math.radians(e["a1"])))
            pe = (c[0] + r * math.cos(math.radians(e["a2"])), c[1] + r * math.sin(math.radians(e["a2"])))
            w("_.ARC"); w("_C"); w(P(c)); w(P(ps)); w(P(pe))
        elif t == "donut":
            w("_.DONUT"); w(fmt(e["din"])); w(fmt(e["dout"])); w(P(e["c"])); w("")
        elif t == "dim":
            nm = f"E-{int(e['sc'])}"
            if cur_dim[0] != nm:
                w("_.-DIMSTYLE"); w("_R"); w(nm)
                cur_dim[0] = nm
            w("_.DIMLINEAR"); w(P(e["p1"])); w(P(e["p2"]))
            w("_H" if e["orient"] == "H" else "_V"); w(P(e["loc"]))
            if e["txt"] is not None:
                w(f"(PLN_DT {lisp_str(e['txt'])})")
            if e["tpos"] is not None:
                w("_.DIMTEDIT"); w("_L"); w(P(e["tpos"]))
        chprop(e)

    model = [e for e in ENTS if e["sp"] == "M"]
    paper = [e for e in ENTS if e["sp"] == "P"]
    for e in model:
        emit(e)
    w("_.ZOOM"); w("_E")
    w("; =====================================================================")
    w("; PRESENTACION A3  'E-01'")
    w("; =====================================================================")
    w('(if (not (member "E-01" (layoutlist))) (command "_.LAYOUT" "_N" "E-01"))')
    w('(setvar "CTAB" "E-01")')
    w("_.PSPACE")
    w("; configuracion de pagina: DWG To PDF.pc3, ISO full bleed A3, 1:1, monochrome.ctb")
    w("(vl-load-com)")
    w("(setq PLN_LAY (vla-get-ActiveLayout (vla-get-ActiveDocument (vlax-get-acad-object))))")
    w('(vl-catch-all-apply (quote vla-put-ConfigName) (list PLN_LAY "DWG To PDF.pc3"))')
    w('(vl-catch-all-apply (quote vla-put-CanonicalMediaName) (list PLN_LAY "ISO_full_bleed_A3_(420.00_x_297.00_MM)"))')
    w("(vl-catch-all-apply (quote vla-put-PaperUnits) (list PLN_LAY 1))")
    w("(vl-catch-all-apply (quote vla-put-PlotType) (list PLN_LAY 5))")
    w("(vl-catch-all-apply (quote vla-put-StandardScale) (list PLN_LAY 16))")
    w('(vl-catch-all-apply (quote vla-put-StyleSheet) (list PLN_LAY "monochrome.ctb"))')
    w("(vl-catch-all-apply (quote vla-put-PlotWithLineweights) (list PLN_LAY :vlax-true))")
    w("(vl-catch-all-apply (quote vla-put-CenterPlot) (list PLN_LAY :vlax-false))")
    w("(vl-catch-all-apply (quote vla-put-PlotOrigin) (list PLN_LAY (vlax-make-variant (vlax-safearray-fill (vlax-make-safearray vlax-vbDouble (quote (0 . 1))) (list 0.0 0.0)))))")
    w("(if (not (vl-catch-all-error-p (vl-catch-all-apply (quote vla-GetPaperSize) (list PLN_LAY (quote PLN_PW) (quote PLN_PH))))) "
      "(vl-catch-all-apply (quote vla-put-PlotRotation) (list PLN_LAY (if (> PLN_PW PLN_PH) 0 1))))")
    w("_.REGENALL")
    for e in paper:
        emit(e)
    w("; ---------------- ventanas de presentacion")
    setlayer("VIEWPORTS")
    for v in VPORTS:
        x1, y1, x2, y2 = v["rect"]
        pcx, pcy = (x1 + x2) / 2, (y1 + y2) / 2
        w(f"; ventana {v['name']}  escala 1:{int(v['s'])}")
        w("_.MVIEW"); w(P((x1, y1))); w(P((x2, y2)))
        w("_.MSPACE")
        w('(setvar "CVPORT" (cdr (assoc 69 (entget (entlast)))))')
        w("_.ZOOM"); w("_C"); w(P(v["c"])); w(fmt(1.0 / v["s"]) + "XP")
        w("_.PSPACE")
        w("_.MVIEW"); w("_L"); w("_ON"); w("_L"); w("")
    w("_.REGENALL")
    w("_.ZOOM"); w("_W"); w("0,0"); w("420,297")
    w("CLAYER"); w("0")
    w("; ---------------- guardar DWG (carpeta por defecto del dibujo: DWGPREFIX)")
    w('(setq PLN_F (strcat (getvar "DWGPREFIX") "Plano_Puente_Fase4.dwg"))')
    w('(if (findfile PLN_F) (command "_.SAVEAS" "" PLN_F "_Y") (command "_.SAVEAS" "" PLN_F))')
    w("(mapcar 'setvar '(\"OSMODE\" \"DYNMODE\" \"FILEDIA\" \"CMDDIA\" \"ORTHOMODE\" \"SNAPMODE\" \"PICKSTYLE\") PLN_SV)")
    w("CMDECHO"); w("1")
    w('(princ (strcat "\\nLamina E-01 generada y guardada en: " PLN_F))')
    w("(princ)")
    data = "\r\n".join(L) + "\r\n"
    with open(path, "w", encoding="ascii", newline="") as f:
        f.write(data)
    return L


# =========================================================================
#  ESCRITOR DXF R12
# =========================================================================
def write_dxf(path):
    o = []
    def g(c, v):
        o.append(f"{c:>3}")
        o.append(str(v))
    def gf(c, v):
        g(c, fmt(v) if isinstance(v, float) else v)
    # HEADER
    g(0, "SECTION"); g(2, "HEADER")
    g(9, "$ACADVER"); g(1, "AC1009")
    g(9, "$DWGCODEPAGE"); g(3, "ANSI_1252")
    g(9, "$INSBASE"); g(10, 0.0); g(20, 0.0); g(30, 0.0)
    g(9, "$EXTMIN"); g(10, -6000.0); g(20, -1500.0); g(30, 0.0)
    g(9, "$EXTMAX"); g(10, 47000.0); g(20, 9700.0); g(30, 0.0)
    g(9, "$LTSCALE"); g(40, LTSCALE)
    g(9, "$PSLTSCALE"); g(70, 1)
    g(9, "$TILEMODE"); g(70, 1)
    g(9, "$TEXTSTYLE"); g(7, "PLANO")
    g(9, "$CLAYER"); g(8, "0")
    g(9, "$LUNITS"); g(70, 2)
    g(9, "$LUPREC"); g(70, 1)
    g(9, "$PLIMMIN"); g(10, 0.0); g(20, 0.0)
    g(9, "$PLIMMAX"); g(10, 420.0); g(20, 297.0)
    g(9, "$PEXTMIN"); g(10, 0.0); g(20, 0.0); g(30, 0.0)
    g(9, "$PEXTMAX"); g(10, 420.0); g(20, 297.0); g(30, 0.0)
    g(9, "$HANDLING"); g(70, 0)
    g(0, "ENDSEC")
    # TABLES
    g(0, "SECTION"); g(2, "TABLES")
    g(0, "TABLE"); g(2, "VPORT"); g(70, 1)
    g(0, "VPORT"); g(2, "*ACTIVE"); g(70, 0)
    g(10, 0.0); g(20, 0.0); g(11, 1.0); g(21, 1.0); g(12, 20000.0); g(22, 4000.0)
    g(13, 0.0); g(23, 0.0); g(14, 10.0); g(24, 10.0); g(15, 10.0); g(25, 10.0)
    g(16, 0.0); g(26, 0.0); g(36, 1.0); g(17, 0.0); g(27, 0.0); g(37, 0.0)
    g(40, 14000.0); g(41, 3.4); g(42, 50.0); g(43, 0.0); g(44, 0.0); g(50, 0.0); g(51, 0.0)
    g(71, 0); g(72, 100); g(73, 1); g(74, 3); g(75, 0); g(76, 0); g(77, 0); g(78, 0)
    g(0, "ENDTAB")
    g(0, "TABLE"); g(2, "LTYPE"); g(70, len(LTYPES) + 1)
    g(0, "LTYPE"); g(2, "CONTINUOUS"); g(70, 0); g(3, "Solid line"); g(72, 65); g(73, 0); g(40, 0.0)
    for n, pat in LTYPES.items():
        g(0, "LTYPE"); g(2, n); g(70, 0); g(3, n); g(72, 65); g(73, len(pat)); g(40, sum(abs(x) for x in pat))
        for x in pat:
            g(49, x)
    g(0, "ENDTAB")
    g(0, "TABLE"); g(2, "LAYER"); g(70, len(LAYERS) + 1)
    g(0, "LAYER"); g(2, "0"); g(70, 0); g(62, 7); g(6, "CONTINUOUS")
    for n, c, lt, lw in LAYERS:
        g(0, "LAYER"); g(2, n); g(70, 0); g(62, c); g(6, lt)
    g(0, "ENDTAB")
    g(0, "TABLE"); g(2, "STYLE"); g(70, 2)
    for n, font in (("STANDARD", "txt"), ("PLANO", "arial.ttf")):
        g(0, "STYLE"); g(2, n); g(70, 0); g(40, 0.0); g(41, 1.0); g(50, 0.0); g(71, 0); g(42, 2.5)
        g(3, font); g(4, "")
    g(0, "ENDTAB")
    g(0, "TABLE"); g(2, "VIEW"); g(70, 0); g(0, "ENDTAB")
    g(0, "TABLE"); g(2, "UCS"); g(70, 0); g(0, "ENDTAB")
    g(0, "TABLE"); g(2, "APPID"); g(70, 1); g(0, "APPID"); g(2, "ACAD"); g(70, 0); g(0, "ENDTAB")
    g(0, "TABLE"); g(2, "DIMSTYLE"); g(70, 0); g(0, "ENDTAB")
    g(0, "ENDSEC")
    g(0, "SECTION"); g(2, "BLOCKS"); g(0, "ENDSEC")
    # ENTITIES
    g(0, "SECTION"); g(2, "ENTITIES")

    def head(t, layer, sp, lt=None):
        g(0, t); g(8, layer)
        if lt:
            g(6, lt)
        if sp == "P":
            g(67, 1)

    def d_line(p1, p2, layer, sp, lt=None):
        head("LINE", layer, sp, lt)
        g(10, float(p1[0])); g(20, float(p1[1])); g(30, 0.0)
        g(11, float(p2[0])); g(21, float(p2[1])); g(31, 0.0)

    def d_text(p, h, s, rot, j, layer, sp):
        jv = {"B": 0, "M": 2, "T": 3}[j[0]]
        jh = {"L": 0, "C": 1, "R": 2}[j[1]]
        head("TEXT", layer, sp)
        g(10, float(p[0])); g(20, float(p[1])); g(30, 0.0)
        g(40, float(h)); g(1, s); g(50, float(rot)); g(7, "PLANO")
        if jh or jv:
            g(72, jh); g(11, float(p[0])); g(21, float(p[1])); g(31, 0.0); g(73, jv)

    def d_poly(pts, layer, sp, closed, widths, bulges=None, lt=None):
        head("POLYLINE", layer, sp, lt)
        g(66, 1); g(10, 0.0); g(20, 0.0); g(30, 0.0); g(70, 1 if closed else 0)
        for i, p in enumerate(pts):
            g(0, "VERTEX"); g(8, layer)
            if sp == "P":
                g(67, 1)
            g(10, float(p[0])); g(20, float(p[1])); g(30, 0.0)
            if widths and i < len(widths):
                g(40, float(widths[i][0])); g(41, float(widths[i][1]))
            if bulges:
                g(42, float(bulges[i]))
        g(0, "SEQEND"); g(8, layer)

    def d_solid(a, b, c, layer, sp):
        head("SOLID", layer, sp)
        for k, p in zip((10, 11, 12, 13), (a, b, c, c)):
            g(k, float(p[0])); g(k + 10, float(p[1])); g(k + 20, 0.0)

    for e in ENTS:
        t, ly, sp = e["t"], e["layer"], e["sp"]
        lt = e.get("lt")
        if t == "line":
            d_line(e["p1"], e["p2"], ly, sp, lt)
        elif t == "pline":
            d_poly(e["pts"], ly, sp, e["closed"], e["widths"], lt=lt)
        elif t == "circle":
            head("CIRCLE", ly, sp, lt); g(10, float(e["c"][0])); g(20, float(e["c"][1])); g(30, 0.0); g(40, float(e["r"]))
        elif t == "arc":
            head("ARC", ly, sp, lt); g(10, float(e["c"][0])); g(20, float(e["c"][1])); g(30, 0.0)
            g(40, float(e["r"])); g(50, float(e["a1"])); g(51, float(e["a2"]))
        elif t == "donut":
            c, din, dout = e["c"], e["din"], e["dout"]
            rm = (din + dout) / 4
            wd = (dout - din) / 2
            d_poly([(c[0] - rm, c[1]), (c[0] + rm, c[1])], ly, sp, True, [(wd, wd), (wd, wd)], bulges=[1.0, 1.0])
        elif t == "text":
            d_text(e["p"], e["h"], e["s"], e["rot"], e["j"], ly, sp)
        elif t == "hatchcircle":
            head("CIRCLE", e["layer_b"], sp); g(10, float(e["c"][0])); g(20, float(e["c"][1])); g(30, 0.0); g(40, float(e["r"]))
            for pr in stipple(e["c"], e["r"], e["sc"]):
                d_line(pr[1], pr[2], ly, sp)
        elif t == "dim":
            for pr in dim_prims(e):
                if pr[0] == "line":
                    d_line(pr[1], pr[2], "COTAS", sp)
                elif pr[0] == "tri":
                    d_solid(pr[1], pr[2], pr[3], "COTAS", sp)
                else:
                    d_text(pr[1], pr[2], pr[3], pr[4], pr[5], "COTAS", sp)
    # VIEWPORTS (paper)
    def vport(cx, cy, wdt, hgt, vid, vcx, vcy, vh, status):
        g(0, "VIEWPORT"); g(8, "VIEWPORTS"); g(67, 1)
        g(10, float(cx)); g(20, float(cy)); g(30, 0.0); g(40, float(wdt)); g(41, float(hgt))
        g(68, status); g(69, vid)
        g(1001, "ACAD"); g(1000, "MVIEW"); g(1002, "{")
        g(1070, 16)
        g(1010, 0.0); g(1020, 0.0); g(1030, 0.0)
        g(1010, 0.0); g(1020, 0.0); g(1030, 1.0)
        g(1040, 0.0); g(1040, float(vh)); g(1040, float(vcx)); g(1040, float(vcy))
        g(1040, 50.0); g(1040, 0.0); g(1040, 0.0)
        g(1070, 0); g(1070, 100); g(1070, 1); g(1070, 3); g(1070, 0); g(1070, 0); g(1070, 0); g(1070, 0)
        g(1040, 0.0); g(1040, 0.0); g(1040, 0.0); g(1040, 10.0); g(1040, 10.0); g(1040, 10.0); g(1040, 10.0)
        g(1070, 0)
        g(1002, "{"); g(1002, "}")
        g(1002, "}")
    vport(210, 148.5, 420 * 1.1, 297 * 1.1, 1, 210, 148.5, 297 * 1.1, 1)
    for i, v in enumerate(VPORTS):
        x1, y1, x2, y2 = v["rect"]
        vport((x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1, i + 2, v["c"][0], v["c"][1], (y2 - y1) * v["s"], i + 2)
    g(0, "ENDSEC"); g(0, "EOF")
    data = "\r\n".join(o) + "\r\n"
    data = data.replace("θ", "%%U+03B8")
    data = data.replace("≠", "<>")
    with open(path, "w", encoding="cp1252", errors="replace", newline="") as f:
        f.write(data)


# =========================================================================
#  PDF (render de la lámina)
# =========================================================================
def write_pdf(path, png=None):
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["lines.scale_dashes"] = False
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, PathPatch, Circle as MCircle, Rectangle, Wedge, Arc as MArc
    from matplotlib.transforms import Affine2D
    from matplotlib.backends.backend_pdf import PdfPages

    fig = plt.figure(figsize=(420 / 25.4, 297 / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 420); ax.set_ylim(0, 297); ax.set_aspect("equal"); ax.axis("off")
    PT = 72 / 25.4
    K = "black"

    def lwof(e, layer=None):
        lw = e.get("lw") if isinstance(e, dict) else None
        if lw is None:
            lw = LAYER[layer or e["layer"]][3]
        return lw * PT

    def ltof(e):
        lt = e.get("lt") or LAYER[e["layer"]][2]
        if lt == "CONTINUOUS":
            return None
        return [abs(x) * LTSCALE * PT for x in LTYPES[lt]]

    def draw(e, T, s, clip):
        """T: función modelo->papel ; s: escala (modelo/papel)."""
        arts = []
        t = e["t"]
        if t == "line":
            (x1, y1), (x2, y2) = T(e["p1"]), T(e["p2"])
            ln, = ax.plot([x1, x2], [y1, y2], color=K, lw=lwof(e), solid_capstyle="round")
            d = ltof(e)
            if d:
                ln.set_dashes(d)
            arts.append(ln)
        elif t == "pline":
            pts = [T(p) for p in e["pts"]]
            if e["widths"] and any(wv > 0 for ww in e["widths"] for wv in ww):
                for i in range(len(pts) - 1):
                    sw, ew = e["widths"][i]
                    a, b = pts[i], pts[i + 1]
                    if sw == 0 and ew == 0:
                        ln, = ax.plot([a[0], b[0]], [a[1], b[1]], color=K, lw=lwof(e))
                        arts.append(ln)
                        continue
                    L_ = math.hypot(b[0] - a[0], b[1] - a[1])
                    nx, ny = -(b[1] - a[1]) / L_, (b[0] - a[0]) / L_
                    sw, ew = sw / s / 2, ew / s / 2
                    poly = [(a[0] + nx * sw, a[1] + ny * sw), (b[0] + nx * ew, b[1] + ny * ew),
                            (b[0] - nx * ew, b[1] - ny * ew), (a[0] - nx * sw, a[1] - ny * sw)]
                    arts.append(ax.add_patch(Polygon(poly, closed=True, fc=K, ec=K, lw=0.1 * PT)))
            else:
                if e["closed"]:
                    pts = pts + [pts[0]]
                ln, = ax.plot([p[0] for p in pts], [p[1] for p in pts], color=K, lw=lwof(e))
                d = ltof(e)
                if d:
                    ln.set_dashes(d)
                arts.append(ln)
        elif t == "circle":
            c = T(e["c"])
            pa = MCircle(c, e["r"] / s, fill=False, ec=K, lw=lwof(e))
            d = ltof(e)
            if d:
                pa.set_linestyle((0, d))
            arts.append(ax.add_patch(pa))
        elif t == "arc":
            c = T(e["c"])
            pa = MArc(c, 2 * e["r"] / s, 2 * e["r"] / s, theta1=e["a1"], theta2=e["a2"], ec=K, lw=lwof(e))
            arts.append(ax.add_patch(pa))
        elif t == "donut":
            c = T(e["c"])
            ro, ri = e["dout"] / 2 / s, e["din"] / 2 / s
            arts.append(ax.add_patch(Wedge(c, ro, 0, 360, width=ro - ri, fc=K, ec=K, lw=0.05 * PT)))
        elif t == "text":
            arts += draw_text(T(e["p"]), e["h"] / s, e["s"], e["rot"], e["j"], lwof(e))
        elif t == "hatchcircle":
            c = T(e["c"])
            arts.append(ax.add_patch(MCircle(c, e["r"] / s, fill=False, ec=K, lw=LAYER[e["layer_b"]][3] * PT)))
            segs = stipple(e["c"], e["r"], e["sc"])
            from matplotlib.collections import LineCollection
            lc = LineCollection([[T(p[1]), T(p[2])] for p in segs], colors="#555555", lw=0.13 * PT)
            arts.append(ax.add_collection(lc))
        elif t == "dim":
            for pr in dim_prims(e):
                if pr[0] == "line":
                    (x1, y1), (x2, y2) = T(pr[1]), T(pr[2])
                    ln, = ax.plot([x1, x2], [y1, y2], color=K, lw=0.18 * PT)
                    arts.append(ln)
                elif pr[0] == "tri":
                    arts.append(ax.add_patch(Polygon([T(pr[1]), T(pr[2]), T(pr[3])], closed=True, fc=K, ec=K, lw=0.1)))
                else:
                    arts += draw_text(T(pr[1]), pr[2] / s, pr[3], pr[4], pr[5], 0.18 * PT)
        if clip is not None:
            for a in arts:
                a.set_clip_path(clip)

    def draw_text(p, h, s, rot, j, lw):
        st = pretty(s)
        tp = TextPath((0, 0), st, size=h / CAP, prop=FP)
        ext = tp.get_extents()
        wdt = ext.x1 if st.strip() else 0
        x0 = {"L": 0, "C": -wdt / 2, "R": -wdt}[j[1]]
        y0 = {"B": 0, "M": -h / 2, "T": -h}[j[0]]
        tr = Affine2D().translate(x0, y0).rotate_deg(rot).translate(p[0], p[1])
        pp = PathPatch(tr.transform_path(tp), fc=K, ec="none", lw=0)
        ax.add_patch(pp)
        return [pp]

    for e in ENTS:
        if e["sp"] == "P":
            draw(e, lambda q: q, 1.0, None)
    for v in VPORTS:
        x1, y1, x2, y2 = v["rect"]
        pcx, pcy = (x1 + x2) / 2, (y1 + y2) / 2
        s = v["s"]
        mcx, mcy = v["c"]
        T = (lambda pcx, pcy, mcx, mcy, s: (lambda q: (pcx + (q[0] - mcx) / s, pcy + (q[1] - mcy) / s)))(pcx, pcy, mcx, mcy, s)
        clip = Rectangle((x1, y1), x2 - x1, y2 - y1, transform=ax.transData)
        for e in ENTS:
            if e["sp"] == "M":
                q = e.get("p1") or e.get("c") or e.get("p") or e["pts"][0]
                hw, hh = (x2 - x1) / 2 * s, (y2 - y1) / 2 * s
                if abs(q[0] - mcx) <= hw + 2000 and abs(q[1] - mcy) <= hh + 2000:
                    draw(e, T, s, clip)
    with PdfPages(path) as pdf:
        d = pdf.infodict()
        d["Title"] = "E-01 Detallado estructural de pila intermedia"
        d["Subject"] = "Lamina A3 - Puente de concreto reforzado"
        pdf.savefig(fig)
    if png:
        fig.savefig(png, dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    write_scr(os.path.join(OUT, NAME + ".scr"))
    write_dxf(os.path.join(OUT, NAME + ".dxf"))
    write_pdf(os.path.join(OUT, NAME + ".pdf"), png=os.path.join(OUT, "preview.png"))
    info = dict(R_ARO_EJE=R_ARO_EJE, D_ARO_EJE=2 * R_ARO_EJE, R_BAR=R_BAR, THETA=THETA, N_AROS=len(ARO_Y),
                Y0=Y0_ARO, ents=len(ENTS))
    print(json.dumps(info, indent=1))
