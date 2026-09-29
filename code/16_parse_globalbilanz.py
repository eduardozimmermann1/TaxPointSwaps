"""
Stage 16/21 — Parse and internally validate Kanton Luzern's Globalbilanz 1
(AFR18 ballot-brochure projection by municipality).

Reads   : gb/gb_raw.txt (source 6 — see SETUP.md for the required
          `pdftotext -raw` conversion step run before this stage)
Writes  : data/globalbilanz.pkl
Feeds   : Stages 17 and 18 ("who reversed" analysis, paper Figure 5(a)).
"""

import re, pandas as pd, numpy as np
t=open('gb/gb_raw.txt',encoding='utf-8').read().splitlines()
num=r"(?:-?\d[\d']*|-)"
def tonum(x): return 0.0 if x=='-' else float(x.replace("'",""))
A_cols=['total','percap','aufgabenreform','wasserbau','strassen_oev','vernetzung','mehrwert','mehrwert_umz','volksschule','weiterbildung','schulentw','fremdspr','kantonsschule','musikschule','instrumental','unterbestand','ggst','hast','erbschaft','personalsteuer','steuerfussabtausch']
B_cols=['ipv','el_ahv','el_iv','el_verw','feuerwehr','stgr2020','fa_total','tla','bla','ila','ra_pot','ra_horiz','besitz_total','bs_tla','bs_bla','bs_ila','bs_ra']
A=[];B=[];totA={};totB={}
reA=re.compile(r"^(\d{4})\s+(\D.*?)\s+((?:"+num+r"\s+){20}"+num+r")\s*$")
reB=re.compile(r"^\s*((?:"+num+r"\s+){16}"+num+r")\s+(\d{4})\s+(\D.*?)\s*$")
reAt=re.compile(r"^Total (Kanton|Gemeinden)\s+((?:"+num+r"\s+){20}"+num+r")\s*$")
reBt=re.compile(r"^\s*((?:"+num+r"\s+){16}"+num+r")\s+Total (Kanton|Gemeinden)\s*$")
for ln in t:
    m=reA.match(ln)
    if m: A.append([int(m.group(1)),m.group(2)]+[tonum(x) for x in m.group(3).split()]); continue
    m=reB.match(ln)
    if m: B.append([int(m.group(2)),m.group(3)]+[tonum(x) for x in m.group(1).split()]); continue
    m=reAt.match(ln)
    if m: totA[m.group(1)]=[tonum(x) for x in m.group(2).split()]; continue
    m=reBt.match(ln)
    if m: totB[m.group(2)]=[tonum(x) for x in m.group(1).split()]
dA=pd.DataFrame(A,columns=['bfs','name']+A_cols); dB=pd.DataFrame(B,columns=['bfs','nameB']+B_cols)
print('parsed A rows',len(dA),'B rows',len(dB),' dup A',dA.bfs.duplicated().sum(),' dup B',dB.bfs.duplicated().sum(), ' totals found A',list(totA),'B',list(totB))
gb=dA.merge(dB,on='bfs',how='outer',indicator=True); print(gb._merge.value_counts().to_dict()); print('name mismatches',int((gb.name!=gb.nameB).sum()))
gb=gb.drop(columns=['_merge','nameB'])
# identity checks
comp=['wasserbau','strassen_oev','vernetzung','mehrwert','mehrwert_umz','volksschule','weiterbildung','schulentw','fremdspr','kantonsschule','musikschule','instrumental','unterbestand','ggst','hast','erbschaft','personalsteuer','steuerfussabtausch','ipv','el_ahv','el_iv','el_verw','feuerwehr']
gb['chk_aufg']=gb[comp].sum(axis=1)-gb.aufgabenreform
gb['chk_total']=gb.aufgabenreform+gb.stgr2020+gb.fa_total+gb.besitz_total-gb.total
print('max |aufgabenreform - sum(components)|',gb.chk_aufg.abs().max(),' max |total - (aufg+StGR+FA+Besitz)|',gb.chk_total.abs().max())
# compare column sums with 'Total Gemeinden' rows
tg=pd.Series(totA['Gemeinden'],index=A_cols); sums=gb[A_cols].sum()
d=(sums-tg); print('col sums vs Total Gemeinden (A): max abs diff',d.abs().max().round(1),' worst cols:',d.abs().sort_values(ascending=False).head(3).round(0).to_dict())
tgb=pd.Series(totB['Gemeinden'],index=B_cols); d2=gb[B_cols].sum()-tgb; print('col sums vs Total Gemeinden (B): max abs diff',d2.abs().max().round(1),d2.abs().sort_values(ascending=False).head(3).round(0).to_dict())
gb.to_pickle('data/globalbilanz.pkl')
print(gb[['bfs','name','total','percap','steuerfussabtausch']].sort_values('percap').head(6).to_string(index=False)); print(gb[['bfs','name','total','percap','steuerfussabtausch']].sort_values('percap').tail(4).to_string(index=False))
print('sum swap (municipalities)',gb.steuerfussabtausch.sum(),' sum total',gb.total.sum(),' n',len(gb))
