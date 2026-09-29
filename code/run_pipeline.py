#!/usr/bin/env python3
"""
run_pipeline.py — single-command, end-to-end replication pipeline for
"Offsetting by Mandate, Not by Choice: Tax-Point Swaps and Vertical Fiscal
Interaction among Swiss Municipalities" (Eduardo Dietrich Zimmermann, 2026).

Run from the project root (the folder that directly contains `code/`,
`paper/`, and the seven raw-data folders documented in DATA.md):

    python3 code/run_pipeline.py

What it does, in order:
  1. Checks the seven raw-data sources are present (see DATA.md) and fails
     fast with a specific, actionable message if any is missing.
  2. Creates data/, paper/figs/, paper/tables/ if they do not exist.
  3. Converts the Globalbilanz PDF to text with `pdftotext -raw`, if that
     has not already been done.
  4. Runs each of the 21 numbered stage scripts in dependency order via a
     subprocess, streaming its output live and checking its exit code.
     Stops immediately, with the full traceback, on the first failure.
  5. Prints a final manifest of every pickle, figure and table produced,
     so the whole run can be verified from one screenful of output.

Every stage script also carries its own docstring stating exactly what it
reads, what it writes, and which table, figure or number in the paper it
feeds — open any `code/NN_*.py` file to see that provenance directly.
"""
import subprocess, sys, shutil, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODE = ROOT / "code"

STAGES = [
    "01_build_multiplier_panel.py",
    "02_load_ffa_financial_panel.py",
    "03_build_federal_tax_panel.py",
    "04_detect_municipal_mergers.py",
    "05_parse_municipality_register.py",
    "06_build_geography_and_events.py",
    "07_estimate_distributed_lag.py",
    "08_estimate_cross_border_design.py",
    "09_permutation_inference.py",
    "10_luzern_ffa_outcomes.py",
    "11_figure_table_event_classification.py",
    "12_figure_swap_event_study.py",
    "13_figure_table_distributed_lag_robustness.py",
    "14_figure_table_luzern_incidence.py",
    "15_figure_mandate_expiry_heterogeneity.py",
    "16_parse_globalbilanz.py",
    "17_figure_who_reversed.py",
    "18_check_exposure_pretrends.py",
    "19_load_effective_burden_panel.py",
    "20_table_effective_burden_robustness.py",
    "21_check_burden_mechanism.py",
]

# (raw path relative to ROOT, human-readable source label, is-a-directory-glob)
RAW_CHECKS = [
    ("Tax_Multipliers/estv_income_rates_2010.xlsx", "Source 1 — ESTV multipliers (DATA.md)"),
    ("FTA", "Source 2 — ESTV federal direct tax by municipality (DATA.md)"),
    ("ffa/fs_gdn/gdn_ab_5000.csv", "Source 3 — FFA municipal financial statistics (DATA.md)"),
    ("hgv", "Source 4 — BFS historised municipality register (DATA.md)"),
    ("geo/swissBOUNDARIES3D_1_5_LV95_LN02.gpkg", "Source 5 — swissBOUNDARIES3D (DATA.md)"),
    ("estv/geo_2010.xlsx", "Source 7 — ESTV effective tax burden (DATA.md)"),
]


def fail(msg):
    print(f"\n✗ {msg}", file=sys.stderr)
    sys.exit(1)


def check_raw_data():
    print("Checking raw data sources against DATA.md ...")
    missing = []
    for rel, label in RAW_CHECKS:
        if not (ROOT / rel).exists():
            missing.append(f"  - {label}: expected {rel}")
    gb_txt = ROOT / "gb" / "gb_raw.txt"
    gb_pdf = ROOT / "gb" / "Globalbilanz_1.pdf"
    if not gb_txt.exists() and not gb_pdf.exists():
        missing.append(
            "  - Source 6 — Kanton Luzern Globalbilanz 1 (DATA.md): "
            "expected gb/Globalbilanz_1.pdf (or an already-converted gb/gb_raw.txt)"
        )
    if missing:
        fail(
            "Missing raw data — see SETUP.md for the folder layout and "
            "DATA.md for where to download each source:\n" + "\n".join(missing)
        )
    print("  ✓ all seven sources found\n")


