"""
Stage 06/21 — Build municipal adjacency from swissBOUNDARIES3D, construct
the stable 1,916-municipality sample, and tabulate the 45 canton-level
multiplier events.

Reads   : geo/swissBOUNDARIES3D_1_5_LV95_LN02.gpkg (source 5);
          data/hgv_records.pkl (Stage 05); data/multipliers_raw.pkl (Stage 01)
Writes  : data/geo_mun.pkl, data/adj_pairs.pkl, data/geo_geom.pkl,
          data/stable_bfs.pkl, data/events_table.pkl, data/cant_events.pkl
Feeds   : the stable sample (stable_bfs.pkl) underlies every subsequent
          regression; events_table.pkl feeds paper Table 1 / Figure 1 via
          Stage 11.
"""

import pandas as pd, numpy as np, geopandas as gpd, shapely, warnings
warnings.filterwarnings('ignore')
h=pd.read_pickle('data/hgv_records.pkl'); mr=pd.read_pickle('data/multipliers_raw.pkl')
g=gpd.read_file('geo/swissBOUNDARIES3D_1_5_LV95_LN02.gpkg',layer='tlm_hoheitsgebiet',engine='pyogrio')
print(g.objektart.value_counts().to_dict(), g.icc.value_counts().to_dict())
g=g[(g.objektart=='Gemeindegebiet')&(g.icc=='CH')].copy()
g['geometry']=shapely.force_2d(g.geometry.values)
gd=g.dissolve(by='bfs_nummer',aggfunc={'name':'first','kantonsnummer':'first','einwohnerzahl':'sum','gem_flaeche':'sum'}).reset_index()
gd['x']=gd.geometry.centroid.x; gd['y']=gd.geometry.centroid.y
gd=gd.rename(columns={'bfs_nummer':'bfs','kantonsnummer':'kt_nr'}); gd['kt_nr']=gd.kt_nr.astype(int)
print('current CH municipalities',len(gd))
gs=gd[['bfs','kt_nr','geometry']]
j=gpd.sjoin(gs,gs,how='inner',predicate='intersects',lsuffix='a',rsuffix='b')
pairs=j[j.bfs_a!=j.bfs_b][['bfs_a','kt_nr_a','bfs_b','kt_nr_b']].drop_duplicates().reset_index(drop=True)
pairs['cross']=pairs.kt_nr_a!=pairs.kt_nr_b
print('adjacent pairs',len(pairs),'cross-canton',int(pairs.cross.sum()))
gd.drop(columns='geometry').to_pickle('data/geo_mun.pkl'); pairs.to_pickle('data/adj_pairs.pkl')
gd[['bfs','geometry']].to_pickle('data/geo_geom.pkl')
# ---- stable municipalities
ab=h[h.municipalityAbolitionDate.notna()].copy()
ab['eff']=(ab.municipalityAbolitionDate+pd.Timedelta(days=1)).dt.year
m29=ab[(ab.municipalityAbolitionMode=='29')&(ab.eff>=2011)&(ab.eff<=2025)]
nums=set(m29.municipalityAbolitionNumber)
inv=h[h.municipalityAbolitionNumber.isin(nums)|h.municipalityAdmissionNumber.isin(nums)]
merger_ids=set(inv.municipalityId)
gone=set(m29.municipalityId)-set(gd.bfs)
print('merger-involved ids',len(merger_ids),'disappeared ids',len(gone))
pres=mr.groupby('bfs').year.agg(['min','max','count']).reset_index()
full=set(pres[pres['count']==16].bfs)
stable=sorted([b for b in full if b not in merger_ids and b in set(gd.bfs)])
print('ESTV codes',len(pres),'present all 16y',len(full),'stable',len(stable))
dc=pd.read_pickle('data/disappearing_codes.pkl')
print('ESTV disappearing codes',dc.bfs.nunique(),'explained by HGV merger set',dc.bfs.isin(merger_ids).mean().round(3))
pd.Series(stable,name='bfs').to_frame().to_pickle('data/stable_bfs.pkl')
# ---- events
cant=mr.groupby(['canton_id','canton','year']).inc_c.agg(['mean','nunique','min','max']).reset_index()
print('cantons with non-uniform cantonal multiplier within year:',cant[cant['nunique']>1].groupby('canton').size().to_dict())
cant=cant.sort_values(['canton','year']); cant['dc']=cant.groupby('canton')['mean'].diff()
ms=mr[mr.bfs.isin(stable)].sort_values(['bfs','year']).copy()
ms['dm']=ms.groupby('bfs').inc_m.diff()
ev=[]
for _,r in cant[cant.dc.abs()>=2].iterrows():
    x=ms[(ms.canton==r.canton)&(ms.year==r.year)].dm.dropna()
    if len(x)==0: continue
    ev.append(dict(kt=r.canton,year=int(r.year),c_prev=r['mean']-r.dc,dc=r.dc,n=len(x),mean_dm=x.mean(),med_dm=x.median(),
      sh_comp=(np.abs(x+r.dc)<=1).mean(),sh_zero=(x==0).mean(),sh_opp=(np.sign(x)==-np.sign(r.dc)).mean()))
ev=pd.DataFrame(ev); ev.to_pickle('data/events_table.pkl')
print(ev.round(2).to_string())
