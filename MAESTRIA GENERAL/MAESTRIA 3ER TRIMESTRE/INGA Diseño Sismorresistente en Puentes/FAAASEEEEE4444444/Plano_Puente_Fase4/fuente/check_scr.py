"""Validador estructural del .SCR: recorre cada comando con la secuencia de
indicaciones (prompts) esperada de AutoCAD y verifica tipos de dato."""
import re, sys, collections

PT = re.compile(r"^-?\d+(\.\d+)?,-?\d+(\.\d+)?$")
NUM = re.compile(r"^-?\d+(\.\d+)?$")
lines = open(sys.argv[1], encoding="ascii", newline="").read().split("\r\n")
assert lines[-1] == ""
lines = lines[:-1]
i = 0
stats = collections.Counter()
errors = []
lisp_n = 0


def nxt():
    global i
    t = lines[i]
    i += 1
    return t


def need(kind, t, ctx):
    ok = {"pt": PT.match(t), "num": NUM.match(t), "blank": t == "", "word": re.match(r"^[A-Za-z0-9_.\-]+$", t)}[kind]
    if not ok:
        errors.append(f"linea {i}: se esperaba {kind} en {ctx}, se obtuvo {t!r}")


def lisp_balanced(t):
    d, ins, esc = 0, False, False
    for ch in t:
        if ins:
            if esc: esc = False
            elif ch == "\\": esc = True
            elif ch == '"': ins = False
        else:
            if ch == '"': ins = True
            elif ch == "(": d += 1
            elif ch == ")": d -= 1
            if d < 0: return False
    return d == 0 and not ins


SYSVARS = set()
while i < len(lines):
    t = nxt()
    if t.startswith(";"):
        continue
    if t == "":
        errors.append(f"linea {i}: linea en blanco en el nivel de comando (repetiria el ultimo comando)")
        continue
    if t.startswith("("):
        lisp_n += 1
        if not lisp_balanced(t):
            errors.append(f"linea {i}: expresion LISP desbalanceada")
        if "PLN_TX" in t and not t.startswith("(defun"):
            stats["TEXT"] += 1
        continue
    if t != t.strip() or " " in t:
        errors.append(f"linea {i}: espacio dentro de un token de comando {t!r}")
    c = t.upper()
    stats[c] += 1
    if c == "_.UCS":
        need("word", nxt(), c)
    elif c == "_.-LAYER":
        while True:
            o = nxt()
            if o == "": break
            if o in ("_M",): need("word", nxt(), c)
            elif o in ("_C", "_LW", "_P", "_LT"): nxt(); need("word", nxt(), c)
            else: errors.append(f"linea {i}: opcion -LAYER desconocida {o}")
    elif c == "CLAYER":
        need("word", nxt(), c)
    elif c == "_.LINE":
        n = 0
        while True:
            o = nxt()
            if o == "": break
            need("pt", o, c); n += 1
        if n < 2: errors.append(f"linea {i}: LINE con {n} puntos")
    elif c == "_.PLINE":
        need("pt", nxt(), c)
        while True:
            o = nxt()
            if o in ("", "_C"): break
            if o == "_W":
                need("num", nxt(), c); need("num", nxt(), c)
                need("pt", nxt(), c)
            else:
                errors.append(f"linea {i}: PLINE token inesperado {o!r}")
    elif c == "_.CIRCLE":
        need("pt", nxt(), c); need("num", nxt(), c)
    elif c == "_.ARC":
        need("word", nxt(), c); need("pt", nxt(), c); need("pt", nxt(), c); need("pt", nxt(), c)
    elif c == "_.DONUT":
        need("num", nxt(), c); need("num", nxt(), c)
        while True:
            o = nxt()
            if o == "": break
            need("pt", o, c)
    elif c == "_.-HATCH":
        assert nxt() == "_P"; need("word", nxt(), c); need("num", nxt(), c); need("num", nxt(), c)
        assert nxt() == "_S"; assert nxt() == "_L"; need("blank", nxt(), c); need("blank", nxt(), c)
    elif c == "_.CHPROP":
        assert nxt() == "_L"; need("blank", nxt(), c)
        while True:
            o = nxt()
            if o == "": break
            if o in ("_LW", "_LT"): need("word", nxt(), c)
            else: errors.append(f"linea {i}: CHPROP opcion {o}")
    elif c == "_.-DIMSTYLE":
        assert nxt() == "_R"; need("word", nxt(), c)
    elif c == "_.DIMLINEAR":
        need("pt", nxt(), c); need("pt", nxt(), c)
        o = nxt()
        if o not in ("_H", "_V"): errors.append(f"linea {i}: DIMLINEAR orient {o}")
        need("pt", nxt(), c)
    elif c == "_.DIMTEDIT":
        assert nxt() == "_L"; need("pt", nxt(), c)
    elif c == "_.ZOOM":
        o = nxt()
        if o == "_E": pass
        elif o == "_C": need("pt", nxt(), c); m = nxt(); assert re.match(r"^\d+(\.\d+)?XP$", m), m
        elif o == "_W": need("pt", nxt(), c); need("pt", nxt(), c)
        else: errors.append(f"ZOOM {o}")
    elif c in ("_.PSPACE", "_.MSPACE", "_.REGENALL"):
        pass
    elif c == "_.MVIEW":
        o = nxt()
        if o == "_L":
            assert nxt() == "_ON"; assert nxt() == "_L"; need("blank", nxt(), c)
        else:
            need("pt", o, c); need("pt", nxt(), c)
    elif re.match(r"^[A-Z]+$", c):     # variable de sistema
        SYSVARS.add(c)
        v = nxt()
        if v == "": errors.append(f"linea {i}: valor vacio para {c}")
    else:
        errors.append(f"linea {i}: comando no reconocido {t!r}")

print("Lineas:", len(lines), " expresiones LISP:", lisp_n)
for k, v in sorted(stats.items()):
    print(f"  {k:14s} {v}")
print("Variables fijadas:", len(SYSVARS))
print("ERRORES:", len(errors))
for e in errors[:30]:
    print("  ", e)
