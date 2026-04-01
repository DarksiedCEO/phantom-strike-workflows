# Smoke: workflows -> core decision handoff

Prerequisites
- core running locally
- temporal dev server running
- workflows worker running
- `.env` present

Run
- `python -m scripts.smoke_workflow_core_handoff`

Pass criteria
- workflow starts
- workflow completes
- core accepts decision submission
- `trace_id` and `correlation_id` match end-to-end
