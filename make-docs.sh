#!/usr/bin/env bash
set -euo pipefail
set LFS=$'\t\n'

PROJECTROOT=$(git rev-parse --show-toplevel)
DOCSROOT="${PROJECTROOT}/docs"

poetry export --dev --format requirements.txt > docs/requirements.txt

cd $DOCSROOT
rm -rf "${DOCSROOT}/source"

make clean

export SPHINX_APIDOC_OPTIONS="members,no-undoc-members,show-inheritance"
sphinx-apidoc -o "${DOCSROOT}/source" --module-first "${PROJECTROOT}/src/activesoup" \
    "${PROJECTROOT}/src/activesoup/driver.py"  # public objects are re-exported from __init__.py

make html
