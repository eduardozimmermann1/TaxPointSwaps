"""
Stage 20/21 — Effective-burden robustness check of the main distributed-lag
result (Table 6, Table 7 first two rows).

Re-uses  : build()/fit() from Stage 13 (via exec of its source).
Reads    : data/estv_geo_panel.pkl (19); data/multipliers_raw.pkl (01);
           data/stable_bfs.pkl (06); data/cant_events.pkl (07)
Writes   : paper/tables/burden_dl.tex, paper/tables/burden_es.tex
Feeds    : paper Table 6, Table 7, Section 5.5.
"""

exec(open('code/13_figure_table_distributed_lag_robustness.py').read().split('specs=')[0])
import numpy as np
G=pd.read_pickle('data/estv_geo_panel.pkl'); G['bc']=G.cant/1000; G['bm']=G.comm/1000; G['bp']=G.pers/1000
kmap=mr[['bfs','canton']].drop_duplicates('bfs'); G=G.drop(columns=['kt']).merge(mr[['bfs','year','canton']].drop_duplicates(['bfs','year']),on=['bfs','year'])
u=G.groupby(['canton','year']).cant.nunique(); print('canton-years with non-uniform cantonal tax at 100k:',u[u>1].reset_index().groupby('canton').size().to_dict())
cb=G.groupby(['canton','year']).bc.median().reset_index().sort_values(['canton','year']); cb['dbc']=cb.groupby('canton').bc.diff()
SW={('LU',2020),('VD',2011),('VD',2012),('NE',2014),('BS',2017),('AI',2011)}; cb['swap']=[(k,y) in SW for k,y in zip(cb.canton,cb.year)]
cb['dcs']=np.where(cb.swap,cb.dbc,0.0); cb['dcu']=np.where(cb.swap,0.0,cb.dbc)
for l in range(-2,4): cb['eu_'+('f%d'%-l if l<0 else 'l%d'%l)]=cb.groupby('canton').dcu.shift(l)
for l in range(0,3): cb['es_l%d'%l]=cb.groupby('canton').dcs.shift(l).fillna(0)
cb['eu_c0']=cb.eu_l0-cb.eu_l3; cb['eu_c1']=cb.eu_l1-cb.eu_l3; cb['eu_c2']=cb.eu_l2-cb.eu_l3
Gs=G.sort_values(['bfs','year']).copy(); Gs['dbm']=Gs.groupby('bfs').bm.diff(); Gs['bt']=Gs.bc+Gs.bm; Gs['dbt']=Gs.groupby('bfs').bt.diff()
D=build(L=3,F=2); D=D.merge(Gs[['bfs','year','dbm','dbt','bm','bc']],on=['bfs','year'],how='left').merge(cb[['canton','year']+[c for c in cb.columns if c.startswith(('eu_','es_'))]],on=['canton','year'],how='left')
D=D.dropna(subset=['dbm','eu_f2','eu_f1','eu_l0','eu_l1','eu_l2','eu_l3'])
print('N',len(D),'munis',D.bfs.nunique(),'cantons',D.canton.nunique())
def fitb(d,y='dbm'):
    return pf.feols(f'{y} ~ eu_f2+eu_f1+eu_c0+eu_c1+eu_c2+eu_l3+es_l0+es_l1+es_l2 | year',data=d,vcov={'CRV1':'canton'})
res=[]
for name,d in [('All stable municipalities',D),('Excl. VS, GE (special rules)',D[~D.canton.isin(['VS','GE'])]),('Excl. VS, GE, VD',D[~D.canton.isin(['VS','GE','VD'])]),('Drop SZ, SH',D[~D.canton.isin(['SZ','SH'])])]:
    f=fitb(d); c=f.coef(); s=f.se(); p=f.pvalue(); res.append((name,c['eu_l3'],s['eu_l3'],p['eu_l3'],c['eu_f2'],p['eu_f2'],c['es_l0'],s['es_l0'],f._N))
    print(f"{name:32s} cum offset {c['eu_l3']:+.3f} ({s['eu_l3']:.3f}) p={p['eu_l3']:.2f} | lead t+2 {c['eu_f2']:+.3f} (p={p['eu_f2']:.3f}) | swap same-year {c['es_l0']:+.3f} ({s['es_l0']:.3f}) | N={f._N}")
fT=fitb(D,'dbt'); print('combined burden pass-through (1+offset):',round(fT.coef()['eu_l3'],3),round(fT.se()['eu_l3'],3),' swap same-year on combined:',round(fT.coef()['es_l0'],3),round(fT.se()['es_l0'],3))
# compare: multiplier-based baseline
fb=fit(build(L=3,F=2),3,2); print('multiplier baseline cum offset',round(fb.coef()['u_l3'],3),round(fb.se()['u_l3'],3))
# LaTeX table
T=["\\begin{tabular}{lcccc}","\\toprule","Sample & Cum. offset (0--3) & S.E. & $p$ & Swap, same year \\\\","\\midrule"]
for n,b,s,p,lf,lp,sw,ss,N in res: T.append(f"{n} & {b:.3f} & ({s:.3f}) & {p:.2f} & {sw:.3f} ({ss:.3f}) \\\\")
T+=["\\bottomrule","\\end{tabular}"]; open('paper/tables/burden_dl.tex','w').write("\n".join(T))
# ---- event studies of swaps with effective burdens (pp of gross income)
Mw={v:Gs.pivot(index='bfs',columns='year',values=v) for v in ['bc','bm','bt']}; ktm=Gs.drop_duplicates('bfs').set_index('bfs').canton
st_=set(stable); cc=cant[['canton','year','dc']]
print('\nSWAP EVENT STUDIES on effective burden at CHF 100k (pp of gross income), gap vs clean controls')
ES=[]
for k,t0,tmax in [('LU',2020,2021),('NE',2014,2019),('VD',2011,2015)]:
    yrs=[y for y in range(t0-4,min(t0+5,tmax)+1) if 2010<=y<=2025]; win=cc[(cc.year>=t0-4)&(cc.year<=t0+5)]; bad=set(win[win.dc.abs()>=1].canton)|{k,'AR'}; ctrl=[c for c in cc.canton.unique() if c not in bad]
    for v,lab in [('bc','Cantonal'),('bm','Communal'),('bt','Cantonal+communal')]:
        W=Mw[v]; W=W[W.index.isin(st_)]; d=W[yrs].sub(W[t0-1],axis=0); dk=d.groupby(ktm.reindex(d.index)).mean(); g=dk.loc[k]-dk.loc[ctrl].mean()
        ES.append((f'{k} {t0}',lab,{y-t0:round(float(g[y]),3) for y in yrs}))
        print(f'{k} {t0} {lab:18s}',{y-t0:round(float(g[y]),3) for y in yrs})
rows=[]
for ev,lab,gp in ES:
    cells=' & '.join(('%.2f'%gp[h]) if h in gp else '---' for h in range(0,6)); rows.append(f"{ev} & {lab} & {cells} \\\\")
T=["\\begin{tabular}{llrrrrrr}","\\toprule","Event & Burden component & $h=0$ & $h=1$ & $h=2$ & $h=3$ & $h=4$ & $h=5$ \\\\","\\midrule"]+rows+["\\bottomrule","\\end{tabular}"]; open('paper/tables/burden_es.tex','w').write("\n".join(T))
