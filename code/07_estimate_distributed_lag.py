"""
Stage 07/21 — Distributed-lag first-differences design: municipal response
to unilateral vs. mandated cantonal multiplier changes.

Reads   : data/multipliers_raw.pkl (01), data/cant_events.pkl (06)
Writes  : data/fd_panel.pkl, data/cant_events.pkl (updated with lags)
Feeds   : paper Table 3, Figure 3(a), and the cumulative-offset numbers in
          Section 5.2.
"""

import pandas as pd, numpy as np, pyfixest as pf, warnings
warnings.filterwarnings('ignore')
mr=pd.read_pickle('data/multipliers_raw.pkl'); stable=pd.read_pickle('data/stable_bfs.pkl').bfs.tolist()
cant=mr.groupby(['canton','year']).inc_c.mean().reset_index().sort_values(['canton','year'])
cant['dc']=cant.groupby('canton').inc_c.diff()
SW={('LU',2020),('VD',2011),('VD',2012),('NE',2014),('BS',2017),('AI',2011)}
cant['swap']=[ (k,y) in SW for k,y in zip(cant.canton,cant.year)]
cant['dcs']=np.where(cant.swap,cant.dc,0.0); cant['dcu']=np.where(cant.swap,0.0,cant.dc)
def lags(df,col,pref,L=(-2,-1,0,1,2,3)):
    for l in L:
        nm=f'{pref}_'+('f%d'%-l if l<0 else 'l%d'%l)
        df[nm]=df.groupby('canton')[col].shift(l)
lags(cant,'dcu','u'); lags(cant,'dcs','s')
cant['dcu_pos']=cant.dcu.clip(lower=0); cant['dcu_neg']=cant.dcu.clip(upper=0)
lags(cant,'dcu_pos','up',L=(0,1,2,3)); lags(cant,'dcu_neg','un',L=(0,1,2,3))
ms=mr[mr.bfs.isin(stable)].sort_values(['bfs','year']).copy()
ms['dm']=ms.groupby('bfs').inc_m.diff(); ms['dT']=ms.groupby('bfs').apply(lambda g:(g.inc_m+g.inc_c).diff()).reset_index(level=0,drop=True)
d=ms.merge(cant.drop(columns=['inc_c','dc']),on=['canton','year'],how='left')
print('dm dist',d.dm.describe(percentiles=[.01,.05,.5,.95,.99]).round(2).to_dict())
print('share dm==0',(d.dm==0).mean().round(3),' by canton |dm|>40:',d[d.dm.abs()>40].groupby(['canton','year']).size().to_dict())
d=d[d.canton!='AR']; d=d[d.dm.abs()<=40]
# cumulative parametrisation: coefficient on u_l3 = sum of beta0..beta3
d['u_c0']=d.u_l0-d.u_l3; d['u_c1']=d.u_l1-d.u_l3; d['u_c2']=d.u_l2-d.u_l3
d['s_c0']=d.s_l0-d.s_l3; d['s_c1']=d.s_l1-d.s_l3; d['s_c2']=d.s_l2-d.s_l3
D=d.dropna(subset=['dm','u_f2','u_f1','u_l0','u_l1','u_l2','u_l3','s_l0','s_l3']).copy()
print('N obs',len(D),'munis',D.bfs.nunique(),'cantons',D.canton.nunique(),'years',D.year.min(),D.year.max())
def show(fit,keep=None):
    t=fit.tidy()[['Estimate','Std. Error','Pr(>|t|)']].round(3)
    print(t.loc[[i for i in t.index if (keep is None or i in keep)]].to_string())
print('\n=== A. Distributed-lag FD: dm on unilateral (u) and swap (s) canton changes; year FE; SE cluster canton')
f1=pf.feols('dm ~ u_f2+u_f1+u_l0+u_l1+u_l2+u_l3+s_l0+s_l1+s_l2 | year',data=D,vcov={'CRV1':'canton'}); show(f1)
print('\n--- cumulative (0..3) offset for unilateral, via reparam')
f2=pf.feols('dm ~ u_f2+u_f1+u_c0+u_c1+u_c2+u_l3+s_l0+s_l1+s_l2 | year',data=D,vcov={'CRV1':'canton'}); show(f2,['u_f2','u_f1','u_l3'])
try:
    wb=f2.wildboottest(param='u_l3',reps=999,cluster='canton',seed=7); print('wild bootstrap p (cum offset):',wb.round(4).to_dict() if hasattr(wb,'round') else wb)
except Exception as e: print('wild fail',e)
print('\n=== B. Asymmetry: hikes (up) vs cuts (un), lags 0-3')
f3=pf.feols('dm ~ up_l0+up_l1+up_l2+up_l3+un_l0+un_l1+un_l2+un_l3+s_l0 | year',data=D,vcov={'CRV1':'canton'}); show(f3)
print('\n=== C. Total burden pass-through: dT on unilateral lags (1+offset)')
f4=pf.feols('dT ~ u_l0+u_l1+u_l2+u_l3+s_l0 | year',data=D,vcov={'CRV1':'canton'}); show(f4)
print('\n=== D. Robustness: canton-specific? drop cantons SZ,SH; and add AR')
f5=pf.feols('dm ~ u_f2+u_f1+u_c0+u_c1+u_c2+u_l3+s_l0 | year',data=D[~D.canton.isin(['SZ','SH'])],vcov={'CRV1':'canton'}); show(f5,['u_f2','u_f1','u_c0','u_l3'])
D.to_pickle('data/fd_panel.pkl'); cant.to_pickle('data/cant_events.pkl')
