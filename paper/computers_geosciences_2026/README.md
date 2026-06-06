# Computers & Geosciences submission materials

This directory contains the manuscript materials corresponding to the current
Computers & Geosciences submission.

## Contents

- `01_manuscript_computers_geosciences.pdf` — main manuscript.
- `02_supplementary_material.pdf` — supplementary material.
- `latex_source/` — LaTeX source files and source result tables used to build
  the manuscript and supplement.
- `latex_source_computers_geosciences.zip` — zip archive of the same anonymous
  LaTeX source package.

The cover letter is intentionally excluded from this reproduction repository
because it is submission correspondence rather than a reproducibility artefact.

## Key source tables

- `latex_source/gemini35_three_factor_n5_majority_summary.csv` — balanced
  `gemini-3.5-flash` A/B/C N=5 majority-vote diagnostic.
- `latex_source/gemma4_host228_scale_sweep_summary.csv` — fixed-host Gemma4
  deployment sweep summary.
- `latex_source/host228_ollama_model_metadata.csv` — local Ollama host metadata.
- `latex_source/floodsql_external_smoke_summary.csv` — FloodSQL-Bench smoke
  audit summary.

## Compile

From `latex_source/`:

```powershell
D:\texlive\2026\bin\windows\xelatex.exe -interaction=nonstopmode 01_manuscript_computers_geosciences.tex
D:\texlive\2026\bin\windows\bibtex.exe 01_manuscript_computers_geosciences
D:\texlive\2026\bin\windows\xelatex.exe -interaction=nonstopmode 01_manuscript_computers_geosciences.tex
D:\texlive\2026\bin\windows\xelatex.exe -interaction=nonstopmode 01_manuscript_computers_geosciences.tex
D:\texlive\2026\bin\windows\xelatex.exe -interaction=nonstopmode 03_supplement_v7_codex.tex
```
