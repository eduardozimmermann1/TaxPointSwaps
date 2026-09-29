# Offsetting by Mandate, Not by Choice
### Tax-Point Swaps and Vertical Fiscal Interaction among Swiss Municipalities

**Eduardo Dietrich Zimmermann** · September 2026

This repository contains the data-construction and empirical pipeline behind
*"Offsetting by Mandate, Not by Choice: Tax-Point Swaps and Vertical Fiscal
Interaction among Swiss Municipalities"* (`paper/main.tex`), a working paper
written as a writing sample for a PhD application to the Chair of Applied
Macroeconomics / KOF Swiss Economic Institute at ETH Zurich. It is shared here
as a reproducibility record and as a portfolio reference for that application,
not as a maintained software package.

## What the paper does

Swiss cantons and municipalities levy their income taxes as multipliers on a
common statutory base, so a point of the cantonal multiplier and a point of
the municipal multiplier are perfect substitutes for the taxpayer. The paper
asks whether municipalities offset changes in their canton's multiplier, and
whether any offsetting observed in the data is voluntary or legally mandated.
It combines a sixteen-year panel of municipal and cantonal multipliers with
the historised municipality register, municipal boundary polygons, municipal
financial statistics, and a canton's own projection of a specific reform's
fiscal impact, to (i) classify 45 large cantonal multiplier changes into
mandated "tax-point swaps" versus unilateral changes, (ii) estimate the
municipal response to each type in a distributed-lag design, (iii) test for
cross-border mimicry between neighbouring cantons, and (iv) study Luzern's
2020 reform (AFR18) as a case study of a mandated swap that a court later
struck down. The full argument, results, and limitations are in the paper
itself; this repository documents how every number in it was produced.

## Repository layout

```
code/     21 numbered Python scripts (one pipeline stage each) plus
          run_pipeline.py, the single entry point that runs all of them
paper/    main.tex, references.bib, figs/, tables/ — the paper's LaTeX source,
          ready to compile in Overleaf or locally (pdflatex + bibtex)
DATA.md   the seven public data sources used, with exact vintages and where
          each script expects to find them locally
SETUP.md  the local folder layout and the one command that runs everything
```

Intermediate and raw data files are **not** included in this repository (the
largest raw sources run to several hundred megabytes and are best obtained
directly from the issuing agencies; see `DATA.md`).

## Running the pipeline

Every stage of the analysis, from the raw data to every figure and table in
the paper, runs with one command from the project root:

```bash
python3 code/run_pipeline.py
```

It checks the seven raw sources are in place (failing with a specific,
actionable message if not), creates `data/`, `paper/figs/` and
`paper/tables/` if needed, converts the Globalbilanz PDF to text, runs all
21 stages in dependency order, and ends with a manifest of every file
produced — checked against the exact set the paper's figures and tables
require. A full run takes about three minutes. See `SETUP.md` for the local
folder layout it expects.

Every one of the 21 scripts also carries its own docstring stating exactly
what it reads, what it writes, and which table, figure or number in the
paper it feeds — open any `code/NN_*.py` file to see that provenance
directly; `run_pipeline.py` runs them in the order below.

| Stage | Script | Produces |
|---|---|---|
| 01 | `01_build_multiplier_panel.py` | the core multiplier panel (all later stages depend on this) |
| 02 | `02_load_ffa_financial_panel.py` | municipal financial statistics (accounts × function × year) |
| 03 | `03_build_federal_tax_panel.py` | federal direct-tax panel (fiscal-capacity proxy) |
| 04 | `04_detect_municipal_mergers.py` | merger cross-check against the multiplier panel |
| 05 | `05_parse_municipality_register.py` | the historised municipality register (eCH-0071) |
| 06 | `06_build_geography_and_events.py` | adjacency, the stable 1,916-municipality sample, the 45 canton events |
| 07 | `07_estimate_distributed_lag.py` | the main distributed-lag design → **Table 3** |
| 08 | `08_estimate_cross_border_design.py` | the cross-border design → **Table 4** |
| 09 | `09_permutation_inference.py` | permutation p-values; the FFA-by-canton panel |
| 10 | `10_luzern_ffa_outcomes.py` | Luzern's financial outcomes from the FFA panel |
| 11 | `11_figure_table_event_classification.py` | **Table 1, Figure 1**, Appendix Table 8 |
| 12 | `12_figure_swap_event_study.py` | **Table 2, Figure 2** |
| 13 | `13_figure_table_distributed_lag_robustness.py` | **Table 3 (robustness), Table 4, Figure 3** |
| 14 | `14_figure_table_luzern_incidence.py` | **Table 5, Appendix Table 9, Figure 4** |
| 15 | `15_figure_mandate_expiry_heterogeneity.py` | **Figure 5(b)** |
| 16 | `16_parse_globalbilanz.py` | Kanton Luzern's AFR18 ballot-brochure projection, by municipality |
| 17 | `17_figure_who_reversed.py` | **Figure 5(a)**, the "who reversed?" regressions |
| 18 | `18_check_exposure_pretrends.py` | the pre-trend statistic quoted directly in Section 5.4 |
| 19 | `19_load_effective_burden_panel.py` | the effective tax-burden panel (Section 5.5) |
| 20 | `20_table_effective_burden_robustness.py` | **Table 6, Table 7** |
| 21 | `21_check_burden_mechanism.py` | the mechanism check quoted in Table 7 / Section 5.5 |

There is no other script in this repository: an earlier, broader working
set included exploratory and superseded specifications (an early
single-canton pre-trend diagnostic, an early heterogeneity probe, an
unused labour-market-region classification, an FFA-outcome regression that
fails pre-trend tests, and a tax-burden series later superseded by a
different ESTV export). None of them feed a number in the final paper, so
none of them are included here.

## Environment

Python 3.10+ (built and verified on 3.12), with `pandas`, `numpy`,
`statsmodels`, `pyfixest`, `geopandas`, `pyogrio`, `shapely`, `scipy`, and
`matplotlib` (see `requirements.txt`). The paper itself is a standard LaTeX
document (`natbib`, `booktabs`, `longtable`, `pdflscape`, `placeins`,
`threeparttable`).

## Data availability

See `DATA.md` for the seven primary sources (all public Swiss federal,
cantonal and municipal statistics), their exact vintage, and the local path
each script expects. No proprietary or restricted-access data is used.

## Citation

If you refer to this work, please cite it as:

> Zimmermann, E. D. (2026). *Offsetting by Mandate, Not by Choice: Tax-Point
> Swaps and Vertical Fiscal Interaction among Swiss Municipalities.* Working
> paper.

## Contact

Eduardo Dietrich Zimmermann.
