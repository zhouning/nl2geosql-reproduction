# LaTeX Source Manifest

This folder contains the LaTeX sources for the Computers & Geosciences
submission package.

## PDFs and Sources

| PDF in parent folder | Source file(s) |
|---|---|
| `01_manuscript_computers_geosciences.pdf` | `01_manuscript_computers_geosciences.tex` plus the input files listed below |
| `02_supplementary_material.pdf` | `03_supplement_v7_codex.tex` |

The non-anonymous cover letter is intentionally excluded from this reproduction
repository.

## Main Manuscript Dependencies

- `related_work_v7_codex.tex`
- `method_v7_codex.tex`
- `experiments_setup_v7_codex.tex`
- `table_benchmark_profile.tex`
- `baseline_results_v7_codex.tex`
- `gisr_section_codex.tex`
- `references_codex.bib`
- `01_manuscript_computers_geosciences.bbl`

## Source Data and Metadata Tables

- `gemma4_host228_scale_sweep_summary.csv`
- `host228_ollama_model_metadata.csv`
- `floodsql_external_smoke_summary.csv`
- `gemini35_three_factor_n5_majority_summary.csv`

## Compile Main Manuscript

```powershell
D:\texlive\2026\bin\windows\xelatex.exe -interaction=nonstopmode 01_manuscript_computers_geosciences.tex
D:\texlive\2026\bin\windows\bibtex.exe 01_manuscript_computers_geosciences
D:\texlive\2026\bin\windows\xelatex.exe -interaction=nonstopmode 01_manuscript_computers_geosciences.tex
D:\texlive\2026\bin\windows\xelatex.exe -interaction=nonstopmode 01_manuscript_computers_geosciences.tex
```

## Compile Supplement

```powershell
D:\texlive\2026\bin\windows\xelatex.exe -interaction=nonstopmode 03_supplement_v7_codex.tex
```

Build products such as `.aux`, `.log`, `.out`, and `.blg` are intentionally not
included.
