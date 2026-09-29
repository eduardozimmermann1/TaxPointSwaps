"""
Stage 11/21 — Classify the 45 canton-level events (mandated swap /
small-canton swap / unilateral) and render the event-classification
figure and table.

Reads   : data/events_table.pkl (06)
Writes  : data/events_classified.pkl, data/event_class_summary.pkl,
          paper/figs/fig1_events.pdf, paper/tables/events.tex
Feeds   : paper Table 1, Figure 1, and Appendix Table 8 (via events.tex).
"""

import pandas as pd, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
ev=pd.read_pickle('data/events_table.pkl'); ev=ev[ev.kt!='AR'].copy()
def cls(r):
    if r.n>=10 and r.sh_comp>=0.8 and r.sh_opp>=0.85: return 'Mandated swap'
    if r.n<10 and r.sh_opp>=0.99 and abs(r.mean_dm+r.dc)<=2: return 'Small-canton swap'
    return 'Unilateral'
ev['cls']=ev.apply(cls,axis=1); ev.to_pickle('data/events_classified.pkl')
print(ev.cls.value_counts().to_dict())
fig,ax=plt.subplots(figsize=(5.2,4.2)); col={'Mandated swap':'#c0392b','Small-canton swap':'#e59866','Unilateral':'#2c3e50'}
for k,g in ev.groupby('cls'): ax.scatter(g.dc,g.mean_dm,c=col[k],label=k,s=28,alpha=.85,edgecolor='white',linewidth=.4)
xs=np.array([-32,32]); ax.plot(xs,-xs,ls='--',c='grey',lw=.8); ax.axhline(0,c='grey',lw=.5); ax.axvline(0,c='grey',lw=.5)
for _,r in ev[ev.cls!='Unilateral'].iterrows(): ax.annotate(f"{r.kt}{str(r.year)[2:]}",(r.dc,r.mean_dm),xytext=(4,4),textcoords='offset points',fontsize=7)
ax.text(-31,27,'full offset: $\\Delta m=-\\Delta c$',fontsize=7,color='grey',rotation=-30)
ax.set_xlabel('Cantonal multiplier change $\\Delta c$ (points)'); ax.set_ylabel('Mean municipal change $\\Delta m$, same year (points)'); ax.legend(frameon=False,fontsize=7,loc='upper right'); ax.set_xlim(-33,33); ax.set_ylim(-16,28)
fig.tight_layout(); fig.savefig('paper/figs/fig1_events.pdf'); plt.close()
# class summary
ev['offset_ratio']=-ev.mean_dm/ev.dc
S=ev.groupby('cls').agg(events=('kt','size'),cantons=('kt','nunique'),mean_abs_dc=('dc',lambda x:x.abs().mean()),med_offset=('offset_ratio','median'),mean_offset=('offset_ratio','mean'),sh_opp=('sh_opp','mean'),sh_zero=('sh_zero','mean'),n_munis=('n','sum')).round(2)
print(S.to_string()); S.to_pickle('data/event_class_summary.pkl')
def row(r): return f"{r.kt} & {r.year} & {r.c_prev:.0f} & {r.dc:+.1f} & {r.n} & {r.mean_dm:+.2f} & {r.sh_comp:.2f} & {r.sh_zero:.2f} & {r.cls} \\\\"
L=["\\begin{longtable}{llrrrrrrl}","\\caption{Canton-level multiplier changes of at least 2 points, 2011--2025, and same-year municipal response}\\label{tab:events}\\\\","\\toprule","Canton & Year & $c_{t-1}$ & $\\Delta c$ & $N$ & Mean $\\Delta m$ & Share offset & Share unchanged & Class \\\\","\\midrule","\\endfirsthead","\\toprule","Canton & Year & $c_{t-1}$ & $\\Delta c$ & $N$ & Mean $\\Delta m$ & Share offset & Share unchanged & Class \\\\","\\midrule","\\endhead"]
L+=[row(r) for _,r in ev.iterrows()]
L+=["\\bottomrule","\\multicolumn{9}{p{0.95\\textwidth}}{\\footnotesize \\emph{Notes:} $c_{t-1}$: cantonal income-tax multiplier in the previous year (\\% of the simple tax). $N$: number of stable municipalities in the canton. ``Share offset'': share of municipalities with $|\\Delta m+\\Delta c|\\le 1$. ``Share unchanged'': share with $\\Delta m=0$. Appenzell Ausserrhoden (2014, 2018) is excluded because of implausible municipal jumps in the source data.}\\\\","\\end{longtable}"]
open('paper/tables/events.tex','w').write("\n".join(L))
