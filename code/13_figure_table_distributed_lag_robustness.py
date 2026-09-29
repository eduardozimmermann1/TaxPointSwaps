"""
Stage 13/21 — Robustness table and coefficient figure for the distributed-lag
design (Table 3 specifications, Figure 3). Defines build()/fit() helpers that
Stages 14, 20 and 21 re-use via exec() of this file's source.

Reads   : data/multipliers_raw.pkl (01); data/stable_bfs.pkl (06);
          data/cant_events.pkl (07); data/fd_spatial.pkl (08)
Writes  : paper/tables/robust_offset.tex, paper/tables/spatial.tex,
          paper/figs/fig3_dl.pdf
Feeds   : paper Table 3, Table 4, Figure 3 (Section 5.2-5.3).
"""

import pandas as pd, numpy as np, pyfixest as pf, warnings, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
warnings.filterwarnings('ignore'); plt.rcParams.update({'font.size':8,'axes.spines.top':False,'axes.spines.right':False})
mr=pd.read_pickle('data/multipliers_raw.pkl'); stable=set(pd.read_pickle('data/stable_bfs.pkl').bfs); cant=pd.read_pickle('data/cant_events.pkl')
def stars(p): return '***' if p<.01 else '**' if p<.05 else '*' if p<.1 else ''
def build(L=3,F=2,drop=(),incl_AR=False,trim=40,kind='u'):
    c=cant[['canton','year','dcu','dcs']].sort_values(['canton','year']).copy()
    c['dpos']=c.dcu.clip(lower=0); c['dneg']=c.dcu.clip(upper=0); c['dabs']=c.dcu.abs()
    for nm,col in [('u','dcu'),('p','dpos'),('n','dneg'),('a','dabs')]:
        for l in range(-F,L+1): c[f'{nm}_'+('f%d'%-l if l<0 else 'l%d'%l)]=c.groupby('canton')[col].shift(l)
    for l in range(0,3): c['s_l%d'%l]=c.groupby('canton').dcs.shift(l).fillna(0)
    ms=mr[mr.bfs.isin(stable)].sort_values(['bfs','year']).copy(); ms['dm']=ms.groupby('bfs').inc_m.diff(); ms['T']=ms.inc_m+ms.inc_c; ms['dT']=ms.groupby('bfs')['T'].diff()
    d=ms.merge(c.drop(columns=['dcu','dcs','dpos','dneg','dabs']),on=['canton','year'],how='left')
    if not incl_AR: d=d[d.canton!='AR']
    d=d[d.dm.abs()<=trim]; d=d[~d.canton.isin(drop)]
    d=d.dropna(subset=['dm']+[f'u_l{l}' for l in range(L+1)]+[f'u_f{l}' for l in range(1,F+1)])
    for nm in 'upna':
        for j in range(L): d[f'{nm}c{j}']=d[f'{nm}_l{j}']-d[f'{nm}_l{L}']
    return d
def fit(d,L,F,y='dm',nm='u'):
    rhs=[f'{nm}_f{l}' for l in range(1,F+1)]+[f'{nm}c{j}' for j in range(L)]+[f'{nm}_l{L}','s_l0','s_l1','s_l2']
    return pf.feols(f'{y} ~ '+'+'.join(rhs)+' | year',data=d,vcov={'CRV1':'canton'})
specs=[('Baseline (3 lags, 2 leads)',dict(L=3,F=2)),('2 lags',dict(L=2,F=2)),('4 lags',dict(L=4,F=2)),('No leads',dict(L=3,F=0)),('Drop SZ',dict(L=3,F=2,drop=('SZ',))),('Drop SZ, SH',dict(L=3,F=2,drop=('SZ','SH'))),
 ('Drop cantons with swaps/partial swaps',dict(L=3,F=2,drop=('LU','VD','NE','BS','AI','AG','NW','ZG','OW'))),('Include AR',dict(L=3,F=2,incl_AR=True)),('Trim $|\\Delta m|\\le 20$',dict(L=3,F=2,trim=20))]
rows=[]; res={}
for name,kw in specs:
    L=kw['L']; F=kw['F']; d=build(**kw); f=fit(d,L,F); co=f.coef(); se=f.se(); pv=f.pvalue()
    r=dict(spec=name,cum=co[f'u_l{L}'],se=se[f'u_l{L}'],p=pv[f'u_l{L}'],N=f._N,cl=d.canton.nunique())
    r['lead1']=(co['u_f1'],se['u_f1'],pv['u_f1']) if F>=1 else None; r['lead2']=(co['u_f2'],se['u_f2'],pv['u_f2']) if F>=2 else None
    rows.append(r)
    print(f"{name:45s} cum={r['cum']:+.3f} se={r['se']:.3f} p={r['p']:.3f} N={r['N']} cl={r['cl']}  lead1={None if r['lead1'] is None else round(r['lead1'][0],3)} lead2={None if r['lead2'] is None else round(r['lead2'][0],3)}")
