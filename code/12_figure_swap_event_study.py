"""
Stage 12/21 — Event-study figure for the three large mandated swaps
(Luzern 2020, Neuchâtel 2014, Vaud 2011-12) against clean control cantons.

Reads   : data/multipliers_raw.pkl (01); data/stable_bfs.pkl (06);
          data/cant_events.pkl (07)
Writes  : data/swap_es.pkl, paper/figs/fig2_swap_es.pdf
Feeds   : paper Figure 2 and Table 2 (Section 5.1).
"""

import pandas as pd, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':8,'axes.spines.top':False,'axes.spines.right':False})
mr=pd.read_pickle('data/multipliers_raw.pkl'); stable=set(pd.read_pickle('data/stable_bfs.pkl').bfs)
cant=pd.read_pickle('data/cant_events.pkl')[['canton','year','inc_c','dc']]
ms=mr[mr.bfs.isin(stable)][['bfs','canton','year','inc_m','inc_c']].copy(); ms['T']=ms.inc_m+ms.inc_c
Mw=ms.pivot(index='bfs',columns='year',values='inc_m'); Tw=ms.pivot(index='bfs',columns='year',values='T'); kt=ms.drop_duplicates('bfs').set_index('bfs').canton
events=[('LU',2020,'Luzern 2020 (AFR18)',2021),('NE',2014,'Neuchâtel 2014',2019),('VD',2011,'Vaud 2011--12',2015)]
fig,axs=plt.subplots(2,3,figsize=(7.2,4.6),sharey='row'); summ=[]
for j,(k,t0,lab,tmax) in enumerate(events):
    yrs=[y for y in range(t0-4,min(t0+5,tmax)+1) if 2010<=y<=2025]
    win=cant[(cant.year>=t0-4)&(cant.year<=t0+5)]; bad=set(win[win.dc.abs()>=1].canton)|{k,'AR'}
    ctrl=[c for c in cant.canton.unique() if c not in bad]
    def gapvar(W,treated,ctrls):
        base=W[t0-1]; d=W[yrs].sub(base,axis=0); dk=d.groupby(kt.reindex(d.index)).mean()
        return dk.loc[treated]-dk.loc[ctrls].mean()
    for r,(W,ttl) in enumerate([(Mw,'Municipal multiplier'),(Tw,'Total burden $c+m$')]):
        ax=axs[r,j]; g=gapvar(W,k,ctrl)
        for q in ctrl:
            o=[c for c in ctrl if c!=q]; ax.plot(yrs,gapvar(W,q,o).values,c='#bbbbbb',lw=.7)
        ax.plot(yrs,g.values,c='#c0392b' if r==0 else 'black',lw=1.8,marker='o',ms=3)
        if r==0:
            cc=cant[cant.canton==k].set_index('year').inc_c; ax.plot(yrs,(cc.reindex(yrs)-cc[t0-1]).values,c='#2471a3',lw=1.2,ls='--')
        ax.axhline(0,c='k',lw=.4); ax.axvline(t0-.5,c='k',lw=.4,ls=':')
        if r==0: ax.set_title(lab,fontsize=8)
        if j==0: ax.set_ylabel(ttl+'\n(points, vs clean controls)')
        summ.append(dict(event=f'{k}{t0}',var='m' if r==0 else 'T',**{f'h{y-t0}':round(float(g[y]),2) for y in yrs},ctrl=','.join(ctrl)))
axs[0,0].plot([],[],c='#2471a3',ls='--',label='cantonal multiplier'); axs[0,0].plot([],[],c='#c0392b',label='treated'); axs[0,0].plot([],[],c='#bbbbbb',label='placebo cantons'); axs[0,0].legend(frameon=False,fontsize=6.5,loc='lower left')
fig.tight_layout(); fig.savefig('paper/figs/fig2_swap_es.pdf'); plt.close()
s=pd.DataFrame(summ); pd.set_option('display.width',250); print(s.drop(columns='ctrl').to_string()); print(s[['event','ctrl']].drop_duplicates().to_string()); s.to_pickle('data/swap_es.pkl')
