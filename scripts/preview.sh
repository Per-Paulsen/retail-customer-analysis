#!/usr/bin/env bash
# Local preview helper — sets PATH/env, then runs quarto preview.
# Usage:
#   ./scripts/preview.sh              # preview the whole project
#   ./scripts/preview.sh 04-clv-bgnbd.qmd   # single chapter
set -e
export PATH="/c/Program Files/Quarto/bin:/c/Program Files/R/R-4.6.0/bin:$PATH"
export RETICULATE_PYTHON="C:/Python314/python.exe"
exec quarto preview "$@"
