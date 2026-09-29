"""
Stage 09/21 — Permutation inference and leave-one-canton-out checks for the
distributed-lag design; also builds the FFA-by-canton panel used later.

Reads   : data/fd_panel.pkl, data/cant_events.pkl (07);
          data/multipliers_raw.pkl (01); data/ffa_gdn5000.pkl (02)
Writes  : data/ffa_with_canton.pkl
Feeds   : the permutation p-values reported in Section 5.2, and (via
          ffa_with_canton.pkl) Stage 10's Luzern financial outcomes.
"""

import pandas as pd, numpy as np, pyfixest as pf, warnings
warnings.filterwarnings('ignore')
D=pd.read_pickle('data/fd_panel.pkl'); cant=pd.read_pickle('data/cant_events.pkl')
# ---------- A1: asymmetry with leads
c=cant.copy()
for nm,col in [('up','dcu_pos'),('un','dcu_neg')]:
    for l in (-2,-1,0,1,2,3):
        c[f'{nm}_'+('f%d'%-l if l<0 else 'l%d'%l)]=c.groupby('canton')[col].shift(l)
D=D.drop(columns=[x for x in D.columns if x.startswith(('up_','un_'))]).merge(c[['canton','year']+[x for x in c.columns if x.startswith(('up_','un_'))]],on=['canton','year'],how='left')
D=D.dropna(subset=['up_f2','up_l3','un_f2','un_l3'])
print('N',len(D))
def show(fit,keep=None):
    t=fit.tidy()[['Estimate','Std. Error','Pr(>|t|)']].round(3)
    print(t.loc[[i for i in t.index if (keep is None or i in keep)]].to_string())
print('=== A1. hikes vs cuts with leads')
f=pf.feols('dm ~ up_f2+up_f1+up_l0+up_l1+up_l2+up_l3+un_f2+un_f1+un_l0+un_l1+un_l2+un_l3+s_l0 | year',data=D,vcov={'CRV1':'canton'}); show(f)
# cumulative sums by reparam
for nm in ['up','un']:
    D[f'{nm}_c0']=D[f'{nm}_l0']-D[f'{nm}_l3']; D[f'{nm}_c1']=D[f'{nm}_l1']-D[f'{nm}_l3']; D[f'{nm}_c2']=D[f'{nm}_l2']-D[f'{nm}_l3']
f2=pf.feols('dm ~ up_f2+up_f1+up_c0+up_c1+up_c2+up_l3+un_f2+un_f1+un_c0+un_c1+un_c2+un_l3+s_l0 | year',data=D,vcov={'CRV1':'canton'}); show(f2,['up_l3','un_l3'])
# ---------- A2: permutation inference on cumulative unilateral offset (permute canton paths)
Dp=pd.read_pickle('data/fd_panel.pkl').dropna(subset=['dm','u_f2','u_f1','u_l0','u_l1','u_l2','u_l3','s_l0']).copy()
cans=sorted(Dp.canton.unique()); ucols=['u_f2','u_f1','u_l0','u_l1','u_l2','u_l3']
paths={k:Dp[Dp.canton==k].groupby('year')[ucols].first() for k in cans}
yrs=sorted(Dp.year.unique())
Dp['s_l1']=Dp['s_l1'].fillna(0); Dp['s_l2']=Dp['s_l2'].fillna(0)
def est(perm=None):
    U=np.zeros((len(Dp),6))
    for k in cans:
        src=paths[perm[k] if perm is not None else k]; m=(Dp.canton==k).values
        U[m]=src.reindex(Dp.year[m]).values
    X=np.column_stack([U[:,0],U[:,1],U[:,2]-U[:,5],U[:,3]-U[:,5],U[:,4]-U[:,5],U[:,5],Dp.s_l0.values,Dp.s_l1.values,Dp.s_l2.values])
    y=Dp.dm.values; ok=~np.isnan(X).any(1)
    yy=pd.Series(y[ok]); XX=pd.DataFrame(X[ok]); g=Dp.year.values[ok]
    yd=yy.values-yy.groupby(g).transform('mean').values; Xd=XX.values-XX.groupby(g).transform('mean').values
    b=np.linalg.lstsq(Xd,yd,rcond=None)[0]; return b
b0=est(); print('\n=== A2. permutation: observed cum. offset (u_l3):',round(b0[5],4),' lead u_f2:',round(b0[0],4),' contemporaneous u_l0-u_l3 coef sum check')
rng=np.random.default_rng(1); dist=[]
for i in range(1500):
    p=rng.permutation(cans); perm=dict(zip(cans,p)); bb=est(perm); dist.append([bb[5],bb[0],bb[1]])
dist=np.array(dist)
print('perm p (|cum offset|):',(np.abs(dist[:,0])>=abs(b0[5])).mean().round(3),' perm sd',dist[:,0].std().round(3),' 2.5/97.5 pct',np.percentile(dist[:,0],[2.5,97.5]).round(3))
print('perm p (lead f2):',(np.abs(dist[:,1])>=abs(b0[0])).mean().round(3),' perm sd',dist[:,1].std().round(3))
# leave-one-canton-out for cumulative offset
print('\n=== A3. leave-one-canton-out cum offset (u_l3) range')
res=[]
for k in cans:
    s=Dp[Dp.canton!=k].copy(); s['u_c0']=s.u_l0-s.u_l3; s['u_c1']=s.u_l1-s.u_l3; s['u_c2']=s.u_l2-s.u_l3
    ff=pf.feols('dm ~ u_f2+u_f1+u_c0+u_c1+u_c2+u_l3+s_l0 | year',data=s,vcov={'CRV1':'canton'}); res.append((k,ff.coef()['u_l3'],ff.se()['u_l3']))
r=pd.DataFrame(res,columns=['drop','b','se']).round(3); print(r.sort_values('b').head(3).to_string(index=False)); print(r.sort_values('b').tail(3).to_string(index=False))
# ---------- B: FFA LU check
ffa=pd.read_pickle('data/ffa_gdn5000.pkl'); print('\nFFA cols',ffa.columns.tolist(),'nr sample',ffa.nr.astype(str).head(3).tolist())
ffa['nr']=ffa.nr.astype(str); ffa['bfs']=ffa.nr.str[2:].astype(int)
mr=pd.read_pickle('data/multipliers_raw.pkl'); ktm=mr[['bfs','canton']].drop_duplicates('bfs')
ffa=ffa.merge(ktm,on='bfs',how='left'); print('unmatched share',ffa.canton.isna().mean().round(3))
ac=sorted(ffa.account.astype(str).unique()); print('accounts (len<=2 or 3):',[a for a in ac if len(a)<=3][:70])
ffa.to_pickle('data/ffa_with_canton.pkl')
