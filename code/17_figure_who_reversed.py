"""
Stage 17/21 — Regress the 2021 multiplier reversal on the projected AFR18
burden ("who reversed?").

Reads   : data/globalbilanz.pkl (16); data/ffa_outcomes.pkl (10);
          data/fta_panel.pkl (03); data/multipliers_raw.pkl (01);
          data/stable_bfs.pkl (06)
Writes  : data/lu_exposure.pkl, paper/figs/fig6_exposure.pdf
Feeds   : paper Figure 5(a) and the "Who reversed?" paragraph in Section 5.4.
"""

import pandas as pd, numpy as np, statsmodels.formula.api as smf, warnings, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy.stats import spearmanr
warnings.filterwarnings('ignore'); plt.rcParams.update({'font.size':8,'axes.spines.top':False,'axes.spines.right':False}); pd.set_option('display.width',220)
gb=pd.read_pickle('data/globalbilanz.pkl').set_index('bfs'); mr=pd.read_pickle('data/multipliers_raw.pkl'); stable=set(pd.read_pickle('data/stable_bfs.pkl').bfs)
fta=pd.read_pickle('data/fta_panel.pkl'); fta['bfs']=fta.bfs.astype(int); pop=fta[fta.year==2016].set_index('bfs')['pop']; kq=fta[fta.year==2019].set_index('bfs')['kopfquote']
gb['pop16']=pop.reindex(gb.index); print('pop16 available',gb.pop16.notna().sum(),'of',len(gb))
gb['net_pc']=gb.total/gb.pop16; print('corr(net_pc, given per-capita)',np.corrcoef(gb.net_pc,gb.percap)[0,1].round(4),' max abs diff',(gb.net_pc-gb.percap).abs().max().round(1))
gb['loss100']=-gb.net_pc/100; gb['swap100']=-gb.steuerfussabtausch/gb.pop16/100*(-1)*(-1)   # swap burden per capita (+ = loss), hundreds CHF
gb['swap100']=(-gb.steuerfussabtausch)/gb.pop16/100
gb['task100']=-((gb.aufgabenreform-gb.steuerfussabtausch)/gb.pop16)/100
gb['fa100']=-((gb.fa_total+gb.besitz_total+gb.stgr2020)/gb.pop16)/100
gb['base_pc']=gb.swap100*100*10   # simple-tax base per capita (CHF), = swap loss of 0.1 unit *10
print(gb[['loss100','swap100','task100','fa100','base_pc']].describe().round(2).to_string())
# --- validation of swap column against FFA revenue (2016)
S=pd.read_pickle('data/ffa_outcomes.pkl'); m16=mr[mr.year==2016].set_index('bfs').inc_m
v=S[(S.year==2016)&(S.canton=='LU')].set_index('bfs'); v=v.join(gb[['steuerfussabtausch']]).join(m16)
v['pred']=v.inc_m/100*(-v.steuerfussabtausch/0.10); v['rev']=v.tax400+v.tax401
r=(v.rev/v.pred); print('\nVALIDATION LU>=5000 (n=%d): median ratio FFA(400+401)/pred(m*base) = %.3f ; IQR %.3f-%.3f ; corr(log) = %.3f'%(len(v),r.median(),r.quantile(.25),r.quantile(.75),np.corrcoef(np.log(v.rev),np.log(v.pred))[0,1])); print('  Luzern city: FFA',v.loc[1061,'rev'],' pred',round(v.loc[1061,'pred']))
# --- LU multiplier panel
lu=mr[mr.canton=='LU'].pivot(index='bfs',columns='year',values='inc_m')
X=lu[[2019,2020,2021,2022]].dropna(); X.columns=['m2019','m2020','m2021','m2022']
X['d2020']=X.m2020-X.m2019; X['dev2020']=X.d2020+10; X['d2021']=X.m2021-X.m2020; X['net2021']=X.m2021-X.m2019; X['d2022']=X.m2022-X.m2021; X['net2022']=X.m2022-X.m2019
Z=X.join(gb[['loss100','swap100','task100','fa100','base_pc','name','pop16']],how='inner'); Z['stable']=Z.index.isin(stable); Z['lkq']=np.log(kq.reindex(Z.index)); 
print('\nLU municipalities in Globalbilanz',len(gb),' with 2019-2022 multipliers',len(Z),' stable',int(Z.stable.sum()))
dev=Z[Z.dev2020.abs()>0.5][['name','d2020','loss100','swap100']]; print('deviators 2020:',dev.to_string())
def ols(y,x,d,ctrl=''):
    d=d.dropna(subset=[y,x]); f=f'{y} ~ {x}'+(' + '+ctrl if ctrl else ''); r=smf.ols(f,data=d).fit(cov_type='HC1'); return r
def ri(y,x,d,B=5000,seed=1):
    d=d.dropna(subset=[y,x]); rng=np.random.default_rng(seed); b0=np.polyfit(d[x],d[y],1)[0]; return (np.abs([np.polyfit(rng.permutation(d[x].values),d[y].values,1)[0] for _ in range(B)])>=abs(b0)).mean()
for sname,D in [('stable (n=%d)'%int(Z.stable.sum()),Z[Z.stable]),('all with data (n=%d)'%len(Z),Z)]:
    print('\n===',sname)
    for y in ['d2021','net2021','net2022','d2022']:
        for x in ['loss100','swap100']:
            r=ols(y,x,D); rc=ols(y,x,D,'m2019'); print(f'{y:8s} ~ {x:8s}: slope {r.params[x]:+.3f} (se {r.bse[x]:.3f}) p={r.pvalues[x]:.3f} RIp={ri(y,x,D):.3f} | +m2019: {rc.params[x]:+.3f} (se {rc.bse[x]:.3f}) p={rc.pvalues[x]:.3f} | n={int(r.nobs)}')