# total burden pass-through
d=build(L=3,F=2); fT=fit(d,3,2,y='dT'); print('dT cum (1+offset):',round(fT.coef()['u_l3'],3),round(fT.se()['u_l3'],3),' swap s_l0 on dT:',round(fT.coef()['s_l0'],3))
fS=fit(d,3,2); print('swap s_l0 on dm:',round(fS.coef()['s_l0'],3),round(fS.se()['s_l0'],3),' s_l1:',round(fS.coef()['s_l1'],3),round(fS.se()['s_l1'],3),' s_l2:',round(fS.coef()['s_l2'],3),round(fS.se()['s_l2'],3))
# asymmetry (hikes p / cuts n) and |dc| (a)
d=build(L=3,F=2); rhs=[f'{nm}_f{l}' for nm in 'pn' for l in (1,2)]+[f'{nm}c{j}' for nm in 'pn' for j in range(3)]+['p_l3','n_l3','s_l0','s_l1','s_l2']
fa=pf.feols('dm ~ '+'+'.join(rhs)+' | year',data=d,vcov={'CRV1':'canton'}); print('hikes cum',round(fa.coef()['p_l3'],3),round(fa.se()['p_l3'],3),round(fa.pvalue()['p_l3'],3),' cuts cum',round(fa.coef()['n_l3'],3),round(fa.se()['n_l3'],3),round(fa.pvalue()['n_l3'],3))
rhs=[f'a_f{l}' for l in (1,2)]+[f'ac{j}' for j in range(3)]+['a_l3','s_l0','s_l1','s_l2']; fb=pf.feols('dm ~ '+'+'.join(rhs)+' | year',data=d,vcov={'CRV1':'canton'}); print('|dc| cum',round(fb.coef()['a_l3'],3),round(fb.se()['a_l3'],3),round(fb.pvalue()['a_l3'],3))
# permutation for baseline
D=build(L=3,F=2); cans=sorted(D.canton.unique()); ucols=['u_f2','u_f1','u_l0','u_l1','u_l2','u_l3']; paths={k:D[D.canton==k].groupby('year')[ucols].first() for k in cans}
sw=D[['s_l0','s_l1','s_l2']].values; y=D.dm.values; yr=D.year.values
def est(perm=None):
    U=np.zeros((len(D),6))
    for k in cans:
        m=(D.canton==k).values; U[m]=paths[perm[k] if perm else k].reindex(D.year[m]).values
    X=np.column_stack([U[:,0],U[:,1],U[:,2]-U[:,5],U[:,3]-U[:,5],U[:,4]-U[:,5],U[:,5],sw]); ok=~np.isnan(X).any(1)
    yy=pd.Series(y[ok]); XX=pd.DataFrame(X[ok]); g=yr[ok]; yd=yy.values-yy.groupby(g).transform('mean').values; Xd=XX.values-XX.groupby(g).transform('mean').values
    return np.linalg.lstsq(Xd,yd,rcond=None)[0]
b0=est(); rng=np.random.default_rng(11); dist=np.array([est(dict(zip(cans,rng.permutation(cans))))[[5,1,0]] for _ in range(1000)])
pc=(np.abs(dist[:,0])>=abs(b0[5])).mean(); pl1=(np.abs(dist[:,1])>=abs(b0[1])).mean(); pl2=(np.abs(dist[:,2])>=abs(b0[0])).mean()
print('PERM cum',round(b0[5],3),'p',pc,'sd',dist[:,0].std().round(3),'| lead1 p',pl1,'| lead2 p',pl2, '| perm 95% range cum',np.percentile(dist[:,0],[2.5,97.5]).round(3))
# ---- LaTeX robustness table
T=["\\begin{tabular}{lcccccc}","\\toprule","Specification & Cum. offset (0--3) & S.E. & $p$ (cluster) & Lead $t{+}2$ & $N$ & Cantons \\\\","\\midrule"]
for r in rows:
    l2='' if r['lead2'] is None else f"{r['lead2'][0]:.3f}{stars(r['lead2'][2])}"
    T.append(f"{r['spec']} & {r['cum']:.3f} & ({r['se']:.3f}) & {r['p']:.2f} & {l2} & {r['N']:,} & {r['cl']} \\\\")
