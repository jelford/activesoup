#! /usr/bin/env bash
set -euo pipefail
poetry run bump2version "$@"
