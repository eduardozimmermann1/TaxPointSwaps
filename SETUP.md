# Local setup and run order

This describes how to lay out the raw data (see `DATA.md` for where to get
each one), then run the pipeline end to end, before pushing to GitHub.

## 1. Folder layout

Create this structure at the repository root, alongside `code/` and `paper/`:

```
.
├── code/                          (already in this repo)
├── data/                          (empty — scripts write .pkl here)
├── paper/
│   ├── figs/                      (empty — scripts write output PDFs here)
│   └── tables/                    (empty — scripts write output .tex here)
├── Tax_Multipliers/                Source 1
│   └── estv_income_rates_2010.xlsx ... estv_income_rates_2025.xlsx
├── FTA/                            Source 2
│   ├── statistik-dbst-np-gemeinde-2010-auswertung-de.xls ... -2019-auswertung-de.xlsx
│   ├── statistik-dbst-np-gden-2020-mit-belastung-normalfall-de.xlsx
│   ├── statistik-dbst-np-gden-2021-mit-belastung-normalfall-de.xlsx
│   └── statistik-dbst-np-gden-2022-mit-belastung-normalfall.xlsx
├── ffa/                            Source 3
│   └── fs_gdn/gdn_ab_5000.csv
├── hgv/                            Source 4 (extract anywhere under here)
│   └── dz-b-00.04-hgv-02.20260101/1.2.0/eCH0071_260101.xml
├── geo/                            Source 5
│   └── swissBOUNDARIES3D_1_5_LV95_LN02.gpkg
├── gb/                             Source 6 (see conversion step below)
│   └── gb_raw.txt
└── estv/                           Source 7
    └── geo_2010.xlsx ... geo_2025.xlsx
```

Before running anything:

```bash
mkdir -p data paper/figs paper/tables
```

No script creates these directories itself; writing a pickle or a figure to
a directory that does not exist yet raises `FileNotFoundError`.

Source 6 is a PDF, not a text file; convert it once before running script
`19`:

```bash
pdftotext -raw Globalbilanz_1.pdf gb/gb_raw.txt
```

## 2. Run

One command, from the project root, runs all 21 stages in dependency order:

```bash
python3 code/run_pipeline.py
```

It checks the seven raw sources first and stops with a specific message if
any is missing; creates `data/`, `paper/figs/`, `paper/tables/` if they
don't already exist; converts the Globalbilanz PDF to text if that hasn't
been done yet; then runs each stage as its own subprocess, printing a `✓`
and the elapsed time after each one, and stopping immediately — with the
full Python traceback — on the first failure, so a stage never runs on
incomplete inputs.

A full run takes about three minutes. It ends with a manifest listing every
`.pkl`, `.pdf` and `.tex` file produced, and checks that off against the
exact set the paper's figures and tables require:

```
paper/figs/  (6 figures)
paper/tables/  (7 tables)
✓ All 6 expected figures and 7 expected table fragments are present.
```

If a file is missing from the manifest, the run stops there and names it —
open the corresponding `code/NN_*.py` (its docstring says what it reads and
writes) to see why.

## 3. Before pushing to GitHub

Add a `.gitignore` so the raw data and generated pickles are not committed
(`DATA.md` documents where to get them instead of bundling them):

```
Tax_Multipliers/
FTA/
ffa/
hgv/
geo/
gb/
estv/
data/
```
