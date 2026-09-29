# Data sources

All data used in this pipeline are public statistics published by Swiss
federal, cantonal, or municipal authorities. None are redistributed in this
repository; each raw source below must be obtained directly from the issuing
agency and placed at the local path shown, which is the path each script
expects relative to the repository root.

| # | Source | Agency | Vintage used | Local path expected by the scripts | Where to get it |
|---|---|---|---|---|---|
| 1 | Cantonal and municipal income-tax multipliers ("Grunddaten") | Federal Tax Administration (ESTV), Swiss Tax Calculator | 2010–2025, one workbook per year | `Tax_Multipliers/estv_income_rates_YYYY.xlsx` | `swisstaxcalculator.estv.admin.ch` → "Grunddaten" module (interactive; one export per year) |
| 2 | Federal direct tax statistics, natural persons, by municipality | Federal Tax Administration (ESTV) | 2010–2019 (used); later years exist in a different file layout and were not used | `FTA/statistik-dbst-np-gemeinde-YYYY-auswertung-de.xls*` | `https://www.estv.admin.ch/estv/de/home/die-estv/steuerstatistiken-estv/allgemeine-steuerstatistiken/direkte-bundessteuer/dbst-np-gemeinden-ab-1983.html` |
| 3 | Municipal financial statistics (accounts × function × year, municipalities ≥5,000 inhabitants) | Federal Finance Administration (EFV/FFA), Government Finance Statistics bundle | 2008–2024 | `ffa/fs_gdn/gdn_ab_5000.csv` | **Direct download, exact filename match confirmed:** `https://www.data.finance.admin.ch/static/assets/datasets/fs_dashboard/zip-e.zip` (listed on the official EFV page as "All files as a ZIP file"); the specific file this pipeline reads is listed separately as `https://www.data.finance.admin.ch/static/assets/datasets/fs_dashboard/gdn_ab_5000-e.csv` ("Municipalities with 5,000 inhabitants or more"). Landing page: `https://www.efv.admin.ch/en/overview-financial-statistics-data` |
| 4 | Historised municipality register (eCH-0071) | Federal Statistical Office (BFS) | Status 1 January 2026 | `hgv/dz-b-00.04-hgv-02.20260101/1.2.0/eCH0071_260101.xml` | **Direct download, confirmed live:** `https://www.agvchapp.bfs.admin.ch/file/xml/dz-b-00.04-hgv-02.zip` (catalog entry: `opendata.swiss/en/dataset/historisiertes-gemeindeverzeichnis-der-schweiz`) |
| 5 | Municipal boundary polygons (swissBOUNDARIES3D) | Federal Office of Topography (swisstopo) | January 2026 edition, LV95/LN02 (published 18 December 2025) | `geo/swissBOUNDARIES3D_1_5_LV95_LN02.gpkg` | **Official product page, confirmed live:** `https://www.swisstopo.admin.ch/en/landscape-model-swissboundaries3d` (or `/de/landschaftsmodell-swissboundaries3d`), which links to the **official download portal** `https://ogd.swisstopo.admin.ch/ch.swisstopo.swissboundaries3d`. **Stable STAC collection (always current edition):** `https://data.geo.admin.ch/browser/index.html#/collections/ch.swisstopo.swissboundaries3d`. **Direct file, 2026 edition:** `https://data.geo.admin.ch/ch.swisstopo.swissboundaries3d/swissboundaries3d_2026-01/swissboundaries3d_2026-01_2056_5728.gpkg.zip` |
| 6 | *Globalbilanz 1*: projected municipality-level fiscal effect of the AFR18 reform | Kanton Luzern | Version of the ballot brochure, figures as of the cantonal parliament's WAK committee, 31 January 2019 | `gb/gb_raw.txt` (plain text extracted from the original PDF; script `19` parses this text) | **Direct download, confirmed live and content-verified:** `https://www.lu.ch/-/media/Kanton/Dokumente/JSD/Wahlen_und_Abstimmungen/Abstimmungen_2019/Globalbilanz_1.pdf` |
| 7 | Tax burden statistics, "Geographical comparison" (effective tax burden by municipality) | Federal Tax Administration (ESTV), Swiss Tax Calculator | 2010–2025, one export per year: single taxpayer, no children, no church affiliation, gross income CHF 100,000 | `estv/geo_YYYY.xlsx` | `swisstaxcalculator.estv.admin.ch` → "Tax burden statistics" module (interactive; one export per year) |

