"""
Stage 04/21 — Detect municipal mergers from year-over-year code
disappearance in the multiplier panel (cross-check for Stage 05/the HGV).

Reads   : data/multipliers_raw.pkl (Stage 01);
          FTA/statistik-dbst-np-gemeinde-YYYY-auswertung-de.xls* (source 2)
Writes  : data/spatial_all.pkl, data/disappearing_codes.pkl
Feeds   : Stage 05 and Stage 06, which use disappearing_codes.pkl to confirm
          97.5% of disappearing multiplier codes are explained by mergers in
          the official register (paper, Section 3 / Appendix A).
"""

import pandas as pd, numpy as np, glob, re, warnings
warnings.filterwarnings("ignore")
# 1) district (Bezirk) per municipality-year from FTA sheet '0' (2010-2019); fall back to 2019 for later years
sp=[]
for f in sorted(glob.glob("FTA/statistik-dbst-np-gemeinde-20*-auswertung-de.xls*")):
    y=int(re.search(r"gemeinde-(\d{4})",f).group(1))
    xl=pd.ExcelFile(f); df=xl.parse('0',header=None)
    d=df[pd.to_numeric(df[0],errors="coerce").notna() & pd.to_numeric(df[2],errors="coerce").notna()].copy()
    out=pd.DataFrame({"year":y,"kt_nr":pd.to_numeric(d[0]).astype(int),"bfs":pd.to_numeric(d[2]).astype(int),"name":d[3].values,"bez_nr":pd.to_numeric(d[4],errors="coerce").values})
    sp.append(out)
sp=pd.concat(sp); sp.to_pickle("data/spatial_all.pkl")
print(sp.groupby("year").size().to_dict())
# 2) code disappearances from ESTV multiplier panel
m=pd.read_pickle("data/multipliers_raw.pkl")
codes=m.groupby("year").bfs.apply(set).to_dict()
can=m.drop_duplicates("bfs").set_index("bfs").canton
disap=[]
for y in range(2011,2026):
    gone=codes[y-1]-codes[y]
    for b in gone:
        disap.append({"year":y,"bfs":b,"canton":can.get(b)})
disap=pd.DataFrame(disap)
print(disap.groupby("year").size().to_dict())
# 3) district of disappearing codes (use year y-1 classification if <=2019, else 2019)
def dist_of(b,y):
    yy=min(y-1,2019)
    r=sp[(sp.year==yy)&(sp.bfs==b)]
    if len(r)==0:
        r=sp[(sp.bfs==b)].sort_values("year").tail(1)
    return (r.bez_nr.iloc[0], r.kt_nr.iloc[0]) if len(r) else (np.nan,np.nan)
tmp=[dist_of(b,y) for b,y in zip(disap.bfs,disap.year)]
disap["bez_nr"]=[t[0] for t in tmp]; disap["kt_nr"]=[t[1] for t in tmp]
print("disappearing codes w/o district:", disap.bez_nr.isna().sum(), "of", len(disap))
disap.to_pickle("data/disappearing_codes.pkl")
print(disap.groupby("canton").size().sort_values(ascending=False).head(12).to_dict())