D=Z[Z.stable]
r=smf.ols('d2021 ~ task100 + swap100 + fa100',data=D).fit(cov_type='HC1'); print('\ncomponents d2021:',r.params.round(3).to_dict(),' p:',r.pvalues.round(3).to_dict())
print('corr(loss100,swap100)',D.loss100.corr(D.swap100).round(2),' corr(loss100,lkq)',D.loss100.corr(D.lkq).round(2),' corr(swap100,lkq)',D.swap100.corr(D.lkq).round(2))
D=D.copy(); D['q']=pd.qcut(D.loss100,4,labels=['Q1 (relief)','Q2','Q3','Q4 (largest loss)']); print('\nby quartile of net loss:'); print(D.groupby('q').agg(n=('d2021','size'),mean_d2021=('d2021','mean'),share_up=('d2021',lambda s:(s>0).mean()),share_full=('d2021',lambda s:(s>=9).mean()),mean_loss=('loss100','mean')).round(2).to_string())
# --- placebo yearly slopes (stable LU)
ms=mr[mr.bfs.isin(stable)&(mr.canton=='LU')].sort_values(['bfs','year']).copy(); ms['dm']=ms.groupby('bfs').inc_m.diff(); ms=ms.join(gb[['loss100']],on='bfs')
pl=[]
for y in list(range(2012,2020))+[2023,2024]:
    if y==2014: continue
    d=ms[ms.year==y].dropna(subset=['dm','loss100']); 
    if len(d)>=20: pl.append((y,np.polyfit(d.loss100,d.dm,1)[0]))
print('\nplacebo-year slopes (dm on loss100), LU stable:',{y:round(s,2) for y,s in pl},' mean',round(np.mean([s for _,s in pl]),3),' sd',round(np.std([s for _,s in pl]),3))
# --- FFA outcomes on exposure (n~21)
print('\nFFA large LU municipalities: log change vs 2019 on loss100 (HC1)')
G=S[(S.canton=='LU')&(S.year.isin([2019,2021,2022]))].pivot_table(index='bfs',columns='year',values=['tax400','trans_in','exp_op','rev_op','trans_out'])
out=[]
for var in ['tax400','trans_in','trans_out','exp_op','rev_op']:
    for yy in [2021,2022]:
        d=pd.DataFrame({'y':np.log(G[(var,yy)]/G[(var,2019)]).replace([np.inf,-np.inf],np.nan)}).join(gb[['loss100']]).dropna()
        r=smf.ols('y ~ loss100',data=d).fit(cov_type='HC1'); out.append((var,yy,round(r.params['loss100'],4),round(r.bse['loss100'],4),round(r.pvalues['loss100'],3),len(d)))
print(pd.DataFrame(out,columns=['var','year','slope_per_100CHF','se','p','n']).to_string(index=False))
# --- figure
def label_no_overlap(ax, pts, fontsize=6, min_sep_pts=9.0):
    """pts: list of (x_data, y_data, text). Places each label with a small
    base offset, then nudges any label that would collide with one already
    placed (within min_sep_pts, in display points) further away, and draws
    a thin leader line back to its data point so the mapping stays clear
    even when two points sit close together (as Weggis/Greppen or
    Weggis/Vitznau do here)."""
    order = sorted(range(len(pts)), key=lambda i: pts[i][1])
    placed = []
    trans = ax.transData
    for idx in order:
        x, y, text = pts[idx]
        x_disp, y_disp = trans.transform((x, y))
        cand_y = y_disp + 4.0
        for (px, py) in placed:
            if abs(px - x_disp) < 40 and abs(cand_y - py) < min_sep_pts:
                cand_y = py + min_sep_pts
        placed.append((x_disp, cand_y))
        ax.annotate(text, (x, y), xytext=(4.0, cand_y - y_disp), textcoords='offset points',
                    fontsize=fontsize, ha='left', va='bottom',
                    arrowprops=dict(arrowstyle='-', lw=0.4, color='#888888', shrinkA=0, shrinkB=1))

fig,axs=plt.subplots(1,2,figsize=(7.0,2.9)); D=Z[Z.stable]; rng=np.random.default_rng(4)
for ax,x,lab in [(axs[0],'loss100','Net burden of AFR18 per capita (CHF 100; + = loss)'),(axs[1],'swap100','Mechanical loss from the tax-point swap per capita (CHF 100)')]:
    ax.scatter(D[x],D.d2021+rng.uniform(-.25,.25,len(D)),s=14,c='#c0392b',alpha=.75,edgecolor='none'); b=np.polyfit(D[x],D.d2021,1); xs=np.linspace(D[x].min(),D[x].max(),10); ax.plot(xs,np.polyval(b,xs),c='k',lw=1); ax.axhline(0,c='grey',lw=.5)
    ax.set_xlabel(lab); ax.set_ylabel('Change in municipal multiplier, 2020$\\to$2021 (pts)')
    top3 = D.sort_values(x).tail(3)
    label_no_overlap(ax, [(rw[x], rw.d2021, rw['name']) for _, rw in top3.iterrows()])
    ax.margins(x=0.18)
axs[0].set_title('(a) Net exposure (Globalbilanz 1)',fontsize=8); axs[1].set_title('(b) Swap component only',fontsize=8)
fig.tight_layout(); fig.savefig('paper/figs/fig6_exposure.pdf'); plt.close(); Z.to_pickle('data/lu_exposure.pkl')
