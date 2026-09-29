"""
Stage 01/21 — Build the cantonal/municipal multiplier panel.

Reads   : Tax_Multipliers/estv_income_rates_YYYY.xlsx (2010-2025, source 1)
Writes  : data/multipliers_raw.pkl
Feeds   : the entire paper — every table and figure in Sections 3-5 starts
          from this panel (36,619 municipality-year rows, 2010-2025).
"""

import pandas as pd, numpy as np, glob, re, warnings
warnings.filterwarnings("ignore")
rows=[]
for f in sorted(glob.glob("Tax_Multipliers/estv_income_rates_*.xlsx")):
    y=int(re.search(r"(\d{4})",f).group(1))
    df=pd.read_excel(f, header=None, skiprows=4)
    df=df.iloc[:, :20]
    df.columns=["canton_id","canton","bfs","commune",
                "inc_c","inc_m","inc_ch_prot","inc_ch_rc","inc_ch_cc",
                "wea_c","wea_m","wea_ch_prot","wea_ch_rc","wea_ch_cc",
                "prof_c","prof_m","prof_ch","cap_c","cap_m","cap_ch"]
    df["year"]=y
    rows.append(df)
m=pd.concat(rows, ignore_index=True)
m=m.dropna(subset=["bfs"])
m["bfs"]=pd.to_numeric(m["bfs"], errors="coerce")
for c in m.columns[4:20]:
    m[c]=pd.to_numeric(m[c], errors="coerce")
m=m.dropna(subset=["bfs"])
m["bfs"]=m["bfs"].astype(int)
m.to_pickle("data/multipliers_raw.pkl")
print(m.shape)
print(m.groupby("year").agg(n=("bfs","nunique"), inc_c_na=("inc_c",lambda s:s.isna().sum()), inc_m_na=("inc_m",lambda s:s.isna().sum())).T)
print(m.groupby("year").canton.nunique().T)
# dup check
print("dups:", m.duplicated(["bfs","year"]).sum())
print(m[m.duplicated(["bfs","year"], keep=False)].sort_values(["bfs","year"]).head(10))
