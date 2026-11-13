#!/usr/bin/env bash
set -euo pipefail
paper_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd -- "$paper_dir"
mkdir -p build
if command -v pdflatex >/dev/null 2>&1; then
  pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
  pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
elif [ -x tools/tectonic ]; then
  tools/tectonic --keep-logs --outdir build main.tex
elif command -v tectonic >/dev/null 2>&1; then
  tectonic --keep-logs --outdir build main.tex
else
  printf '%s\n' 'Build blocked: install a standard TeX distribution with IEEEtran, or provide tectonic. Source and IEEEtran.cls are included.' >&2
  exit 1
fi
