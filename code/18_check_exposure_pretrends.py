"""
Stage 18/21 — Exposure-by-year event studies confirming that FFA-outcome
regressions on the projected burden fail pre-trend tests, while multiplier
levels themselves show no such pre-trend.

Reads   : data/multipliers_raw.pkl (01); data/stable_bfs.pkl (06);
          data/ffa_outcomes.pkl (10); data/fta_panel.pkl (03);
          data/globalbilanz.pkl (16)
Writes  : (console output only — no persisted file)
Feeds   : the specific "joint pre-trend p = 0.001" claim for operating
          expenditure and the operating balance, quoted directly in Section
          5.4 of the paper. This stage is load-bearing for that sentence
          even though it writes no file — do not skip it.
"""

import pandas as pd, numpy as np, pyfixest as pf, warnings
warnings.filterwarnings('ignore'); pd.set_option('display.width',220)
S=pd.read_pickle('data/ffa_outcomes.pkl'); gb=pd.read_pickle('data/globalbilanz.pkl').set_index('bfs'); fta=pd.read_pickle('data/fta_panel.pkl'); fta['bfs']=fta.bfs.astype(int)
pop=fta[fta.year==2016].set_index('bfs')['pop']; gb['pop16']=pop.reindex(gb.index)
gb['loss100']=-gb.total/gb.pop16/100; gb['swap100']=-gb.steuerfussabtausch/gb.pop16/100
L=S[(S.canton=='LU')&S.bfs.isin(gb.index)&S.year.between(2016,2023)].copy(); L=L.join(gb[['loss100','swap100','pop16']],on='bfs'); L['bal']=L.rev_op-L.exp_op
for v in ['tax400','trans_in','trans_out','exp_op','rev_op','bal']: L[v+'_pc']=L[v]/L.pop16
ok=L.groupby('bfs').year.nunique(); L=L[L.bfs.isin(ok[ok==8].index)]; print('FFA LU munis with 2016-2023:',L.bfs.nunique())
def es(df,y,x,years,ref=2019):
    d=df.copy()
    for k in years:
        if k!=ref: d[f'e{k}']=d[x]*(d.year==k)
    rhs='+'.join(f'e{k}' for k in years if k!=ref)
    f=pf.feols(f'{y} ~ {rhs} | bfs + year',data=d,vcov={'CRV1':'bfs'}); c=f.coef(); se=f.se(); p=f.pvalue()
    return {k:(c[f'e{k}'],se[f'e{k}'],p[f'e{k}']) for k in years if k!=ref}, f
for x in ['loss100','swap100']:
    print(f'\n=== FFA outcomes (CHF per capita) on {x} (CHF 100 per capita) x year; ref 2019; muni+year FE; cluster muni; coef (p)')
    rows={}
    for v in ['tax400_pc','trans_in_pc','trans_out_pc','exp_op_pc','rev_op_pc','bal_pc']:
        r,f=es(L,v,x,list(range(2016,2024))); rows[v]={k:f'{a:+.0f} ({p:.2f})' for k,(a,s,p) in r.items()}
        # joint pre-trend (2016-2018) Wald
        try:
            import numpy as _n
            names=[f'e{k}' for k in (2016,2017,2018)]; b=f.coef()[names].values; V=f._vcov[[list(f.coef().index).index(n) for n in names]][:,[list(f.coef().index).index(n) for n in names]]
            from scipy.stats import chi2; W=float(b@np.linalg.solve(V,b)); rows[v]['joint_pre_p']=f'{1-chi2.cdf(W,3):.3f}'
        except Exception as e: rows[v]['joint_pre_p']='na'
    print(pd.DataFrame(rows).T.to_string())
# multiplier levels, 71 stable
mr=pd.read_pickle('data/multipliers_raw.pkl'); stable=set(pd.read_pickle('data/stable_bfs.pkl').bfs)
M=mr[(mr.canton=='LU')&mr.bfs.isin(stable)&mr.year.between(2014,2023)][['bfs','year','inc_m']].join(gb[['loss100','swap100']],on='bfs'); print('\nMultiplier levels, stable LU munis:',M.bfs.nunique())
for x in ['loss100','swap100']:
    r,f=es(M,'inc_m',x,list(range(2014,2024))); print(x,{k:f'{a:+.2f} ({p:.2f})' for k,(a,s,p) in r.items()})
