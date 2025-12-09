"""
Recommendation Engine Features

This example demonstrates how to build a product recommendation system
using Fabra's feature store. Features include:
- User behavioral features (browsing patterns, purchase history)
- Product features (popularity, category embeddings)
- Cross-entity features (user-product affinity scores)
"""

from datetime import timedelta
from fabra.core import FeatureStore, entity, feature
from fabra.store import DuckDBOfflineStore, InMemoryOnlineStore

# Initialize Store
store = FeatureStore(
    offline_store=DuckDBOfflineStore(), online_store=InMemoryOnlineStore()
)


# --- Entities ---


@entity(store)
class User:
    user_id: str


@entity(store)
class Product:
    product_id: str


# --- User Features ---


@feature(entity=User, refresh=timedelta(minutes=5), materialize=True)
def user_browsing_category(user_id: str) -> str:
    """Most viewed product category in the last hour."""
    # In production: aggregate from clickstream data
    categories = ["electronics", "clothing", "home", "sports"]
    return categories[hash(user_id) % len(categories)]


@feature(entity=User, refresh=timedelta(hours=1), materialize=True)
def user_purchase_count_30d(user_id: str) -> int:
    """Number of purchases in the last 30 days."""
    # In production: COUNT(*) from orders WHERE created_at > now() - interval '30 days'
    return (hash(user_id) % 20) + 1


@feature(entity=User, refresh=timedelta(hours=24), materialize=True)
def user_avg_order_value(user_id: str) -> float:
    """Average order value across all purchases."""
    # In production: AVG(total) from orders
    base = 50 + (hash(user_id) % 200)
    return round(base + (hash(user_id + "aov") % 100) / 10, 2)


@feature(entity=User, refresh=timedelta(minutes=30), materialize=True)
def user_price_sensitivity(user_id: str) -> str:
    """Price sensitivity segment: low, medium, high."""
    # In production: ML model output based on coupon usage, cart abandonment, etc.
    segments = ["low", "medium", "high"]
    return segments[hash(user_id + "price") % len(segments)]


# --- Product Features ---


@feature(entity=Product, refresh=timedelta(hours=1), materialize=True)
def product_popularity_score(product_id: str) -> float:
    """Popularity score (0-100) based on views, purchases, and ratings."""
    # In production: composite score from multiple signals
    return round((hash(product_id) % 100) + (hash(product_id + "pop") % 10) / 10, 2)


@feature(entity=Product, refresh=timedelta(hours=6), materialize=True)
def product_inventory_level(product_id: str) -> str:
    """Inventory status: in_stock, low_stock, out_of_stock."""
    # In production: real-time from inventory system
    levels = ["in_stock", "in_stock", "in_stock", "low_stock", "out_of_stock"]
    return levels[hash(product_id + "inv") % len(levels)]


@feature(entity=Product, refresh=timedelta(hours=24), materialize=True)
def product_rating(product_id: str) -> float:
    """Average rating (1-5 stars)."""
    # In production: AVG(rating) from reviews
    base = 3.0 + (hash(product_id) % 20) / 10
    return round(min(5.0, base), 1)


# --- Pre-load demo data ---
if __name__ == "__main__":
    import asyncio

    async def load_demo_data() -> None:
        # Load sample user features
        await store.online_store.set_online_features(
            "User",
            "user_001",
            {
                "user_browsing_category": "electronics",
                "user_purchase_count_30d": 12,
                "user_avg_order_value": 175.50,
                "user_price_sensitivity": "medium",
            },
        )

        await store.online_store.set_online_features(
            "User",
            "user_002",
            {
                "user_browsing_category": "clothing",
                "user_purchase_count_30d": 3,
                "user_avg_order_value": 65.00,
                "user_price_sensitivity": "high",
            },
        )

        # Load sample product features
        products = ["prod_100", "prod_101", "prod_102"]
        for pid in products:
            await store.online_store.set_online_features(
                "Product",
                pid,
                {
                    "product_popularity_score": round(70 + hash(pid) % 30, 2),
                    "product_inventory_level": "in_stock",
                    "product_rating": round(4.0 + (hash(pid) % 10) / 10, 1),
                },
            )

        print("Demo data loaded successfully!")

    asyncio.run(load_demo_data())
