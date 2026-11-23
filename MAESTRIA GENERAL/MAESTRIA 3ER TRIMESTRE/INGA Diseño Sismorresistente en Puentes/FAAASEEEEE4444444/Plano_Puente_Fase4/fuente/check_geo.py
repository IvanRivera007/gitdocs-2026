import math, re, sys, itertools
sys.argv=['x','/tmp/o']; exec(open('plano.py',encoding='utf-8').read().split('if __name__')[0])
ok=lambda c,m: print(("OK   " if c else "FALLA"), m)
# barras en sección
bars=[e for e in ENTS if e['t']=='donut' and e['dout']==DB]
ok(len(bars)==26, f"26 barras No.14 en la sección (encontradas {len(bars)})")
angs=sorted((math.degrees(math.atan2(b['c'][1]-CY,b['c'][0]-CX))%360) for b in bars)
d=[(angs[(i+1)%26]-angs[i])%360 for i in range(26)]
ok(max(abs(x-360/26) for x in d)<1e-9, f"separación angular uniforme = {360/26:.4f}° (dif. máx {max(abs(x-360/26) for x in d):.1e})")
rs=[math.hypot(b['c'][0]-CX,b['c'][1]-CY) for b in bars]
ok(all(abs(r-502.3)<1e-6 for r in rs), "todas las barras en R = 502.3 mm")
dmin=min(math.dist(a['c'],b['c']) for a,b in itertools.combinations(bars,2))
ok(dmin-DB>0, f"sin superposición: c-c mín {dmin:.1f} mm, libre {dmin-DB:.1f} mm")
ok(max(rs)+DB/2 <= R_ARO_INT+1e-9, f"barras dentro del aro (borde ext. barra {max(rs)+DB/2:.1f} <= cara int. aro {R_ARO_INT:.1f})")
ok(abs(R_COL-R_ARO_EXT-50.8)<1e-9, "recubrimiento libre al aro = 50.8 mm")
ok(abs(2*R_ARO_EJE-1073.0)<1e-6, f"Ø aro eje a eje = {2*R_ARO_EJE:.4f} mm (dato 1072.9976 ≈)")
hoop=[e for e in ENTS if e['t']=='donut' and e['din']>0][0]
ok(abs(hoop['dout']/2-R_ARO_EXT)<1e-9 and abs(hoop['din']/2-R_ARO_INT)<1e-9, "aro dibujado con espesor real 25.4 mm")
# aros detalle
ys=sorted(e['pts'][0][1] for e in ENTS if e['t']=='pline' and e['widths'] and e['widths'][0]==(DH,DH) and abs(e['pts'][0][0]-(30000-R_ARO_EJE))<1)
sp=set(round(b-a,6) for a,b in zip(ys,ys[1:]))
ok(sp=={127.0}, f"detalle 1:100: {len(ys)} aros, separación única {sp} mm, extremos {ys[0]} / {7000-ys[-1]}")
for lo,hi,n in ((0,1800,'inferior'),(1800,5200,'central'),(5200,7000,'superior')):
    print(f"      zona {n}: {sum(lo<=y<hi for y in ys)} aros")
# cotas
def dims(sc_): return [e for e in ENTS if e['t']=='dim' and e['sc']==sc_]
meas=lambda e: abs(e['p2'][0]-e['p1'][0]) if e['orient']=='H' else abs(e['p2'][1]-e['p1'][1])
print("      cotas 1:50 :", [round(meas(e),1) for e in dims(50)])
print("      cotas 1:100:", [round(meas(e),1) for e in dims(100)])
print("      cotas 1:25 :", [(round(meas(e),1),e['txt']) for e in dims(25)])
print("      cotas 1:10 :", [(round(meas(e),1),e['txt']) for e in dims(10)])
m50=sorted(round(meas(e)) for e in dims(50)); ok(m50==sorted([1800,6000,1800,9600,7000,1500,8500,1800,3400,1800,1200]),"cotas de elevación = datos")
ok(sorted(round(meas(e)) for e in dims(100))==[851,851,1800,1800,3400,7000],"cotas detalle: 1800/3400/1800, 7000 y Lp 851 (x2)")
# viewports
for v in VPORTS:
    x1,y1,x2,y2=v['rect']; print(f"      ventana {v['name']:10s} 1:{int(v['s']):<4d} papel {x2-x1:.0f}x{y2-y1:.0f} mm -> modelo {(x2-x1)*v['s']:.0f}x{(y2-y1)*v['s']:.0f} mm, ZOOM {1/v['s']:g}XP")
# todo el contenido modelo de cada vista dentro de su ventana
def bbox(e):
    P=[]
    for k in ('p1','p2','c','p','loc','tpos'):
        if e.get(k): P.append(e[k])
    if e['t']=='pline': P+=e['pts']
    r=e.get('r',0) or (e.get('dout',0)/2)
    return [(p[0]-r,p[1]-r) for p in P]+[(p[0]+r,p[1]+r) for p in P]
for v in VPORTS:
    x1,y1,x2,y2=v['rect']; s=v['s']; cx,cy=v['c']
    X1,X2=cx-(x2-x1)/2*s, cx+(x2-x1)/2*s; Y1,Y2=cy-(y2-y1)/2*s, cy+(y2-y1)/2*s
    inside=[e for e in ENTS if e['sp']=='M' and e['sc']==s]
    out=[e['t'] for e in inside for p in bbox(e) if not (X1<=p[0]<=X2 and Y1<=p[1]<=Y2) and e['t']!='dim']
    ok(not out, f"{v['name']}: geometría dentro de la ventana ({len(inside)} entidades)")
    others=[e for e in ENTS if e['sp']=='M' and e['sc']!=s and any(X1<=p[0]<=X2 and Y1<=p[1]<=Y2 for p in bbox(e))]
    ok(not others, f"{v['name']}: no aparece geometría de otras vistas")
for v in VPORTS:
    x1,y1,x2,y2=v['rect']; s=v['s']; cx,cy=v['c']
    X1,X2=cx-(x2-x1)/2*s, cx+(x2-x1)/2*s; Y1,Y2=cy-(y2-y1)/2*s, cy+(y2-y1)/2*s
    for e in ENTS:
        if e['sp']!='M': continue
        b=bbox(e)
        if e['sc']==s and e['t']!='dim' and any(not (X1<=p[0]<=X2 and Y1<=p[1]<=Y2) for p in b): print(v['name'],'OUT',e['t'],e.get('s'),b[:2], (X1,X2,Y1,Y2))
        if e['sc']!=s and any(X1<=p[0]<=X2 and Y1<=p[1]<=Y2 for p in b): print(v['name'],'FOREIGN',e['t'],e['sc'],b[:2])
