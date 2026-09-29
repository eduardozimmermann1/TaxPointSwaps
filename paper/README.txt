Offsetting by Mandate, Not by Choice
Tax-Point Swaps and Vertical Fiscal Interaction among Swiss Municipalities
Eduardo Dietrich Zimmermann — September 2026

CONTENTS
  main.tex          paper source (LaTeX, natbib author-year citations)
  references.bib    BibTeX database (19 entries, all independently verified)
  figs/              6 PDF figures (fig1_events ... fig6_exposure)
  tables/            6 table fragments \input by main.tex, incl. lu_full.tex
                     (landscape appendix version of Table 5 with 95% CIs)

COMPILING
  Overleaf: upload this folder (or the zip) as a new project and press
  Recompile — Overleaf detects \bibliography{references} and runs the
  pdflatex -> bibtex -> pdflatex -> pdflatex sequence automatically.

  Command line:
      pdflatex main
      bibtex main
      pdflatex main
      pdflatex main
  (or: latexmk -pdf main)

  Packages used: amsmath, amssymb, booktabs, longtable, array, graphicx,
  pdflscape, placeins, caption, xcolor, hyperref, natbib (plainnat.bst) —
  all in any standard TeX Live / MiKTeX distribution.

VERSION
  23 pages. No table or figure exceeds the page margins; the appendix
  landscape table (Table 9) carries the full Luzern results with 95%
  confidence intervals. Last verified with a clean pdflatex+bibtex+
  pdflatex+pdflatex run from an empty directory (zero errors, zero
  overfull \hbox warnings) on 28 September 2026.
