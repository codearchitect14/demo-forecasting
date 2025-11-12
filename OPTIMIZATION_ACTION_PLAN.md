### 🔥 Final Optimization Action Plan (Prophet Accuracy + Fast Inference)

#### 🎯 Objectives and SLA
- **Primary goal**: Forecast for 5×5×5 (cities × stores × products) completes in under 10 seconds (p95).
- **User experience**: Fast results in <3s (using cached predictions) with live streaming of refinements if needed.
- **Reliability**: Consistent response time under moderate concurrency.

---

### ⚡ Current Bottlenecks (Original Diagnosis)
- Per-combination DB calls inside nested loops.
- Sequential forecasting (fit per combination).
- Non-vectorized feature engineering (Python loops).
- CPU-bound Prophet training blocking request handling.
- Limited caching of historical data and outputs.

---

### 🏗️ Plan Pillars (Updated With Offline Prophet)

1) Data Access: Bulk Retrieval and Indexing
- Replace per-combo queries with a single set-based SQL query for historical data.
- Batch lookups for city/store/product metadata.
- Add/verify covering index on `sales_data(city_id, store_id, product_id, dt)`.
- Optional: Materialized view (last 180–365 days) with precomputed features; refresh every 10–30 minutes.

2) Feature Engineering: Vectorized / SQL
- Move lags, rolling averages, and seasonal indicators into SQL window functions.
- If in Python → pandas groupby once instead of loops.
- Reduce history to 180–270 days for fast mode (can extend in accuracy mode).

3) Modeling Strategy (Accuracy Kept With Prophet)
- Train Prophet once offline (batch job).
- Parallelize across cores (Ray/Dask/ProcessPoolExecutor).
- Save models (pickle/JSON).
- Prediction mode:
  - Load pre-trained Prophet model at request time.
  - Run `.predict()` (fast, milliseconds).
  - Cache predicted outputs (e.g., next 30–60 days) in Redis/disk for instant responses.
- Optional: Use Prophet + ensemble offline, store final predictions.

✅ No compromise on Prophet accuracy
✅ Fast inference at runtime

4) Concurrency and Compute Offload
- Training: parallelized offline.
- Inference: Prophet `.predict()` is cheap → can run inline.
- Background training via Celery/RQ/Airflow; results stored and served on next request.

5) Caching Layers
- Redis or Disk:
  - Cache pre-trained models keyed by (city, store, product).
  - Cache forecasts (e.g., 7/30/60-day horizons).
- TTL strategy:
  - Models → retrain daily/weekly.
  - Forecasts → cache until next retraining.
- In-process LRU for hot combos.

6) API and Response Shaping
- Add `mode='fast'|'accurate'`.
- Fast mode: Serve cached Prophet predictions (instant).
- Accurate mode: Optionally run Prophet with full history or Prophet+ensemble offline, stream refinements.
- Trim payload: return numeric arrays only, gzip compress.

7) Frontend Adjustments
- Display results immediately from cache.
- Show “retraining in progress” or “updated forecast available” when offline jobs refresh models.
- Add per-stage timing for transparency.

8) Infra Tuning
- Server: uvicorn + uvloop; multiple workers per core.
- DB pool: sized to DB instance; enable keep-alives.
- Compression: gzip/deflate; static assets on CDN.

9) Observability and Guardrails
- Instrument timings: DB fetch, feature build, predict, payload build.
- Track p50/p95 latency.
- Monitor cache hit/miss ratios.
- Add alerts for latency regressions or cache staleness.

---

### Phased Execution Steps

1) Baseline and Targets (0.5 day)
- Add timers; record current p50/p95 for 5×5×5.
- Define success: p95 < 10s, mean 2–4s.

2) Bulk Data Fetch and Names (0.5–1 day)
- Implement set-based historical fetch for all combos.
- Batch name lookups; remove per-combo queries.
- Verify query plans and add/confirm covering index.

3) Feature Engineering Optimization (0.5 day)
- Move lags/rolling to SQL window functions or vectorize with pandas groupby.
- Reduce history window to 180–270 days in fast mode.

4) Offline Prophet + Caching (1–2 days)
- Train Prophet offline across combos; parallelize; persist models.
- Load models at startup; serve `.predict()`; cache horizons (7/30/60 days).

5) Concurrency and CPU Offload (0.5 day)
- Keep event loop free; use process pool for any CPU-bound steps.
- Bound parallelism; tune process/thread counts.

6) Accuracy-mode Background Jobs (1 day)
- Use Celery/RQ/Airflow for retraining and ensemble refinements.
- Stream updates over WebSocket; progressively merge in UI.

7) Infra and Payload (0.5 day)
- Enable gzip; reduce response size; confirm multiple workers; tune DB pool.

8) Validation and Load Testing (0.5–1 day)
- Measure p95 under realistic load; address hotspots.
- Add alerts for latency regressions.

---

### Risks and Mitigations
- **DB pressure from bulk queries**: covering index, limit history, bound concurrency.
- **CPU contention**: isolate CPU work in processes; cap concurrency; profile.
- **Cache staleness**: short TTLs; invalidate on data refresh.
- **Model drift**: schedule retraining; monitor accuracy.

---

### Success Criteria
- 5×5×5: **p95 < 10s**, typical 2–4s.
- Initial results in **<3s** from cache; refinements streamed when available.
- Under moderate concurrency, p95 remains **<10s**.


