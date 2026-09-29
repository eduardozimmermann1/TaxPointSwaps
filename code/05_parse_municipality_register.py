"""
Stage 05/21 — Parse the BFS historised municipality register (eCH-0071) and
identify every merger-involved municipality.

Reads   : hgv/**/eCH0071_*.xml (source 4);
          data/disappearing_codes.pkl (Stage 04, for the cross-check print)
Writes  : data/hgv_records.pkl, data/hgv_districts.pkl, data/hgv_mutations.pkl
Feeds   : Stage 06 (the "stable" 1,916-municipality sample used in every
          regression in the paper) and the merger counts in Appendix A.
"""

import xml.etree.ElementTree as ET, pandas as pd, numpy as np, glob
matches = sorted(glob.glob('hgv/**/eCH0071_*.xml', recursive=True))
assert matches, "No eCH0071_*.xml found under hgv/ — check the HGV zip was extracted there (see DATA.md, source 4)"
p = matches[-1]  # most recent vintage if more than one is present
print(f"Using HGV file: {p}")
root=ET.parse(p).getroot()
rows=[]
for m in root.iter('municipality'):
    rows.append({c.tag:(c.text or '').strip() for c in m})
h=pd.DataFrame(rows)
for c in ['municipalityAdmissionDate','municipalityAbolitionDate','municipalityDateOfChange']:
    h[c]=pd.to_datetime(h[c],errors='coerce')
h['municipalityId']=h['municipalityId'].astype(int)
print(h.shape)
print('EntryMode',h.municipalityEntryMode.value_counts().to_dict())
print('Status',h.municipalityStatus.value_counts().to_dict())
print('AdmMode',h.municipalityAdmissionMode.value_counts().to_dict())
print('AbolMode',h.municipalityAbolitionMode.value_counts().to_dict())
h.to_pickle('data/hgv_records.pkl')
# districts
drows=[]
for d in root.iter('district'):
    drows.append({c.tag:(c.text or '').strip() for c in d})
dd=pd.DataFrame(drows); dd.to_pickle('data/hgv_districts.pkl')
print(dd.columns.tolist()); print(dd.head(3).to_string())
# window mutations
w0,w1=pd.Timestamp('2008-01-01'),pd.Timestamp('2025-12-31')
ab=h[(h.municipalityAbolitionDate>=w0)&(h.municipalityAbolitionDate<=w1)].copy()
ad=h[(h.municipalityAdmissionDate>w0)&(h.municipalityAdmissionDate<=w1)&(h.municipalityAdmissionMode!='20')].copy()
print('abolished in window',len(ab),'admitted(non-first) in window',len(ad))
print(ab.municipalityAbolitionMode.value_counts().to_dict(), ad.municipalityAdmissionMode.value_counts().to_dict())
# mutation-level table
mut=[]
for num,g in ab.groupby('municipalityAbolitionNumber'):
    succ=h[(h.municipalityAdmissionNumber==num)]
    mut.append(dict(num=num,date=g.municipalityAbolitionDate.iloc[0],kt=g.cantonAbbreviation.iloc[0],
        n_ab=len(g),ab_ids=sorted(g.municipalityId.tolist()),ab_names=list(g.municipalityLongName),
        adm_ids=sorted(succ.municipalityId.tolist()),adm_names=list(succ.municipalityLongName),abmode=g.municipalityAbolitionMode.iloc[0]))
mut=pd.DataFrame(mut).sort_values('date')
mut.to_pickle('data/hgv_mutations.pkl')
print('mutations in window',len(mut)); print(mut.n_ab.value_counts().sort_index().to_dict())
print(mut[mut.n_ab>=2].groupby(mut.date.dt.year).size().to_dict())
print(mut[mut.n_ab>=2].groupby('kt').size().sort_values(ascending=False).to_dict())
for k,d in [('GL','2010'),('VD','2012'),('LU','2013'),('AG','2012')]:
    x=mut[(mut.kt==k)&(mut.date.dt.year==int(d))&(mut.n_ab>=2)]
    print(k,d); print(x[['num','date','ab_ids','adm_ids','adm_names']].head(4).to_string())
# compare to ESTV disappearing codes
dc=pd.read_pickle('data/disappearing_codes.pkl'); print(type(dc), getattr(dc,'shape',None)); print(dc.head(3).to_string() if hasattr(dc,'head') else list(dc)[:5])
mr=pd.read_pickle('data/multipliers_raw.pkl'); print(mr.columns.tolist()); print(mr.head(2).to_string())
