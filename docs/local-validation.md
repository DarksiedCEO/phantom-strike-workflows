# Local Validation: PhantomStrike decision handoff

## Purpose
Validate the proven local chain end-to-end:
- core
- Temporal dev
- workflows worker
- direct contract smoke
- workflows-to-core smoke

## Prerequisites
- core repo present at `/Users/andrelove/RustroverProjects/phantom-strike-core`
- workflows repo present at `/Users/andrelove/PycharmProjects/phantom-strike-workflows`
- `.env` created from `.env.example` in both repos
- Rust toolchain installed
- Python 3.11 env available for workflows at `/Users/andrelove/PycharmProjects/phantom-strike-workflows/.venv311`
- Temporal dev server available

## Startup Order

### 1. Start core
```bash
cd /Users/andrelove/RustroverProjects/phantom-strike-core
cargo run
```

Expected:
- core starts successfully
- service listens on `127.0.0.1:3100`

### 2. Start Temporal dev server
```bash
temporal server start-dev
```

Expected:
- Temporal dev server starts successfully
- default namespace is available on `localhost:7233`

### 3. Start workflows worker
```bash
cd /Users/andrelove/PycharmProjects/phantom-strike-workflows
cp .env.example .env   # first time only
/Users/andrelove/PycharmProjects/phantom-strike-workflows/.venv311/bin/python run_worker.py
```

Expected:
- worker boot log prints `core_base_url`
- worker boot log prints task queue
- worker begins polling successfully

### 4. Run core contract smoke
```bash
cd /Users/andrelove/RustroverProjects/phantom-strike-core
python3 -m scripts.smoke_contract_decision_submit
```

Pass signals:
- valid flat payload returns `200`
- invalid nested payload returns `400`
- response preserves `trace_id`
- response preserves `correlation_id`

### 5. Run workflows-to-core smoke
```bash
cd /Users/andrelove/PycharmProjects/phantom-strike-workflows
/Users/andrelove/PycharmProjects/phantom-strike-workflows/.venv311/bin/python -m scripts.smoke_workflow_core_handoff
```

Pass signals:
- workflow starts
- workflow completes
- worker posts to core successfully
- core accepts flat decision payload
- `trace_id` preserved end-to-end
- `correlation_id` preserved end-to-end

## One-command smoke wrapper
After core, Temporal dev, and the workflows worker are already running:

```bash
cd /Users/andrelove/PycharmProjects/phantom-strike-workflows
./scripts/run_local_validation.sh
```

## Minimal troubleshooting

### Port `3100` already in use
- stop the other process using port `3100`
- restart core and confirm it binds to `127.0.0.1:3100`

### Temporal connection failure
- confirm `temporal server start-dev` is running
- confirm workflows `.env` still points to `localhost:7233`

### `CORE_BASE_URL` missing or wrong
- confirm `.env` exists in both repos
- confirm workflows worker boot log shows `http://127.0.0.1:3100`

### Wrong task queue
- confirm workflows worker boot log shows `phantom-strike-signal-validation`
- confirm the same queue is set in workflows `.env`

### Stale local service state
- restart core first
- restart Temporal dev second
- restart workflows worker third
- rerun both smoke commands

## Overall pass
Local validation passes only if both smoke scripts pass against the live local stack after core, Temporal, and the workflows worker are started from canonical config.
GitHub Actions should be treated as the required enforcement path for this same lane on `main`.
