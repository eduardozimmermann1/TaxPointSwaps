"""
Stage 21/21 — Distinguish a multiplier-driven cantonal burden shock from a
schedule-driven one (rules out the naive positive coefficient as mechanical
schedule co-movement).

Re-uses  : build()/fit() from Stage 13, via Stage 20's re-use of it.
Reads    : data/estv_geo_panel.pkl (19); data/multipliers_raw.pkl (01);
           data/stable_bfs.pkl (06); data/cant_events.pkl (07)
Writes   : (console output only — no persisted file)
Feeds    : the "multiplier-driven cantonal shock" row of paper Table 7 and
           the accompanying discussion in Section 5.5. Load-bearing for
           those specific numbers even though it writes no file.
"""

exec(open('code/20_table_effective_burden_robustness.py').read().split("D=build(L=3,F=2)")[0])
# simple-tax base S (pp of gross income per 100 multiplier points) and multiplier-driven cantonal burden change
st_=set(stable)
cc2=cant[['canton','year','inc_c','dc']].copy(); cb=cb.merge(cc2,on=['canton','year'],how='left'); cb['S']=cb.bc/(cb.inc_c/100); cb=cb.sort_values(['canton','year']); cb['S_lag']=cb.groupby('canton').S.shift(1); cb['dS_rel']=cb.S/cb.S_lag-1
cb['dBm']=cb.S_lag*cb.dc/100   # multiplier-driven cantonal burden change (pp)
print('canton-years (2011-25) with a schedule/deduction change (|dS/S|>0.5%):',int((cb.dS_rel.abs()>0.005).sum()),'of',int(cb.dS_rel.notna().sum()),'; among them with NO multiplier change (|dc|<0.5):',int(((cb.dS_rel.abs()>0.005)&(cb.dc.abs()<0.5)).sum()))
# mechanical test: in canton-years with no multiplier change, does the communal burden move with the cantonal burden?
Gs2=Gs.merge(cb[['canton','year','dbc','dc','dS_rel']],on=['canton','year'],how='left'); T=Gs2[(Gs2.dc.abs()<0.5)&(Gs2.dbc.abs()>0.005)&Gs2.dbm.notna()&Gs2.bfs.isin(st_)&(Gs2.canton!='AR')&~Gs2.canton.isin(['VS','GE'])]
import statsmodels.formula.api as smf
r=smf.ols('dbm ~ dbc',data=T).fit(cov_type='cluster',cov_kwds={'groups':T.canton.astype('category').cat.codes}); mc=(mr[mr.bfs.isin(T.bfs.unique())].inc_m/mr[mr.bfs.isin(T.bfs.unique())].inc_c).median()
print('tariff-only canton-years: n obs',len(T),' slope of d(communal burden) on d(cantonal burden):',round(r.params['dbc'],3),'(se',round(r.bse['dbc'],3),') ; median m/c in these obs',round(mc,3))
# DL with multiplier-driven cantonal burden shock (schedule held at t-1) as regressor
cb['dcs2']=np.where(cb.swap,cb.dBm,0.0); cb['dcu2']=np.where(cb.swap,0.0,cb.dBm)
for l in range(-2,4): cb['gu_'+('f%d'%-l if l<0 else 'l%d'%l)]=cb.groupby('canton').dcu2.shift(l)
for l in range(0,3): cb['gs_l%d'%l]=cb.groupby('canton').dcs2.shift(l).fillna(0)
cb['gu_c0']=cb.gu_l0-cb.gu_l3; cb['gu_c1']=cb.gu_l1-cb.gu_l3; cb['gu_c2']=cb.gu_l2-cb.gu_l3
D=build(L=3,F=2); D=D.merge(Gs[['bfs','year','dbm']],on=['bfs','year'],how='left').merge(cb[['canton','year']+[c for c in cb.columns if c.startswith(('gu_','gs_'))]],on=['canton','year'],how='left').dropna(subset=['dbm','gu_f2','gu_l0','gu_l3'])
for name,d in [('All',D),('Excl. VS, GE',D[~D.canton.isin(['VS','GE'])])]:
    f=pf.feols('dbm ~ gu_f2+gu_f1+gu_c0+gu_c1+gu_c2+gu_l3+gs_l0+gs_l1+gs_l2 | year',data=d,vcov={'CRV1':'canton'}); c=f.coef(); s=f.se(); p=f.pvalue()
    print(f'{name:14s} shock = multiplier-driven cantonal burden change: cum offset {c["gu_l3"]:+.3f} ({s["gu_l3"]:.3f}) p={p["gu_l3"]:.2f}; lead t+2 {c["gu_f2"]:+.3f} (p={p["gu_f2"]:.3f}); swap same-year {c["gs_l0"]:+.3f} ({s["gs_l0"]:.3f}); N={f._N}')
