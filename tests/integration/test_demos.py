import pytest

from fabra.demos import demo_context, demo_features


@pytest.mark.asyncio
async def test_demo_context_features():
    """Test feature functions in demo_context."""
    # Deterministic checks based on hash
    uid1 = "user_123"
    # uid2 = "user_456" # Unused

    assert demo_context.user_tier(uid1) in ["premium", "free"]
    assert isinstance(demo_context.user_engagement_score(uid1), float)
    assert demo_context.support_priority(uid1) in ["high", "medium", "normal"]


@pytest.mark.asyncio
async def test_demo_context_search_docs():
    """Test search_docs retriever in demo_context."""
    results = await demo_context.search_docs("features", top_k=2)
    assert len(results) == 2
    assert "Features" in results[0]["content"]
    assert results[0]["source"].startswith("docs/fabra/")


@pytest.mark.asyncio
async def test_demo_context_chat_context():
    """Test chat_context assembly in demo_context."""
    ctx = await demo_context.chat_context("user_123", "how do features work?")

    # Context object returned, check content
    assert "System Prompt" in ctx.content or "helpful AI assistant" in ctx.content
    assert "User Query: how do features work?" in ctx.content
    assert "Relevant Documentation" in ctx.content
    assert ctx.meta["freshness_status"] in ["guaranteed", "unknown"]


@pytest.mark.asyncio
async def test_demo_features_logic():
    """Test feature functions in demo_features."""
    uid = "user_123"

    # Test deterministic features
    tier = demo_features.user_tier(uid)
    assert tier in ["premium", "free"]

    score = demo_features.user_engagement(uid)
    assert 0 <= score <= 100

    count = demo_features.purchase_count(uid)
    assert isinstance(count, int)

    days = demo_features.days_since_signup(uid)
    assert 0 <= days <= 365

    active = demo_features.is_active(uid)
    assert isinstance(active, bool)


@pytest.mark.asyncio
async def test_demo_features_seeding():
    """Test that seeding runs without error."""
    await demo_features._seed_demo_data()

    features = await demo_features.store.online_store.get_online_features(
        "User", "user_123", ["user_tier", "user_engagement"]
    )
    assert features["user_tier"] is not None
    assert features["user_engagement"] is not None
