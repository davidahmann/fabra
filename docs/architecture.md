# Meridian Architecture: Boring Technology, Properly Applied

## Design Philosophy

1. **Redis-Only Caching (No L1)**
   - Most feature stores use in-memory L1 + Redis L2
   - This creates cache coherence bugs (pods see stale values)
   - We use Redis-only: 1ms localhost latency, strong consistency
   - Correctness > micro-optimization for fraud/finance

2. **Randomized Distributed Locking (No Leader Election)**
   - Most systems use consistent hashing or leader election
   - We use randomized work selection + Redis SETNX locks
   - Self-healing, no topology awareness required
   - "Even enough" statistically, brutally simple

3. **Explicit Over Magic**
   - No auto-caching hot features
   - No query optimization
   - User writes `materialize=True`, we cache. That's it.
   - Predictability > cleverness

## The Stack

**Local Mode:**
- **Offline:** DuckDB (embedded SQL engine)
- **Online:** Python dict (in-memory)
- **Scheduler:** APScheduler (background thread)
- **Infrastructure:** None (Just `pip install`)

**Production Mode:**
- **Offline:** Postgres 13+ (or Snowflake/BigQuery)
- **Online:** Redis 6+ (standalone or cluster)
- **Scheduler:** Distributed Workers with Redis Locks
- **Infrastructure:** 1x Postgres, 1x Redis, Nx API Pods

## Point-in-Time Correctness

Training/serving skew is the #1 killer of ML models in production.

**Problem:** Your model trains on Monday's features but serves Tuesday's features.

**Solution:** Meridian's `get_training_data()` uses "as-of" joins:
```sql
SELECT features.*
FROM events e
LEFT JOIN features f ON e.user_id = f.user_id
  AND f.valid_from <= e.timestamp
  AND f.valid_to > e.timestamp
```

Same logic offline (training) and online (serving). Guaranteed consistency.
