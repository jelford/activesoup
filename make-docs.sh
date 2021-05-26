#!/usr/bin/env bash
set -euo pipefail
set LFS=$'\t\n'

PROJECTROOT=$(git rev-parse --show-toplevel)
DOCSROOT="${PROJECTROOT}/docs"

poetry export --dev --format requirements.txt > docs/requirements.txt

cd $DOCSROOT
rm -rf "${DOCSROOT}/source"
sphinx-apidoc -o "${DOCSROOT}/source" --module-first "${PROJECTROOT}/src/activesoup" 
make html
