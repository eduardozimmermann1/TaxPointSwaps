"""
Stage 19/21 — Parse the ESTV Swiss Tax Calculator's "geographical
comparison" exports (effective tax burden, single taxpayer, CHF 100,000,
every municipality, 2010-2025).

Reads   : estv/geo_YYYY.xlsx (source 7)
Writes  : data/estv_geo_panel.pkl
Feeds   : Stages 20 and 21 — paper Section 5.5 (effective-burden robustness).
"""

import pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore'); pd.set_option('display.width',240)
exp={2010:2596,2011:2551,2012:2495,2013:2408,2014:2352,2015:2324,2016:2294,2017:2255,2018:2222,2019:2212,2020:2202,2021:2172,2022:2148,2023:2136,2024:2131,2025:2121}
mr=pd.read_pickle('data/multipliers_raw.pkl'); st=set(pd.read_pickle('data/stable_bfs.pkl').bfs); out=[]; rows=[]
for y in range(2010,2026):
    d=pd.read_excel(f'estv/geo_{y}.xlsx',header=None)
    hdr=[str(d.iloc[i,0]) for i in range(0,3)]; yr=d.iloc[3,0]; inc=d.iloc[4,2]; cols=d.iloc[6,:].tolist()
    b=d.iloc[7:,:].copy(); b.columns=['kid','kt','bfs','name','tot_pct','tot','fed','cant','comm','church','pers'][:b.shape[1]]
    for c in ['bfs','tot_pct','tot','fed','cant','comm','church','pers']: b[c]=pd.to_numeric(b[c],errors='coerce')
    b['year']=y; chk=(b.tot-(b.fed+b.cant+b.comm+b.church+b.pers)).abs().max()
    mm=mr[mr.year==y][['bfs','canton','inc_c','inc_m']].drop_duplicates('bfs'); E=b.merge(mm,on='bfs',how='left'); mt=E.inc_c.notna().mean()
    E['d']=(E.comm/E.cant)/(E.inc_m/E.inc_c)-1; ok=(E.d.abs()<0.005)|E.d.isna()
    out.append(dict(year=y,file_year=yr,income=inc,hdr=hdr[0]+'|'+hdr[1]+'|'+hdr[2],rows=len(b),expected=exp[y],dup=int(b.bfs.duplicated().sum()),na=int(b[['tot','cant','comm']].isna().sum().sum()),max_id_err=chk,match_mult=round(mt,3),ratio_ok=round(ok.mean(),3),stable=int(b.bfs.isin(st).sum()),church_pos=int((b.church>0).sum()),
        bad_cantons=','.join(sorted(E[~ok].kt.value_counts().index[:6]))))
    rows.append(b)
S=pd.DataFrame(out); print(S.to_string(index=False)); P=pd.concat(rows,ignore_index=True); P.to_pickle('data/estv_geo_panel.pkl'); print(P.shape)
