"""
Stage 10/21 — Luzern case-study financial outcomes from the FFA panel
(tax revenue, transfers, operating expenditure/revenue by account).

Reads   : data/ffa_with_canton.pkl (09); data/multipliers_raw.pkl (01)
Writes  : data/ffa_outcomes.pkl
Feeds   : paper Table 5/9 and Figure 4 (Section 5.4 incidence discussion).
"""

import pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore'); pd.set_option('display.width',220)
f=pd.read_pickle('data/ffa_with_canton.pkl'); f['account']=f.account.astype(str)
print('account length dist',f.account.str.len().value_counts().to_dict())
a3=f[f.account.str.len()==3].copy()
print('4xx accounts:',sorted(a3[a3.account.str.startswith('4')].account.unique())); print('3xx accounts:',sorted(a3[a3.account.str.startswith('3')].account.unique()))
def agg(mask,name): 
    return a3[mask].groupby(['canton','bfs','year']).amount.sum().rename(name)
S=pd.concat([agg(a3.account=='400','tax400'),agg(a3.account=='401','tax401'),agg(a3.account.str.startswith('40'),'tax40'),
 agg(a3.account.str.startswith('46'),'trans_in'),agg(a3.account.str.startswith('36'),'trans_out'),agg(a3.account=='462','fila_in'),agg(a3.account=='362','fila_out'),
 agg(a3.account.str.startswith('30'),'personnel'),agg(a3.account.str.startswith('31'),'goods'),agg(a3.account.isin(['330','331','332','333','334','335','336','337','338','339']),'deprec'),
 agg(a3.account.str[:2].isin(['30','31','33','34','35','36']),'exp_op'),agg(a3.account.str[:2].isin(['40','41','42','43','44','45','46']),'rev_op')],axis=1).fillna(0).reset_index()
S.to_pickle('data/ffa_outcomes.pkl')
ctrl=['BL','GE','JU','UR','VS','ZH']
mr=pd.read_pickle('data/multipliers_raw.pkl')[['bfs','year','inc_m','inc_c']]
S=S.merge(mr,on=['bfs','year'],how='left')
# balanced panel for LU and controls 2016-2023 with positive tax400
yrs=list(range(2016,2024)); G=S[S.canton.isin(['LU']+ctrl)&S.year.isin(yrs)]
ok=G.groupby('bfs').year.nunique(); ok=ok[ok==len(yrs)].index; G=G[G.bfs.isin(ok)]
print('LU munis',G[G.canton=='LU'].bfs.nunique(),' control munis',G[G.canton!='LU'].bfs.nunique(), G[G.canton!='LU'].groupby('canton').bfs.nunique().to_dict())
def path(var,base=2019):
    P=G.pivot_table(index=['canton','bfs'],columns='year',values=var); P=P[(P>0).all(axis=1)] if var not in ['fila_in','fila_out'] else P
    L=np.log(P); L=L.sub(L[base],axis=0); return L
out={}
for v in ['tax400','tax401','tax40','trans_in','trans_out','personnel','goods','exp_op','rev_op']:
    L=path(v); lu=L[L.index.get_level_values(0)=='LU'].mean(); co=L[L.index.get_level_values(0)!='LU'].mean()
    # canton-level placebo: gap at 2020 and 2021 for each canton vs others
    cm=L.groupby(level=0).mean()
    gaps={c:(cm.loc[c]-cm.drop(c).mean()) for c in cm.index}
    p20=(np.abs(pd.Series({c:gaps[c][2020] for c in gaps}))>=abs(gaps['LU'][2020])).mean()
    p22=(np.abs(pd.Series({c:gaps[c][2022] for c in gaps}))>=abs(gaps['LU'][2022])).mean()
    out[v]=pd.Series({**{f'gap{y}':(lu-co)[y] for y in [2017,2018,2020,2021,2022,2023]},'perm_p2020':p20,'perm_p2022':p22,'n_LU':int((L.index.get_level_values(0)=='LU').sum())})
print(pd.DataFrame(out).T.round(3).to_string())
# mechanical prediction: log change in municipal multiplier LU vs controls (same municipalities)
M=G.pivot_table(index=['canton','bfs'],columns='year',values='inc_m'); Ml=np.log(M); Ml=Ml.sub(Ml[2019],axis=0)
print('\nlog multiplier gap LU-ctrl:',(Ml[Ml.index.get_level_values(0)=='LU'].mean()-Ml[Ml.index.get_level_values(0)!='LU'].mean()).round(3).to_dict())
# fiscal-capacity heterogeneity within LU: mechanical revenue change (CHF) = 10pts * base ; base=tax400/(inc_m/100) in 2019
lu=S[(S.canton=='LU')&(S.year.isin([2019,2021,2022]))].pivot_table(index='bfs',columns='year',values=['tax400','inc_m','exp_op','trans_in'])
print('\nLU FFA munis:',len(lu)); 
