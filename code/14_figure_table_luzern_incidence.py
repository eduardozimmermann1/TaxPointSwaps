"""
Stage 14/21 — Drift/asymmetry robustness checks and the Luzern incidence
figure/table (multiplier, tax, transfers, expenditure relative to controls).

Re-uses  : build()/fit() from Stage 13 (via exec of its source — run Stage 13
           first so this file exists to be read, though its pickle outputs
           are not required).
Reads    : data/ffa_outcomes.pkl (10); data/multipliers_raw.pkl (01)
Writes   : paper/tables/lu.tex, paper/tables/lu_full.tex, paper/figs/fig4_lu.pdf
Feeds    : paper Table 5/9, Figure 4 (Section 5.4).
"""

exec(open('code/13_figure_table_distributed_lag_robustness.py').read().split('specs=')[0])
import numpy as np
# (i) drift check: canton FE (canton-specific linear drift in levels) and municipality FE
d=build(L=3,F=2)
rhs_a=[f'a_f{l}' for l in (1,2)]+[f'ac{j}' for j in range(3)]+['a_l3','s_l0','s_l1','s_l2']
rhs_pn=[f'{nm}_f{l}' for nm in 'pn' for l in (1,2)]+[f'{nm}c{j}' for nm in 'pn' for j in range(3)]+['p_l3','n_l3','s_l0','s_l1','s_l2']
for fe in ['year','year + canton','year + bfs']:
    fb=pf.feols('dm ~ '+'+'.join(rhs_a)+' | '+fe,data=d,vcov={'CRV1':'canton'}); fa=pf.feols('dm ~ '+'+'.join(rhs_pn)+' | '+fe,data=d,vcov={'CRV1':'canton'})
    fu=pf.feols('dm ~ '+'+'.join([f'u_f{l}' for l in (1,2)]+[f'uc{j}' for j in range(3)]+['u_l3','s_l0','s_l1','s_l2'])+' | '+fe,data=d,vcov={'CRV1':'canton'})
    print(f"FE={fe:15s} |dc| cum {fb.coef()['a_l3']:+.3f} ({fb.se()['a_l3']:.3f}) | hikes {fa.coef()['p_l3']:+.3f} ({fa.se()['p_l3']:.3f}) | cuts {fa.coef()['n_l3']:+.3f} ({fa.se()['n_l3']:.3f}) | symmetric {fu.coef()['u_l3']:+.3f} ({fu.se()['u_l3']:.3f}) lead2 {fu.coef()['u_f2']:+.3f}")
# (ii) LU fiscal DiD
S=pd.read_pickle('data/ffa_outcomes.pkl'); mm=mr[['bfs','year','inc_m']]; S=S.merge(mm,on=['bfs','year'],how='left')
ctrl=['BL','GE','JU','UR','VS','ZH']; yrs=list(range(2016,2024))
G=S[S.canton.isin(['LU']+ctrl)&S.year.isin(yrs)]; ok=G.groupby('bfs').year.nunique(); G=G[G.bfs.isin(ok[ok==len(yrs)].index)]
def Lmat(var):
    P=G.pivot_table(index=['canton','bfs'],columns='year',values=var); P=P[(P>0).all(axis=1)]; L=np.log(P); return L.sub(L[2019],axis=0)
V={'inc_m':'Municipal multiplier','tax400':'Direct taxes, nat. persons (acct. 400)','trans_in':'Transfer revenue (acct. 46x)','trans_out':'Transfer expenditure (acct. 36x)','exp_op':'Operating expenditure','rev_op':'Operating revenue'}
rng=np.random.default_rng(3); fig,axs=plt.subplots(2,3,figsize=(7.2,4.4),sharex=True); tab=[]
for ax,(v,ttl) in zip(axs.ravel(),V.items()):
    L=Lmat(v); isLU=(L.index.get_level_values(0)=='LU'); A=L[isLU].values; B=L[~isLU].values; gap=A.mean(0)-B.mean(0)
    bt=np.array([A[rng.integers(0,len(A),len(A))].mean(0)-B[rng.integers(0,len(B),len(B))].mean(0) for _ in range(1000)]); lo,hi=np.percentile(bt,[2.5,97.5],axis=0)
    x=np.array(L.columns); ax.fill_between(x,lo,hi,color='#c0392b',alpha=.18,lw=0); ax.plot(x,gap,c='#c0392b',marker='o',ms=3,lw=1.5); ax.axhline(0,c='k',lw=.4); ax.axvline(2019.5,c='k',lw=.4,ls=':'); ax.set_title(ttl,fontsize=8)
    if v=='tax400': ax.axhline(-0.055,c='grey',ls='--',lw=.8); ax.text(2016,-0.075,'mechanical (-5.5%)',fontsize=6.5,color='grey')
    tab.append((v,ttl,len(A),len(B),[(int(y),round(float(g),3),round(float(l),3),round(float(h),3)) for y,g,l,h in zip(x,gap,lo,hi) if y>=2020]))
    print(v,'nLU',len(A),'nCtrl',len(B),' gaps 2018-2023:',[round(float(g),3) for g in gap[2:]],' CI2021',(round(float(lo[5]),3),round(float(hi[5]),3)))
for ax in axs[1]: ax.set_xlabel('Year')
axs[0,0].set_ylabel('Log gap, LU vs. controls\n(relative to 2019)'); axs[1,0].set_ylabel('Log gap, LU vs. controls\n(relative to 2019)')
fig.tight_layout(); fig.savefig('paper/figs/fig4_lu.pdf'); plt.close()
# Two renderings of the same numbers. lu.tex (main text, Table 5) carries
# point estimates only, so the table fits within the page margin (a wider
# version with inline 95% CI brackets in every cell overflows \textwidth —
# confirmed by an overfull \hbox warning during compilation). lu_full.tex
# (Appendix Table 9, set in landscape orientation in the paper) carries the
# full numbers including the CI brackets. Both come from the same `tab`.
Tc=["\\begin{tabular}{lcccc}","\\toprule","Outcome (log gap vs.\\ 2019) & 2020 & 2021 & 2022 & 2023 \\\\","\\midrule"]
for v,ttl,na,nb,vals in tab:
    Tc.append(ttl+' & '+' & '.join(f"{g:+.3f}" for y,g,l,h in vals)+' \\\\')
Tc+=["\\midrule",f"Municipalities (LU / controls) & \\multicolumn{{4}}{{c}}{{{tab[0][2]} / {tab[0][3]}}} \\\\","\\bottomrule","\\end{tabular}"]
open('paper/tables/lu.tex','w').write("\n".join(Tc))

Tf=["\\begin{tabular}{lcccc}","\\toprule","Outcome (log gap vs.\\ 2019) & 2020 & 2021 & 2022 & 2023 \\\\","\\midrule"]
for v,ttl,na,nb,vals in tab:
    Tf.append(ttl+' & '+' & '.join(f"{g:+.3f}" for y,g,l,h in vals)+' \\\\'); Tf.append(' & '+' & '.join(f"[{l:+.3f}, {h:+.3f}]" for y,g,l,h in vals)+' \\\\')
Tf+=["\\midrule",f"Municipalities (LU / controls) & \\multicolumn{{4}}{{c}}{{{tab[0][2]} / {tab[0][3]}}} \\\\","\\bottomrule","\\end{tabular}"]
open('paper/tables/lu_full.tex','w').write("\n".join(Tf))
