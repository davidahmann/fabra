"""
Recommendation Engine - Main Application

Demonstrates a recommendation API that uses Fabra features
to personalize product recommendations for users.
"""

import asyncio
from recommendation_features import store


async def get_user_recommendations(
    user_id: str, candidate_products: list[str]
) -> list[dict]:
    """
    Score and rank products for a user based on their features.

    In production, you might:
    1. Get candidate products from a retrieval model (ANN search)
    2. Score each candidate using user + product features
    3. Apply business rules (inventory, geo restrictions)
    4. Return top-K ranked products
    """
    # 1. Fetch user features
    user_features = await store.get_online_features(
        "User",
        user_id,
        [
            "user_browsing_category",
            "user_purchase_count_30d",
            "user_avg_order_value",
            "user_price_sensitivity",
        ],
    )

    print(f"\nUser Features for {user_id}:")
    for k, v in user_features.items():
        print(f"  {k}: {v}")

    # 2. Fetch product features and score each
    scored_products = []

    for product_id in candidate_products:
        product_features = await store.get_online_features(
            "Product",
            product_id,
            ["product_popularity_score", "product_inventory_level", "product_rating"],
        )

        # Simple scoring function (in production: ML model)
        score = compute_recommendation_score(user_features, product_features)

        scored_products.append(
            {
                "product_id": product_id,
                "score": score,
                "popularity": product_features.get("product_popularity_score"),
                "rating": product_features.get("product_rating"),
                "inventory": product_features.get("product_inventory_level"),
            }
        )

    # 3. Sort by score (descending) and apply inventory filter
    ranked = sorted(scored_products, key=lambda x: x["score"], reverse=True)
    available = [p for p in ranked if p["inventory"] != "out_of_stock"]

    return available


def compute_recommendation_score(user_features: dict, product_features: dict) -> float:
    """
    Compute a recommendation score based on user and product features.

    In production, this would be an ML model (e.g., Two-Tower, xgboost ranker).
    This is a simplified heuristic for demonstration.
    """
    score = 0.0

    # Base score from product popularity and rating
    popularity = product_features.get("product_popularity_score", 50)
    rating = product_features.get("product_rating", 3.0)
    score += (popularity / 100) * 40  # 0-40 points from popularity
    score += (rating / 5.0) * 30  # 0-30 points from rating

    # Boost for active users
    purchase_count = user_features.get("user_purchase_count_30d", 0)
    if purchase_count > 10:
        score += 10  # Loyal customer boost

    # Price sensitivity adjustment
    sensitivity = user_features.get("user_price_sensitivity", "medium")
    if sensitivity == "high":
        score -= 5  # Lower score for price-sensitive users (they need deals)
    elif sensitivity == "low":
        score += 5  # Higher score for price-insensitive users

    return round(score, 2)


async def main() -> None:
    print("=" * 60)
    print("Fabra Recommendation Engine Demo")
    print("=" * 60)

    # First, load demo data
    from recommendation_features import store as feature_store

    # Manually set some feature values for demo
    await feature_store.online_store.set_online_features(
        "User",
        "user_001",
        {
            "user_browsing_category": "electronics",
            "user_purchase_count_30d": 15,
            "user_avg_order_value": 175.50,
            "user_price_sensitivity": "low",
        },
    )

    await feature_store.online_store.set_online_features(
        "User",
        "user_002",
        {
            "user_browsing_category": "clothing",
            "user_purchase_count_30d": 2,
            "user_avg_order_value": 45.00,
            "user_price_sensitivity": "high",
        },
    )

    # Set product features
    products = [
        ("prod_100", 85.5, "in_stock", 4.5),
        ("prod_101", 72.3, "low_stock", 4.2),
        ("prod_102", 91.0, "in_stock", 4.8),
        ("prod_103", 65.0, "out_of_stock", 3.9),
    ]

    for pid, pop, inv, rating in products:
        await feature_store.online_store.set_online_features(
            "Product",
            pid,
            {
                "product_popularity_score": pop,
                "product_inventory_level": inv,
                "product_rating": rating,
            },
        )

    # Get recommendations for two different users
    candidate_products = ["prod_100", "prod_101", "prod_102", "prod_103"]

    print("\n" + "-" * 60)
    print("Recommendations for user_001 (Loyal, Price Insensitive)")
    print("-" * 60)

    recs_1 = await get_user_recommendations("user_001", candidate_products)

    print("\nTop Recommendations:")
    for i, rec in enumerate(recs_1[:3], 1):
        print(
            f"  {i}. {rec['product_id']} (score: {rec['score']}, rating: {rec['rating']})"
        )

    print("\n" + "-" * 60)
    print("Recommendations for user_002 (New, Price Sensitive)")
    print("-" * 60)

    recs_2 = await get_user_recommendations("user_002", candidate_products)

    print("\nTop Recommendations:")
    for i, rec in enumerate(recs_2[:3], 1):
        print(
            f"  {i}. {rec['product_id']} (score: {rec['score']}, rating: {rec['rating']})"
        )

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
