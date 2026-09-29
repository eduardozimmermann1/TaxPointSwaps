"""
Stage 08/21 — Cross-border design: municipal response to a neighbouring
canton's unilateral changes and mandated swaps.

Reads   : data/fd_panel.pkl, data/cant_events.pkl (07); data/adj_pairs.pkl (06);
          data/multipliers_raw.pkl (01)
Writes  : data/fd_spatial.pkl
Feeds   : paper Table 4 and Section 5.3.
"""

import pandas as pd, numpy as np, pyfixest as pf, warnings
warnings.filterwarnings('ignore')
D=pd.read_pickle('data/fd_panel.pkl'); cant=pd.read_pickle('data/cant_events.pkl')
pairs=pd.read_pickle('data/adj_pairs.pkl'); mr=pd.read_pickle('data/multipliers_raw.pkl')
km=mr[['canton_id','canton']].drop_duplicates().set_index('canton_id').canton.to_dict()
px=pairs[pairs.cross].copy(); px['kb']=px.kt_nr_b.map(km)
ucols=['u_f2','u_f1','u_l0','u_l1','u_l2','u_l3']; scols=['s_f2','s_f1','s_l0','s_l1','s_l2','s_l3']
c2=cant[['canton','year']+ucols+scols].copy()
for c in ucols+scols: c2.loc[c2.canton=='AR',c]=0.0
for c in scols: c2[c]=-c2[c]           # neighbour's *mandated municipal-rate* change = -(cantonal swap change)
c2=c2.rename(columns={c:'nb_'+c for c in ucols+scols})
e=px[['bfs_a','kb']].merge(c2,left_on='kb',right_on='canton').drop(columns=['canton','kb'])
exp=e.groupby(['bfs_a','year']).mean().reset_index().rename(columns={'bfs_a':'bfs'})
exp[[c for c in exp.columns if c.startswith('nb_')]]=exp[[c for c in exp.columns if c.startswith('nb_')]].fillna(0)
D2=D.merge(exp,on=['bfs','year'],how='left'); nbc=[c for c in D2.columns if c.startswith('nb_')]
D2['border']=D2.bfs.isin(set(px.bfs_a)).astype(int); D2[nbc]=D2[nbc].fillna(0); D2['cy']=D2.canton+'_'+D2.year.astype(str)
print('stable munis in panel',D2.bfs.nunique(),' border(cross-canton adjacent):',D2[D2.border==1].bfs.nunique())
print('border munis by canton:',D2[D2.border==1].groupby('canton').bfs.nunique().to_dict())
# how many border muni-years have non-zero exposure
print('nonzero nb_u_l0 obs',int((D2.nb_u_l0!=0).sum()),' nonzero nb_s_l0 obs',int((D2.nb_s_l0!=0).sum()))
def show(fit,keep=None):
    t=fit.tidy()[['Estimate','Std. Error','Pr(>|t|)']].round(3)
    print(t.loc[[i for i in t.index if (keep is None or i in keep)]].to_string())
DD=D2.dropna(subset=['dm']).copy()
print('\n=== S1: dm on neighbours (cross-border) cantonal unilateral changes & mandated swap rate changes; canton x year FE')
f=pf.feols('dm ~ nb_u_f1+nb_u_l0+nb_u_l1+nb_u_l2+nb_s_f1+nb_s_l0+nb_s_l1+nb_s_l2 | cy',data=DD,vcov={'CRV1':'canton'}); show(f); print('N',f._N)
print('\n=== S2: cumulative (0..2) via reparam')
DD['nu_c0']=DD.nb_u_l0-DD.nb_u_l2; DD['nu_c1']=DD.nb_u_l1-DD.nb_u_l2
DD['ns_c0']=DD.nb_s_l0-DD.nb_s_l2; DD['ns_c1']=DD.nb_s_l1-DD.nb_s_l2
f2=pf.feols('dm ~ nb_u_f1+nu_c0+nu_c1+nb_u_l2+nb_s_f1+ns_c0+ns_c1+nb_s_l2 | cy',data=DD,vcov={'CRV1':'canton'}); show(f2,['nb_u_f1','nb_u_l2','nb_s_f1','nb_s_l2'])
print('\n=== S3: restrict to border municipalities only (control = border munis not exposed that year)')
fb=pf.feols('dm ~ nb_u_f1+nb_u_l0+nb_u_l1+nb_u_l2+nb_s_f1+nb_s_l0+nb_s_l1+nb_s_l2 | cy',data=DD[DD.border==1],vcov={'CRV1':'canton'}); show(fb); print('N',fb._N)
print('\n=== S4: add municipality FE (FD drift)')
fm=pf.feols('dm ~ nb_u_f1+nb_u_l0+nb_u_l1+nb_u_l2+nb_s_f1+nb_s_l0+nb_s_l1+nb_s_l2 | cy + bfs',data=DD,vcov={'CRV1':'canton'}); show(fm)
# swap-specific: list swap events with neighbours
sw=exp.merge(D[['bfs','canton']].drop_duplicates(),on='bfs')
for (k,y) in [('LU',2020),('VD',2011),('VD',2012),('NE',2014)]:
    x=e.merge(px[['bfs_a','kb']].rename(columns={'bfs_a':'bfs_a2'}),left_on='bfs_a',right_on='bfs_a2') if False else None
nbs={}
for (k,y) in [('LU',2020),('VD',2011),('NE',2014)]:
    kt=[i for i,v in km.items() if v==k][0]; s=set(px[px.kt_nr_b==kt].bfs_a)
    nbs[(k,y)]=(len(s), sorted(D[D.bfs.isin(s)].canton.unique()))
print('\nborder munis adjacent to swap canton (all, incl. non-stable):',{k:v[0] for k,v in nbs.items()}, {k:v[1] for k,v in nbs.items()})
DD.to_pickle('data/fd_spatial.pkl')