def ensure_output_dirs():
    for d in ["data", "paper/figs", "paper/tables"]:
        (ROOT / d).mkdir(parents=True, exist_ok=True)
    print("✓ data/, paper/figs/, paper/tables/ ready\n")


def ensure_globalbilanz_text():
    txt = ROOT / "gb" / "gb_raw.txt"
    pdf = ROOT / "gb" / "Globalbilanz_1.pdf"
    if txt.exists():
        print("✓ gb/gb_raw.txt already present\n")
        return
    if shutil.which("pdftotext") is None:
        fail(
            "gb/gb_raw.txt is missing and `pdftotext` is not on PATH. "
            "Install poppler (see SETUP.md step 4), then re-run."
        )
    print("Converting Globalbilanz_1.pdf to text (pdftotext -raw) ...")
    r = subprocess.run(["pdftotext", "-raw", str(pdf), str(txt)])
    if r.returncode != 0 or not txt.exists():
        fail("pdftotext conversion failed — check gb/Globalbilanz_1.pdf exists and is readable.")
    print("  ✓ gb/gb_raw.txt created\n")


def run_stages():
    t_start = time.time()
    for i, stage in enumerate(STAGES, 1):
        script = CODE / stage
        if not script.exists():
            fail(f"Stage script not found: {script}")
        print(f"[{i:02d}/{len(STAGES)}] {stage}")
        print("-" * 70)
        t0 = time.time()
        result = subprocess.run([sys.executable, str(script)], cwd=str(ROOT))
        dt = time.time() - t0
        if result.returncode != 0:
            fail(
                f"Stage {i:02d} ({stage}) failed with exit code "
                f"{result.returncode} after {dt:.1f}s. Fix the error above "
                f"and re-run — the pipeline stops at the first failure so "
                f"stages are never run on incomplete inputs."
            )
        print(f"  ✓ stage {i:02d} completed in {dt:.1f}s\n")
    print(f"All {len(STAGES)} stages completed in {time.time()-t_start:.1f}s.\n")


def print_manifest():
    print("=" * 70)
    print("FINAL MANIFEST")
    print("=" * 70)
    for d, pattern, label in [
        ("data", "*.pkl", "intermediate data"),
        ("paper/figs", "*.pdf", "figures"),
        ("paper/tables", "*.tex", "tables"),
    ]:
        files = sorted((ROOT / d).glob(pattern))
        print(f"\n{d}/  ({len(files)} {label})")
        for f in files:
            print(f"  {f.name:45s} {f.stat().st_size:>10,} bytes")
    print()
    fig_expected = {f"fig{i}_{n}.pdf" for i, n in enumerate(
        ["events", "swap_es", "dl", "lu", "rebound", "exposure"], start=1)}
    tab_expected = {"events.tex", "robust_offset.tex", "spatial.tex", "lu.tex",
                     "lu_full.tex", "burden_es.tex", "burden_dl.tex"}
    figs_got = {f.name for f in (ROOT / "paper/figs").glob("*.pdf")}
    tabs_got = {f.name for f in (ROOT / "paper/tables").glob("*.tex")}
    missing_figs = fig_expected - figs_got
    missing_tabs = tab_expected - tabs_got
    if missing_figs or missing_tabs:
        print("⚠ Expected outputs not found:")
        for f in sorted(missing_figs):
            print(f"  missing figure: paper/figs/{f}")
        for t in sorted(missing_tabs):
            print(f"  missing table:  paper/tables/{t}")
    else:
        print("✓ All 6 expected figures and 7 expected table fragments are present.")
        print("  (paper/main.tex \\input's 6 of the 7 tables directly; burden_dl.tex")
        print("   is reproduced as a hand-typed table in the paper text for formatting —")
        print("   compare its numbers against Table 7 in the compiled PDF.)")


if __name__ == "__main__":
    print("Tax-point swaps pipeline — 21 stages\n" + "=" * 70 + "\n")
    check_raw_data()
    ensure_output_dirs()
    ensure_globalbilanz_text()
    run_stages()
    print_manifest()
