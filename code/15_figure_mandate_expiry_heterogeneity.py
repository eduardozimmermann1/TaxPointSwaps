"""
Stage 15/21 — Mandate-expiry heterogeneity: who reversed the Luzern swap
once free to, and placebo-year benchmarking against fiscal capacity.

Reads   : data/multipliers_raw.pkl (01); data/stable_bfs.pkl (06);
          data/fta_panel.pkl (03)
Writes  : data/lu_rebound.pkl, paper/figs/fig5_rebound.pdf
Feeds   : paper Figure 5 (b) and the fiscal-capacity heterogeneity discussion
          in Section 5.4.
"""

import pandas as pd, numpy as np, statsmodels.formula.api as smf, warnings, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
warnings.filterwarnings('ignore'); plt.rcParams.update({'font.size':8,'axes.spines.top':False,'axes.spines.right':False})
mr=pd.read_pickle('data/multipliers_raw.pkl'); stable=set(pd.read_pickle('data/stable_bfs.pkl').bfs); fta=pd.read_pickle('data/fta_panel.pkl'); fta['bfs']=fta.bfs.astype(int)
ms=mr[mr.bfs.isin(stable)].sort_values(['bfs','year']).copy(); ms['dm']=ms.groupby('bfs').inc_m.diff()
kq=fta.pivot_table(index='bfs',columns='year',values='kopfquote')
def zcap(bfs_idx,year):
    s=np.log(kq[year].reindex(bfs_idx).clip(lower=1)); return (s-s.mean())/s.std()
ev={'LU':(2019,2021),'VD':(2010,2013),'NE':(2013,2015)}   # (capacity year, first free year)
out={}; rows=[]
for k,(cy,fy) in ev.items():
    d=ms[(ms.canton==k)&(ms.year==fy)].set_index('bfs'); d['z']=zcap(d.index,cy); d=d.dropna(subset=['z','dm'])
    r=smf.ols('dm ~ z',data=d).fit(cov_type='HC1'); out[k]=(r.params['z'],r.bse['z'],r.pvalues['z'],int(r.nobs)); print(k,'first free year',fy,'slope',round(r.params['z'],3),'se',round(r.bse['z'],3),'p',round(r.pvalues['z'],3),'n',int(r.nobs),' mean dm',round(d.dm.mean(),2),'share !=0',round((d.dm!=0).mean(),2))
    if k=='LU':
        dl=d.copy(); rng=np.random.default_rng(5); b0=r.params['z']; perm=[np.polyfit(rng.permutation(dl.z.values),dl.dm.values,1)[0] for _ in range(5000)]
        print('  LU randomisation p:',(np.abs(perm)>=abs(b0)).mean().round(4)); dl['rev']=(dl.dm>=5).astype(int)
        rr=smf.ols('rev ~ z',data=dl).fit(cov_type='HC1'); print('  LPM full reversal (dm>=5):',round(rr.params['z'],3),round(rr.bse['z'],3),round(rr.pvalues['z'],3),'share',dl.rev.mean().round(3))
        from scipy.stats import spearmanr; print('  Spearman',spearmanr(dl.z,dl.dm))
        LUd=dl
# placebo years: slope of dm on z in non-event years, per canton
pl={}
for k,(cy,fy) in ev.items():
    evy={'LU':[2014,2020,2021,2022,2025],'VD':[2011,2012,2013],'NE':[2014,2015]}[k]; sl=[]
    for y in range(2012,2025):
        if y in evy: continue
        d=ms[(ms.canton==k)&(ms.year==y)].set_index('bfs'); d['z']=zcap(d.index,cy); d=d.dropna(subset=['z','dm'])
        if len(d)<15: continue
        sl.append((y,np.polyfit(d.z,d.dm,1)[0]))
    pl[k]=sl; print(k,'placebo-year slopes: mean',round(np.mean([s for _,s in sl]),3),' sd',round(np.std([s for _,s in sl]),3),' min/max',round(min(s for _,s in sl),3),round(max(s for _,s in sl),3),' n years',len(sl))
LUpl=dict(pl['LU']); print('LU placebo slopes by year:',{y:round(s,2) for y,s in pl['LU'].items()} if isinstance(pl['LU'],dict) else {y:round(s,2) for y,s in pl['LU']})
# general benchmark: all stable munis, dm ~ z (z within canton, cap year 2012) with canton x year FE
import pyfixest as pf
g=ms[(ms.year>=2013)&(ms.year<=2019)&(ms.canton!='AR')].copy(); g=g[g.dm.abs()<=40]; g['lk']=np.log(kq[2012].reindex(g.bfs).clip(lower=1).values); g['z']=g.groupby('canton').lk.transform(lambda s:(s-s.mean())/s.std()); g['cy']=g.canton+'_'+g.year.astype(str)
gg=pf.feols('dm ~ z | cy',data=g.dropna(subset=['z','dm']),vcov={'CRV1':'canton'}); print('general benchmark slope (all cantons, 2013-19):',round(gg.coef()['z'],3),'se',round(gg.se()['z'],3))
# figure
fig,axs=plt.subplots(1,2,figsize=(7.0,2.9),gridspec_kw={'width_ratios':[1,1.15]})
ax=axs[0]; rng=np.random.default_rng(2); ax.scatter(LUd.z,LUd.dm+rng.uniform(-.25,.25,len(LUd)),s=14,c='#c0392b',alpha=.75,edgecolor='none'); xs=np.linspace(LUd.z.min(),LUd.z.max(),10); b=np.polyfit(LUd.z,LUd.dm,1); ax.plot(xs,np.polyval(b,xs),c='k',lw=1)
ax.axhline(0,c='grey',lw=.5); ax.set_xlabel('Fiscal capacity (z-score, log federal tax per capita, 2019)'); ax.set_ylabel('Change in municipal multiplier 2020$\\to$2021 (pts)'); ax.set_title('(a) Luzern: first free year after the swap',fontsize=8)
ax=axs[1]; lab=['LU 2021\n(event)','VD 2013\n(event)','NE 2015\n(event)','LU\nplacebo yrs','VD\nplacebo yrs','NE\nplacebo yrs']; est=[out['LU'][0],out['VD'][0],out['NE'][0]]+[np.mean([s for _,s in pl[k]]) for k in ['LU','VD','NE']]
lo=[out[k][0]-1.96*out[k][1] for k in ['LU','VD','NE']]+[np.min([s for _,s in pl[k]]) for k in ['LU','VD','NE']]; hi=[out[k][0]+1.96*out[k][1] for k in ['LU','VD','NE']]+[np.max([s for _,s in pl[k]]) for k in ['LU','VD','NE']]
cols=['#c0392b']*3+['#7f8c8d']*3
for i in range(6): ax.plot([i,i],[lo[i],hi[i]],c=cols[i],lw=1.4); ax.scatter(i,est[i],c=cols[i],s=22,zorder=3)
ax.axhline(0,c='k',lw=.5); ax.set_xticks(range(6)); ax.set_xticklabels(lab,fontsize=6.5); ax.set_ylabel('Slope of $\\Delta m$ on capacity (pts per s.d.)'); ax.set_title('(b) Events: 95% CI; placebo years: mean and range',fontsize=8)
fig.tight_layout(); fig.savefig('paper/figs/fig5_rebound.pdf'); plt.close()
LUd.to_pickle('data/lu_rebound.pkl')
