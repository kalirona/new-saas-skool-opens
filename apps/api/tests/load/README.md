# Load Testing Scenarios

Uses [k6](https://k6.io) — install: `winget install k6` or `brew install k6`

## Scenarios

| Scenario | VUs | Duration | Targets |
|----------|-----|----------|---------|
| Light    | 10  | 8m       | avg <200ms, p95 <500ms |
| Medium   | 100 | 15m      | avg <500ms, p95 <1500ms |
| High     | 1K  | 23m      | avg <1s, p95 <3s |
| Stress   | 10K | 25m      | avg <2s, p95 <5s |

## Run

```bash
# Light load (single scenario)
k6 run --env BASE_URL=http://localhost:1338 tests/load/scenarios.js

# With admin token for authenticated endpoints
k6 run --env BASE_URL=http://localhost:1338 --env ADMIN_TOKEN=xxx tests/load/scenarios.js

# JSON output for analysis
k6 run --out json=results.json tests/load/scenarios.js

# HTML report
k6 run --out html=report.html tests/load/scenarios.js

# Run all scenarios sequentially
# (edit scenarios.js to uncomment the multi-scenario block)
```

## Monitoring While Testing

In a separate terminal:

```bash
# Watch DB connections
watch -n 2 "psql \$DATABASE_URL -c \"SELECT count(*) FROM pg_stat_activity;\""

# Watch Redis
redis-cli INFO stats

# Watch system resources (Linux)
htop

# Watch application logs
tail -f logs/learnhouse.log
```

## Metrics Collected

- `api_latency_ms` — per-request latency
- `errors` — error rate
- `http_req_duration` — built-in k6 metric
- `http_req_failed` — failure rate

## Interpreting Results

- **avg < 200ms**: Healthy
- **avg 200-500ms**: Acceptable
- **avg 500ms-1s**: Needs investigation
- **avg > 1s**: Critical — optimize before production deployment
- **error rate > 1%**: Investigate immediately
