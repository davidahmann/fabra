---
title: "Deploying Meridian: From Local Laptop to Production API | One-Command Deploy"
description: "Guide to deploying Meridian. Move from DuckDB/In-Memory on your laptop to Postgres/Redis in production with zero code changes. One-command deploy to Fly.io, Cloud Run, and more."
keywords: deploy feature store, meridian production, postgres redis feature store, mlops deployment, fly.io deploy, cloud run deploy, ecs deploy, railway deploy
---

# From Laptop to Production in 3 Steps

## At a Glance

| Environment | Offline Store | Online Cache | Deploy Command |
|:---|:---|:---|:---|
| Development | DuckDB (embedded) | In-memory | `meridian serve` |
| Production | Postgres | Redis | `MERIDIAN_ENV=production` |
| Local Prod | Postgres (Docker) | Redis (Docker) | `meridian setup && docker compose up` |
| Cloud | Postgres (managed) | Redis (managed) | `meridian deploy fly\|cloudrun\|ecs` |

## Step 1: Local Development (Day 1)

Your laptop is your feature store:

```python
# features.py - works locally, no setup
store = FeatureStore()  # DuckDB + In-Memory

@feature(entity=User, refresh="5m", materialize=True)
def fraud_score(user_id: str) -> float:
    # In reality, this would query your data warehouse
    return 0.85
```

Test in Jupyter. Iterate fast. Zero infrastructure.

## Step 2: Single-Server Production (Week 2)

Same code, just set environment variables:

```bash
export MERIDIAN_ENV=production
export MERIDIAN_POSTGRES_URL="postgresql+asyncpg://prod-db/features"
export MERIDIAN_REDIS_URL="redis://prod-cache:6379"
```

And initialize the store without arguments:

```python
# features.py
store = FeatureStore()  # Auto-detects Prod
```

Infrastructure needed:

- AWS RDS Postgres ($50/month)
- AWS ElastiCache Redis ($30/month)
- Deploy API to Heroku/Railway ($20/month)

**Total cost:** $100/month
**Setup time:** 1 hour

## Step 3: Horizontal Scale (Month 3)

No code changes. Just deploy more API pods.

Infrastructure:

- Same Postgres (vertically scale if needed)
- Redis cluster mode ($200/month)
- 3-5 API pods behind load balancer

**Total cost:** $500/month
**Setup time:** 2 hours

## Step 4: Local Production (Docker Compose)

For a proven production stack (Postgres + pgvector + Redis), just run:

```bash
meridian setup
docker compose up -d
```

> [!WARNING]
> **Postgres Requirement:**
> Standard Postgres images (`postgres:16`) **will not work** for Vector Search. You must use `pgvector/pgvector:pg16` or install the extension manually. `meridian setup` handles this for you.

This stack mimics a real production environment and is perfect for integration testing.

## Step 5: One-Command Cloud Deploy (New in v1.3.0)

Deploy to any major cloud platform with a single command. Meridian generates all the deployment configs you need.

### Fly.io

```bash
meridian deploy fly --name my-feature-store
# Generates: Dockerfile, fly.toml, requirements.txt
# Then: fly deploy
```

### Google Cloud Run

```bash
meridian deploy cloudrun --name my-feature-store --project my-gcp-project
# Generates: Dockerfile, cloudbuild.yaml, service.yaml
# Then: gcloud run deploy
```

### AWS ECS

```bash
meridian deploy ecs --name my-feature-store --cluster my-cluster
# Generates: Dockerfile, task-definition.json, ecs-params.yml
# Then: ecs-cli compose up
```

### Railway

```bash
meridian deploy railway --name my-feature-store
# Generates: Dockerfile, railway.json
# Then: railway up
```

### Render

```bash
meridian deploy render --name my-feature-store
# Generates: Dockerfile, render.yaml
# Then: git push (auto-deploys)
```

### Options

| Flag | Description | Default |
| :--- | :--- | :--- |
| `--name` | Service name | `meridian-app` |
| `--port` | Port to expose | `8000` |
| `--dry-run` | Preview files without writing | `false` |
| `--verbose` | Show detailed output | `false` |

### Preview Mode

Use `--dry-run` to see what would be generated without writing files:

```bash
meridian deploy fly --name my-app --dry-run
```

## FAQ

**Q: How do I deploy Meridian to production?**
A: Set `MERIDIAN_ENV=production` and configure `MERIDIAN_POSTGRES_URL` and `MERIDIAN_REDIS_URL`. Same code works locally and in production—zero changes required.

**Q: What infrastructure do I need for production?**
A: Postgres (for offline store), Redis (for online cache), and any app host. Total cost starts at ~$100/month on managed services.

**Q: How do I deploy to Fly.io?**
A: Run `meridian deploy fly --name my-app`. This generates Dockerfile and fly.toml, then run `fly deploy`.

**Q: Can I run a production stack locally?**
A: Yes. Run `meridian setup` to generate docker-compose.yml with Postgres (pgvector) and Redis. Then `docker compose up -d`.

**Q: What's the difference between development and production mode?**
A: Development uses DuckDB (file-based) and in-memory cache. Production uses Postgres and Redis for durability and horizontal scale.

**Q: How do I scale horizontally?**
A: Deploy multiple API pods behind a load balancer. No code changes needed—Postgres and Redis handle shared state.

---

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "Deploy Meridian Feature Store to Production",
  "description": "Step-by-step guide to deploying Meridian from local development to production on Fly.io, Cloud Run, AWS ECS, Railway, or Render.",
  "totalTime": "PT1H",
  "step": [{
    "@type": "HowToStep",
    "name": "Local Development",
    "text": "Start with pip install and DuckDB for zero-infrastructure local development."
  }, {
    "@type": "HowToStep",
    "name": "Set Production Environment",
    "text": "Set MERIDIAN_ENV=production and configure Postgres/Redis URLs."
  }, {
    "@type": "HowToStep",
    "name": "Deploy to Cloud",
    "text": "Use 'meridian deploy' command to generate deployment configs for your platform."
  }]
}
</script>
