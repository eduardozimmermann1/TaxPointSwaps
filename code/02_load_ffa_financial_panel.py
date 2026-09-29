"""
Stage 02/21 — Load the FFA municipal financial statistics.

Reads   : ffa/fs_gdn/gdn_ab_5000.csv (source 3)
Writes  : data/ffa_gdn5000.pkl
Feeds   : Stage 09 (permutation inference / ffa_with_canton), which in turn
          feeds Stage 10 (Luzern financial outcomes) — paper Table 5/9 and
          Figure 4.
"""

import pandas as pd, numpy as np, time
pd.set_option("display.width",250); pd.set_option("display.max_rows",200)
t=time.time()
f=pd.read_csv("ffa/fs_gdn/gdn_ab_5000.csv", sep=";", dtype={"year":int,"nr":str,"municipality":str,"account":str,"function":str}, na_values=[""], keep_default_na=False)
f["function"]=f["function"].replace("", np.nan)
f["amount"]=pd.to_numeric(f["amount"], errors="coerce")
print(f.shape, time.time()-t)
print(f.year.min(), f.year.max())
print(f.groupby("year").nr.nunique().to_string())
f.to_pickle("data/ffa_gdn5000.pkl")
print(f.account.nunique(), "accounts;", f["function"].nunique(), "functions")
print(sorted(f.account.unique())[:80])
