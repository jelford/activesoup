#!/usr/bin/env bash
set -euo pipefail
IFS=$'\t\n'

PROJECTROOT=$(git rev-parse --show-toplevel)
DOCSROOT="${PROJECTROOT}/docs"

poetry export --dev --without-hashes --format requirements.txt > docs/requirements.txt

cd $DOCSROOT

make clean
rm -rf "${DOCSROOT}/source"

export SPHINX_APIDOC_OPTIONS="members,no-undoc-members,show-inheritance"
sphinx-apidoc -o "${DOCSROOT}/source" --ext-intersphinx --module-first "${PROJECTROOT}/src/activesoup"

make html