T+=["\\bottomrule","\\end{tabular}"]; open('paper/tables/robust_offset.tex','w').write("\n".join(T))
# ---- coefficient figure
d=build(L=3,F=2); f=pf.feols('dm ~ u_f2+u_f1+u_l0+u_l1+u_l2+u_l3+s_l0+s_l1+s_l2 | year',data=d,vcov={'CRV1':'canton'}); co=f.coef(); se=f.se()
fig,axs=plt.subplots(1,2,figsize=(6.8,2.7),gridspec_kw={'width_ratios':[1.6,1]})
nm=['u_f2','u_f1','u_l0','u_l1','u_l2','u_l3']; xs=[-2,-1,0,1,2,3]
axs[0].errorbar(xs,[co[n] for n in nm],yerr=[1.96*se[n] for n in nm],fmt='o',c='#2c3e50',capsize=2,ms=4); axs[0].axhline(0,c='k',lw=.5); axs[0].axhline(-1,c='grey',ls='--',lw=.7); axs[0].text(-2.1,-0.93,'full offset',fontsize=7,color='grey')
axs[0].set_xlabel('Years since cantonal change ($k$)'); axs[0].set_ylabel('Effect on $\\Delta m$ per point of $\\Delta c$'); axs[0].set_title('(a) Unilateral cantonal changes',fontsize=8); axs[0].set_ylim(-1.15,0.4)
ns=['s_l0','s_l1','s_l2']; axs[1].errorbar([0,1,2],[co[n] for n in ns],yerr=[1.96*se[n] for n in ns],fmt='o',c='#c0392b',capsize=2,ms=4); axs[1].axhline(0,c='k',lw=.5); axs[1].axhline(-1,c='grey',ls='--',lw=.7)
axs[1].set_xlabel('Years since swap ($k$)'); axs[1].set_title('(b) Mandated swaps',fontsize=8); axs[1].set_ylim(-1.15,0.4); axs[1].set_xticks([0,1,2])
fig.tight_layout(); fig.savefig('paper/figs/fig3_dl.pdf'); plt.close()
print('coef table:',{n:(round(co[n],3),round(se[n],3)) for n in nm+ns})
# ---- spatial table
DD=pd.read_pickle('data/fd_spatial.pkl'); DD['nu_c0']=DD.nb_u_l0-DD.nb_u_l2; DD['nu_c1']=DD.nb_u_l1-DD.nb_u_l2; DD['ns_c0']=DD.nb_s_l0-DD.nb_s_l2; DD['ns_c1']=DD.nb_s_l1-DD.nb_s_l2
def sp(data,fe): return pf.feols('dm ~ nb_u_f1+nu_c0+nu_c1+nb_u_l2+nb_s_f1+ns_c0+ns_c1+nb_s_l2 | '+fe,data=data,vcov={'CRV1':'canton'})
S1=sp(DD,'cy'); S3=sp(DD[DD.border==1],'cy'); S4=sp(DD,'cy + bfs')
lab=[('nb_u_f1','Neighbour cantonal change, lead $t{+}1$'),('nb_u_l2','Neighbour cantonal change, cum. $t$ to $t{-}2$'),('nb_s_f1','Neighbour mandated swap ($-\\Delta c$), lead $t{+}1$'),('nb_s_l2','Neighbour mandated swap, cum. $t$ to $t{-}2$')]
T=["\\begin{tabular}{lccc}","\\toprule"," & (1) All & (2) Border only & (3) + Muni FE \\\\","\\midrule"]
for k,l in lab:
    T.append(l+' & '+' & '.join(f"{m.coef()[k]:.3f}{stars(m.pvalue()[k])}" for m in (S1,S3,S4))+' \\\\'); T.append(' & '+' & '.join(f"({m.se()[k]:.3f})" for m in (S1,S3,S4))+' \\\\')
T+=["\\midrule","Canton$\\times$year FE & Yes & Yes & Yes \\\\","Municipality FE & No & No & Yes \\\\","Observations & "+' & '.join(f"{m._N:,}" for m in (S1,S3,S4))+" \\\\","\\bottomrule","\\end{tabular}"]; open('paper/tables/spatial.tex','w').write("\n".join(T))
print('SPATIAL',{k:[(round(m.coef()[k],3),round(m.se()[k],3)) for m in (S1,S3,S4)] for k,_ in lab})
