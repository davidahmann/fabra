# Troubleshooting Guide

Common issues and how to fix them.

## Point-in-Time Correctness

### "KeyError: timestamp" or "Column timestamp not found"
**Cause:** Meridian's `get_training_data` requires a `timestamp` column in your entity DataFrame to perform point-in-time joins.
**Fix:**
```python
entity_df["timestamp"] = pd.to_datetime("now")
```

### "No matching features found"
**Cause:** Your entity timestamps might be *older* than your feature timestamps. Meridian uses `ASOF JOIN ... WHERE entity.ts >= feature.ts`. If your features are from today but your entities are from yesterday, you get nothing (to prevent data leakage).
**Fix:** Ensure your feature data covers the time range of your training labels.

## Production (Async/Postgres)

### "RuntimeError: Event loop is closed"
**Cause:** You might be trying to run `FeatureStore` methods (which are `async`) in a synchronous context without `asyncio.run()`, or mixing sync/async incorrectly.
**Fix:**
```python
import asyncio
async def main():
    await store.initialize()

if __name__ == "__main__":
    asyncio.run(main())
```

### "UndefinedTableError: relation ... does not exist"
**Cause:** In Hybrid Mode, if you define `@feature(sql="SELECT * FROM my_table")`, Meridian expects `my_table` to exist in Postgres.
**Fix:** Ensure the table exists in your offline store. Meridian does not create raw data tables for you.

## Redis

### "ConnectionError: Connection refused"
**Cause:** Redis is not running or the URL is wrong.
**Fix:** Check `MERIDIAN_REDIS_URL`. Default is `redis://localhost:6379`.
