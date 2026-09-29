"""
Stage 03/21 — Build the federal direct-tax panel (fiscal-capacity proxy).

Reads   : FTA/statistik-dbst-np-gemeinde-YYYY-auswertung-de.xls* (source 2)
Writes  : data/fta_panel.pkl
Feeds   : Stages 15 and 17-18 (mandate-expiry heterogeneity and the "who
          reversed" checks) — the per-capita federal tax yield used as the
          fiscal-capacity control in Figure 5 and its surrounding text.
"""

import pandas as pd, numpy as np, glob, re, warnings
warnings.filterwarnings("ignore")

def to_num(s):
    s = pd.Series(s).replace({"*": np.nan, "-": 0, "–": 0})
    return pd.to_numeric(s, errors="coerce")

def parse_old(xl, sheet):
    df = xl.parse(sheet, header=None)
    d = df[pd.to_numeric(df[0], errors="coerce").notna() & pd.to_numeric(df[1], errors="coerce").notna()].copy()
    d["bfs"] = pd.to_numeric(d[1]).astype(int)
    d["kt_nr"] = pd.to_numeric(d[0]).astype(int)
    d["name"] = d[2]
    return d

def data_cols(d):
    return [c for c in d.columns if isinstance(c, int) and c >= 4]

rows = []
for f in sorted(glob.glob("FTA/statistik-dbst-np-gemeinde-20*-auswertung-de.xls*")):
    y = int(re.search(r"gemeinde-(\d{4})", f).group(1))
    xl = pd.ExcelFile(f)
    d141, d143, d144, d4 = (parse_old(xl, s) for s in ("141", "143", "144", "4"))
    out = pd.DataFrame({"bfs": d141.bfs.values, "kt_nr": d141.kt_nr.values, "name": d141.name.values})
    c = data_cols(d141)
    out["n_tp"] = to_num(d141[c[-1]]).values
    out["n_tp_75plus"] = to_num(d141[c[-2]]).values
    for nm, dd, key in (("ti", d143, "ti"), ("tax", d144, "tax")):
        cc = data_cols(dd)
        t = pd.DataFrame({"bfs": dd.bfs.values, f"{key}_tot": to_num(dd[cc[-1]]).values, f"{key}_75plus": to_num(dd[cc[-2]]).values})
        out = out.merge(t, on="bfs", how="left")
    cc = data_cols(d4)
    t = pd.DataFrame({"bfs": d4.bfs.values, "tax_all": to_num(d4[cc[-3]]).values, "kopfquote": to_num(d4[cc[-2]]).values, "pop": to_num(d4[cc[-1]]).values})
    out = out.merge(t, on="bfs", how="left")
    out["year"] = y
    rows.append(out)

def parse_new(xl, sheet):
    df = xl.parse(sheet, header=None)
    h = df.index[df[2].astype(str).str.strip().eq("Gemeinde ID")][0]
    d = df.iloc[h + 1:].copy()
    d = d[pd.to_numeric(d[2], errors="coerce").notna()].copy()
    d["kt_nr"] = pd.to_numeric(d[0], errors="coerce")
    d["kt_nr"] = d["kt_nr"].ffill()
    d["bfs"] = pd.to_numeric(d[2]).astype(int)
    d["name"] = d[3]
    hdr = [str(x) for x in df.iloc[h].tolist()]
    return d, hdr

for y, f in [(2020, "FTA/statistik-dbst-np-gden-2020-mit-belastung-normalfall-de.xlsx"),
             (2021, "FTA/statistik-dbst-np-gden-2021-mit-belastung-normalfall-de.xlsx"),
             (2022, "FTA/statistik-dbst-np-gden-2022-mit-belastung-normalfall.xlsx")]:
    xl = pd.ExcelFile(f)
    d111, h111 = parse_new(xl, "111"); d112, _ = parse_new(xl, "112"); d113, _ = parse_new(xl, "113")
    d121, h121 = parse_new(xl, "121")
    out = pd.DataFrame({"bfs": d111.bfs.values, "kt_nr": d111.kt_nr.values, "name": d111.name.values})
    def tot(dd, hh):
        return pd.Series(to_num(dd[len(hh) - 1]).values, index=dd.bfs.values)
    out["n_tp"] = tot(d111, h111).reindex(out.bfs).values
    out["ti_tot"] = tot(d112, _).reindex(out.bfs).values if False else pd.Series(to_num(d112[[c for c in d112.columns if isinstance(c,int)][-1]]).values, index=d112.bfs.values).reindex(out.bfs).values
    out["tax_tot"] = pd.Series(to_num(d113[[c for c in d113.columns if isinstance(c,int)][-1]]).values, index=d113.bfs.values).reindex(out.bfs).values
    labs = h121[4:]
    cnt = pd.DataFrame({lab: to_num(d121[4 + i]).values for i, lab in enumerate(labs)}, index=d121.bfs.values)
    def sumcls(keys):
        cols = [c for c in cnt.columns if any(k in c for k in keys)]
        return cnt[cols].sum(axis=1, min_count=1).reindex(out.bfs).values
    out["n_tp_75plus"] = sumcls(["75'001", "100'001", "200'001", "500'001", "1'000'001"])
    out["n_tp_200plus"] = sumcls(["200'001", "500'001", "1'000'001"])
    out["n_tp_500plus"] = sumcls(["500'001", "1'000'001"])
    out["n_tp_1m"] = sumcls(["1'000'001"])
    out["year"] = y
    rows.append(out)
    print(y, "classes:", labs)

fta = pd.concat(rows, ignore_index=True)
fta.to_pickle("data/fta_panel.pkl")
print(fta.groupby("year").agg(n=("bfs", "size"), ntp=("n_tp", "sum"), ntp_na=("n_tp", lambda s: s.isna().sum()), pop=("pop", "sum"), tax=("tax_tot", "sum")).to_string())
