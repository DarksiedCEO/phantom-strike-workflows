#!/usr/bin/env bash
set -euo pipefail

CORE_REPO="/Users/andrelove/RustroverProjects/phantom-strike-core"
WORKFLOWS_REPO="/Users/andrelove/PycharmProjects/phantom-strike-workflows"
WORKFLOWS_PYTHON="/Users/andrelove/PycharmProjects/phantom-strike-workflows/.venv311/bin/python"

echo "Running local validation smoke checks"
echo "Assumes core, Temporal dev, and workflows worker are already running"

if [[ ! -f "$CORE_REPO/.env" ]]; then
  echo "LOCAL VALIDATION FAIL: missing core .env at $CORE_REPO/.env"
  exit 1
fi

if [[ ! -f "$WORKFLOWS_REPO/.env" ]]; then
  echo "LOCAL VALIDATION FAIL: missing workflows .env at $WORKFLOWS_REPO/.env"
  exit 1
fi

if [[ ! -x "$WORKFLOWS_PYTHON" ]]; then
  echo "LOCAL VALIDATION FAIL: missing workflows python env at $WORKFLOWS_PYTHON"
  exit 1
fi

echo "Step 1/2: direct contract smoke"
(cd "$CORE_REPO" && python3 -m scripts.smoke_contract_decision_submit)

echo "Step 2/2: workflows-to-core smoke"
(cd "$WORKFLOWS_REPO" && "$WORKFLOWS_PYTHON" -m scripts.smoke_workflow_core_handoff)

echo "LOCAL VALIDATION PASS"
