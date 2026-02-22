#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "${ROOT}/../.." && pwd)"

export PYTHONPATH="${ROOT}"
cd "${REPO_ROOT}"

pytest -q contracts/cost-governor/tests/test_policy_as_code.py