Sources 1 and 7 were obtained interactively from the ESTV's Swiss Tax
Calculator (`swisstaxcalculator.estv.admin.ch`), which does not expose a bulk
API: source 1 from its "Grunddaten" (base data) module, one export per tax
year; source 7 from its "Tax burden statistics" module, selecting *Income and
wealth tax → Single, no children → Other/None (religion) → Geographical
comparison → Income → 100,000*, one export per tax year. Reproducing these
two sources requires repeating that same sequence of selections in the tool
for each year from 2010 to 2025.

## Verification notes (checked 29 September 2026)

Every link above was checked with a live HTTP fetch before being included
here. The strength of each check varies with what the fetch tool could
actually retrieve, from strongest to weakest:

- **Source 6 (Globalbilanz 1):** fully content-verified, not just live. The
  fetch returned the complete PDF text, and it matches the document
  originally supplied for this pipeline word for word and figure for figure
  (spot-checked against the Luzern municipality row,
  `1061 Luzern -12'732'019 -156 -11'784'258 ...`, identical down to the last
  digit). This is the one source in this table whose content, not merely its
  liveness, was confirmed.

- **Source 3 (FFA financial statistics):** exact filename match on the
  agency's own page. `efv.admin.ch/en/overview-financial-statistics-data`
  loaded in full and lists, verbatim, a file named `zip-e.zip` — the exact
  filename originally supplied for this pipeline — under a "Downloads"
  heading, and the specific `gdn_ab_5000-e.csv` file this pipeline reads,
  under "Municipalities with 5,000 inhabitants or more". Fetching either file
  directly failed with a server-side error, consistent with their size (the
  original `gdn_ab_5000.csv` alone is 95,870,524 bytes); their content was
  not inspected, but the exact filename match on the agency's own page is
  stronger evidence than a live fetch of a large binary would have added.

- **Source 4 (HGV):** confirmed live. The fetch resolved without a redirect
  and served a genuine `application/zip` file. This confirms the link is
  live, not that its contents are byte-identical to the copy used to build
  this pipeline's `data/hgv_records.pkl` — no such byte-level comparison was
  run.

- **Source 5 (swissBOUNDARIES3D):** confirmed live at three levels. The
  official product page loaded in full and confirmed the release date
  (18 December 2025), the four municipalities merged for the 2026 edition,
  the available formats (including GeoPackage), and the coordinate system
  (LV95/LN02) — and itself links to the `ogd.swisstopo.admin.ch` download
  portal as "swissBOUNDARIES3D - Download" (that portal returned only its
  JavaScript application shell to the fetch tool, expected for this kind of
  interactive OGD portal, not a sign of a wrong link). The direct
  2026-edition file link separately failed only because the response
  (over 30 MB) exceeded the checking tool's size limit, consistent with it
  being the genuine ~74 MB dataset rather than an error page. The stable
  STAC collection link was confirmed directly via the official API
  (`data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swissboundaries3d`),
  metadata current to 17 December 2025. The `.gpkg` file used to build this
  pipeline's `data/geo_mun.pkl` and `data/adj_pairs.pkl` has MD5
  `350707086b540d90563e5058ca9ef27b` (74,231,808 bytes); anyone
  re-downloading from any of the links above can compare against this hash
  after unzipping.

- **Sources 1, 2, 7:** landing/product pages confirmed live; sources 1 and 7
  require the manual interactive steps above and so have no single file to
  content-check.

Source 6 was additionally cross-checked at the processing level: the PDF was
converted to plain text (`pdftotext -raw`) before parsing, since its two data
tables ("Globalbilanz 1: Details Gemeinden", cantonal and communal columns)
are laid out as wide, multi-page tables that are easier to parse reliably
from the raw text stream than from the PDF's internal table structure.

## What is not included

An earlier, broader working set of scripts included exploratory and
superseded specifications: an early single-canton pre-trend diagnostic that
motivated moving to the multi-canton swap classification used in the final
design; an early heterogeneity probe superseded by the design in the current
`15_figure_mandate_expiry_heterogeneity.py`; a labour-market-region
classification that was never used by any later stage or cited in the paper;
an FFA-outcome-on-projected-exposure regression that fails pre-trend tests
(superseded by the event-study version that is in the pipeline, which
confirms and quantifies that same pre-trend problem); an ESTV municipal
tax-burden publication (2009–2018) superseded because its calculation
methodology differs from the 2010–2025 Swiss Tax Calculator series actually
used; and a set of FFA cantonal-level revenue tables explored for an
inheritance/gift-tax extension that was ultimately not pursued for this
paper. None of these feed a number in the final paper, so none of them are
part of the 21-stage pipeline in `code/`.
