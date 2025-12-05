# Why Meridian Instead of Feast?

## Feast Requires Infrastructure You Don't Have

Feast documentation Day 1:
- Install Docker Desktop (8GB download)
- Set up Kubernetes cluster (local or cloud)
- Configure feature repository (YAML hell)
- Debug registry sync issues
- Still haven't served a single feature

Meridian Day 1:
```bash
pip install "meridian-oss[ui]"
python examples/quickstart.py
```

## The Philosophy Difference

| Feature | Feast | Meridian |
| :--- | :--- | :--- |
| **Philosophy** | Enterprise-first, infrastructure-heavy | Developer-first, local-first |
| **Config** | YAML | Python Code |
| **Maintenance** | Requires Platform Team | One ML Engineer |
| **Target Scale** | "Google-scale" | "Series B SaaS" |

## When You Actually Need Feast

You probably don't. But if you have:
- 500+ ML engineers
- Dedicated platform team
- Existing Kubernetes infrastructure
- $500K/year budget for tooling

Then Feast might make sense. For everyone else: Meridian.

## FAQ

**Q: Is Meridian production-ready?**
A: Yes. Uses Postgres + Redis in production - same boring tech running 90% of the internet. No exotic dependencies.

**Q: Can Meridian handle real-time features?**
A: Yes. Sub-5ms latency for cached features (Redis). For streaming: materialize from Kafka/Flink to Postgres, Meridian queries the table.

**Q: What's missing vs Feast?**
A: Streaming ingestion (use Flink), complex feature DAGs (use dbt), enterprise RBAC (Phase 2). If you need these now, you're not our target user.
