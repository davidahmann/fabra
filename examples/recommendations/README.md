# Product Recommendations Example

This example demonstrates building a **personalized recommendation engine** using Meridian's feature store.

## Use Case

An e-commerce platform needs to recommend products to users. The system must:
- Personalize based on user behavior (browsing history, purchase patterns)
- Consider product signals (popularity, ratings, inventory)
- Apply business rules (don't show out-of-stock items)
- Serve recommendations in <50ms at scale

## Features Defined

### User Features
| Feature | Description | Refresh |
|---------|-------------|---------|
| `user_browsing_category` | Most viewed category (last hour) | 5 min |
| `user_purchase_count_30d` | Purchases in last 30 days | 1 hour |
| `user_avg_order_value` | Average order value | 24 hours |
| `user_price_sensitivity` | Price segment (low/medium/high) | 30 min |

### Product Features
| Feature | Description | Refresh |
|---------|-------------|---------|
| `product_popularity_score` | Composite popularity (0-100) | 1 hour |
| `product_inventory_level` | Stock status | 6 hours |
| `product_rating` | Average rating (1-5 stars) | 24 hours |

## Running the Example

```bash
# From the repository root
cd examples/recommendations

# Run the demo
python main.py

# Or serve features via API
meridian serve recommendation_features.py --port 8000
```

## API Usage

Once served, fetch features for scoring:

```bash
# Get user features
curl "http://localhost:8000/features/User/user_001?features=user_browsing_category,user_purchase_count_30d"

# Get product features
curl "http://localhost:8000/features/Product/prod_100?features=product_popularity_score,product_rating"
```

## Architecture

```
                    ┌─────────────┐
                    │   Client    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Candidate  │  ANN Search
                    │ Generation  │  (pgvector)
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Scoring   │  User + Product
                    │    Model    │  Features
                    └──────┬──────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
┌───▼───┐            ┌─────▼─────┐          ┌─────▼─────┐
│ User  │            │  Product  │          │ Business  │
│Features│           │ Features  │          │  Rules    │
│(Redis)│            │  (Redis)  │          │           │
└───────┘            └───────────┘          └───────────┘
```

## Production Considerations

1. **Candidate Generation**: Use pgvector to find semantically similar products before scoring
2. **Feature Freshness**: Tune `refresh` intervals based on business needs
3. **Caching**: Enable `materialize=True` for all frequently-accessed features
4. **Monitoring**: Track feature latency and freshness via Meridian metrics

## Next Steps

- Add user embeddings for collaborative filtering
- Implement A/B testing with feature flags
- Add contextual features (time of day, device type)
