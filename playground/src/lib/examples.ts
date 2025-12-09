export interface Example {
  id: string;
  title: string;
  description: string;
  code: string;
  category: 'feature-store' | 'context-store' | 'rag';
}

export const examples: Example[] = [
  {
    id: 'basic-feature',
    title: 'Basic Feature',
    description: 'Define a simple feature with the @feature decorator',
    category: 'feature-store',
    code: `# Basic Feature Store Example
# This runs in your browser using Pyodide!

from dataclasses import dataclass
from typing import Dict, Any
from datetime import timedelta

# Simulated Meridian core (simplified for browser demo)
class FeatureStore:
    def __init__(self):
        self._features: Dict[str, Any] = {}
        self._cache: Dict[str, Any] = {}

    def register_feature(self, name: str, func, **kwargs):
        self._features[name] = {"func": func, **kwargs}
        print(f"✅ Registered feature: {name}")

    async def get_feature(self, name: str, entity_id: str):
        if name not in self._features:
            raise KeyError(f"Feature {name} not found")

        cache_key = f"{name}:{entity_id}"
        if cache_key in self._cache:
            print(f"📦 Cache hit for {cache_key}")
            return self._cache[cache_key]

        value = self._features[name]["func"](entity_id)
        self._cache[cache_key] = value
        print(f"🔄 Computed {name} for {entity_id}: {value}")
        return value

# Initialize store
store = FeatureStore()

# Define an entity
@dataclass
class User:
    user_id: str

# Define a feature using decorator pattern
def feature(entity, refresh="1h", materialize=False):
    def decorator(func):
        store.register_feature(
            func.__name__,
            func,
            entity=entity,
            refresh=refresh,
            materialize=materialize
        )
        return func
    return decorator

# --- YOUR FEATURE DEFINITIONS ---

@feature(entity=User, refresh="daily", materialize=True)
def user_tier(user_id: str) -> str:
    """Determine user tier based on ID hash."""
    return "premium" if hash(user_id) % 2 == 0 else "free"

@feature(entity=User, refresh="5m")
def login_count(user_id: str) -> int:
    """Simulated login count."""
    return abs(hash(user_id + "login")) % 100

# --- TEST THE FEATURES ---

async def main():
    print("\\n🚀 Meridian Feature Store Demo\\n")

    # Fetch features for different users
    for uid in ["user_001", "user_002", "user_003"]:
        tier = await store.get_feature("user_tier", uid)
        logins = await store.get_feature("login_count", uid)
        print(f"   {uid}: tier={tier}, logins={logins}")

    print("\\n✨ Demo complete!")

# Run the async main function (await works in Pyodide)
await main()
`,
  },
  {
    id: 'context-assembly',
    title: 'Context Assembly',
    description: 'Build LLM context with token budgets',
    category: 'context-store',
    code: `# Context Assembly Example
# Demonstrates token budgeting for LLM prompts

from dataclasses import dataclass, field
from typing import List, Optional
import math

@dataclass
class ContextItem:
    """A piece of context with priority and metadata."""
    content: str
    priority: int = 1  # Lower = higher priority (kept first)
    required: bool = False
    metadata: dict = field(default_factory=dict)

    @property
    def tokens(self) -> int:
        # Rough estimate: ~4 chars per token
        return math.ceil(len(self.content) / 4)

class ContextAssembler:
    """Assembles context items within a token budget."""

    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens

    def assemble(self, items: List[ContextItem]) -> tuple[str, dict]:
        # Sort by priority (lower = higher priority)
        sorted_items = sorted(items, key=lambda x: x.priority)

        included = []
        dropped = []
        total_tokens = 0

        for item in sorted_items:
            if total_tokens + item.tokens <= self.max_tokens:
                included.append(item)
                total_tokens += item.tokens
            elif item.required:
                raise ValueError(
                    f"Required item exceeds budget! "
                    f"Need {item.tokens}, have {self.max_tokens - total_tokens}"
                )
            else:
                dropped.append(item)

        content = "\\n\\n".join(item.content for item in included)
        meta = {
            "total_tokens": total_tokens,
            "max_tokens": self.max_tokens,
            "items_included": len(included),
            "items_dropped": len(dropped),
            "dropped_items": [
                {"priority": d.priority, "tokens": d.tokens}
                for d in dropped
            ]
        }

        return content, meta

# --- DEMO ---

print("🎯 Context Assembly Demo\\n")

# Simulate retrieved documents
docs = [
    "Meridian is a feature store and context store for ML and LLM applications.",
    "It runs locally with DuckDB and scales to production with Postgres + Redis.",
    "The @feature decorator lets you define features in pure Python.",
]

# Simulate user preferences
user_prefs = "User prefers technical explanations. Tier: Premium."

# Simulate chat history (large, might get truncated)
chat_history = "\\n".join([
    f"Turn {i}: User asked about feature stores..."
    for i in range(1, 20)
])

# Build context items
items = [
    ContextItem(
        content="You are a helpful assistant for Meridian documentation.",
        priority=0,  # System prompt: highest priority
        required=True
    ),
    ContextItem(
        content="\\n".join(docs),
        priority=1,  # Retrieved docs: high priority
        required=True
    ),
    ContextItem(
        content=user_prefs,
        priority=2,  # User context: medium priority
        required=False
    ),
    ContextItem(
        content=chat_history,
        priority=3,  # History: lowest priority (truncated first)
        required=False
    ),
]

# Assemble with different budgets
for budget in [500, 200, 100]:
    print(f"\\n📊 Budget: {budget} tokens")
    print("-" * 40)

    assembler = ContextAssembler(max_tokens=budget)

    try:
        content, meta = assembler.assemble(items)
        print(f"✅ Assembled {meta['total_tokens']}/{meta['max_tokens']} tokens")
        print(f"   Items: {meta['items_included']} included, {meta['items_dropped']} dropped")
        if meta['dropped_items']:
            print(f"   Dropped: {meta['dropped_items']}")
    except ValueError as e:
        print(f"❌ Error: {e}")

print("\\n✨ Demo complete!")
`,
  },
  {
    id: 'retriever-pattern',
    title: 'Retriever Pattern',
    description: 'Semantic search with the @retriever decorator',
    category: 'rag',
    code: `# Retriever Pattern Example
# Simulates vector search with caching

from dataclasses import dataclass
from typing import List, Dict, Optional
import hashlib
import random

# Simulated vector store
class VectorStore:
    def __init__(self):
        self.documents: Dict[str, dict] = {}

    def index(self, doc_id: str, text: str, embedding: List[float] = None):
        # In real Meridian, this would use OpenAI/Cohere embeddings
        if embedding is None:
            embedding = [random.random() for _ in range(8)]  # Fake embedding

        self.documents[doc_id] = {
            "text": text,
            "embedding": embedding
        }
        print(f"📄 Indexed: {doc_id}")

    def search(self, query: str, top_k: int = 3) -> List[dict]:
        # Simulate semantic search (in real Meridian: pgvector cosine similarity)
        results = []
        for doc_id, doc in self.documents.items():
            # Fake similarity based on word overlap
            query_words = set(query.lower().split())
            doc_words = set(doc["text"].lower().split())
            score = len(query_words & doc_words) / max(len(query_words), 1)
            results.append({
                "id": doc_id,
                "content": doc["text"],
                "score": score + random.random() * 0.1
            })

        # Sort by score and return top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

# Retriever cache
class RetrieverCache:
    def __init__(self, ttl: int = 300):
        self._cache: Dict[str, List[dict]] = {}
        self.ttl = ttl
        self.hits = 0
        self.misses = 0

    def _hash_query(self, query: str, top_k: int) -> str:
        return hashlib.md5(f"{query}:{top_k}".encode()).hexdigest()

    def get(self, query: str, top_k: int) -> Optional[List[dict]]:
        key = self._hash_query(query, top_k)
        if key in self._cache:
            self.hits += 1
            return self._cache[key]
        self.misses += 1
        return None

    def set(self, query: str, top_k: int, results: List[dict]):
        key = self._hash_query(query, top_k)
        self._cache[key] = results

# Initialize
vector_store = VectorStore()
cache = RetrieverCache()

# Index some documents
print("📚 Indexing documents...\\n")

documents = [
    ("doc_1", "Meridian is a feature store for ML engineers"),
    ("doc_2", "The context store helps build RAG applications"),
    ("doc_3", "Use @retriever decorator for semantic search"),
    ("doc_4", "Token budgeting ensures prompts fit LLM context windows"),
    ("doc_5", "Deploy to Fly.io or Cloud Run with one command"),
]

for doc_id, text in documents:
    vector_store.index(doc_id, text)

# Retriever function (simulates @retriever decorator)
def retriever(index: str, top_k: int = 3, cache_ttl: int = 300):
    def decorator(func):
        def wrapper(query: str):
            # Check cache
            cached = cache.get(query, top_k)
            if cached is not None:
                print(f"📦 Cache HIT for: '{query}'")
                return cached

            # Perform search
            print(f"🔍 Searching for: '{query}'")
            results = vector_store.search(query, top_k)

            # Cache results
            cache.set(query, top_k, results)
            return results

        return wrapper
    return decorator

# Define a retriever
@retriever(index="knowledge_base", top_k=3, cache_ttl=300)
def search_docs(query: str) -> List[dict]:
    pass  # Magic wiring handled by decorator

# --- DEMO ---
print("\\n🔍 Search Demo\\n")

queries = [
    "How do I use feature store?",
    "RAG applications",
    "How do I use feature store?",  # Repeat to show cache hit
    "deployment options",
]

for query in queries:
    print(f"\\nQuery: '{query}'")
    results = search_docs(query)
    for r in results:
        print(f"  [{r['score']:.2f}] {r['content'][:50]}...")

print(f"\\n📊 Cache Stats: {cache.hits} hits, {cache.misses} misses")
print("✨ Demo complete!")
`,
  },
  {
    id: 'hybrid-features',
    title: 'Hybrid Features',
    description: 'Mix Python logic and SQL queries',
    category: 'feature-store',
    code: `# Hybrid Features Example
# Demonstrates mixing Python and SQL features

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import math

# Simulated data store (represents DuckDB/Postgres)
class DataStore:
    def __init__(self):
        # Simulated tables
        self.tables = {
            "transactions": [
                {"user_id": "u1", "amount": 100, "ts": "2024-01-01"},
                {"user_id": "u1", "amount": 50, "ts": "2024-01-02"},
                {"user_id": "u1", "amount": 200, "ts": "2024-01-03"},
                {"user_id": "u2", "amount": 75, "ts": "2024-01-01"},
                {"user_id": "u2", "amount": 25, "ts": "2024-01-02"},
            ],
            "users": [
                {"user_id": "u1", "name": "Alice", "lat": 37.7749, "lon": -122.4194},
                {"user_id": "u2", "name": "Bob", "lat": 40.7128, "lon": -74.0060},
            ]
        }

    def query(self, sql: str) -> List[Dict]:
        """Simulate SQL query execution."""
        # Very basic SQL parser for demo
        sql_lower = sql.lower()

        if "count(*)" in sql_lower and "transactions" in sql_lower:
            # COUNT query on transactions
            results = {}
            for row in self.tables["transactions"]:
                uid = row["user_id"]
                results[uid] = results.get(uid, 0) + 1
            return [{"user_id": k, "txn_count": v} for k, v in results.items()]

        elif "sum(amount)" in sql_lower and "transactions" in sql_lower:
            # SUM query on transactions
            results = {}
            for row in self.tables["transactions"]:
                uid = row["user_id"]
                results[uid] = results.get(uid, 0) + row["amount"]
            return [{"user_id": k, "total_amount": v} for k, v in results.items()]

        elif "users" in sql_lower:
            return self.tables["users"]

        return []

# Feature Store with hybrid support
class HybridFeatureStore:
    def __init__(self):
        self.data_store = DataStore()
        self.features: Dict[str, dict] = {}
        self.cache: Dict[str, Any] = {}

    def register(self, name: str, func=None, sql: str = None, **kwargs):
        self.features[name] = {
            "func": func,
            "sql": sql,
            "is_sql": sql is not None,
            **kwargs
        }
        mode = "SQL" if sql else "Python"
        print(f"✅ Registered {mode} feature: {name}")

    def get(self, name: str, entity_id: str) -> Any:
        if name not in self.features:
            raise KeyError(f"Feature {name} not found")

        feature = self.features[name]

        if feature["is_sql"]:
            # Execute SQL and find matching entity
            results = self.data_store.query(feature["sql"])
            for row in results:
                if row.get("user_id") == entity_id:
                    # Return first non-user_id value
                    for k, v in row.items():
                        if k != "user_id":
                            return v
            return feature["func"](entity_id) if feature["func"] else None
        else:
            # Execute Python function
            return feature["func"](entity_id)

store = HybridFeatureStore()

# --- FEATURE DEFINITIONS ---

# SQL Feature: Transaction count (batch aggregation)
store.register(
    "txn_count",
    sql="SELECT user_id, COUNT(*) as txn_count FROM transactions GROUP BY user_id",
    func=lambda uid: 0  # Fallback
)

# SQL Feature: Total spend
store.register(
    "total_spend",
    sql="SELECT user_id, SUM(amount) as total_amount FROM transactions GROUP BY user_id",
    func=lambda uid: 0.0
)

# Python Feature: Haversine distance (complex math)
def distance_from_sf(user_id: str) -> float:
    """Calculate distance from San Francisco HQ."""
    SF_LAT, SF_LON = 37.7749, -122.4194

    # Get user location from data store
    users = store.data_store.query("SELECT * FROM users")
    user = next((u for u in users if u["user_id"] == user_id), None)

    if not user:
        return 0.0

    # Haversine formula
    lat1, lon1 = math.radians(SF_LAT), math.radians(SF_LON)
    lat2, lon2 = math.radians(user["lat"]), math.radians(user["lon"])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    return round(6371 * c, 2)  # km

store.register("distance_from_hq", func=distance_from_sf)

# Python Feature: Risk score (combines SQL + Python)
def risk_score(user_id: str) -> str:
    """Compute risk score using other features."""
    txn_count = store.get("txn_count", user_id)
    total_spend = store.get("total_spend", user_id)
    distance = store.get("distance_from_hq", user_id)

    # Simple risk heuristic
    score = 0
    if txn_count > 2:
        score += 20
    if total_spend > 200:
        score += 30
    if distance > 3000:  # Far from HQ
        score += 10

    if score >= 50:
        return "high"
    elif score >= 20:
        return "medium"
    return "low"

store.register("risk_score", func=risk_score)

# --- DEMO ---
print("\\n🔀 Hybrid Features Demo\\n")

for user_id in ["u1", "u2"]:
    print(f"\\n👤 {user_id}:")
    print(f"   txn_count (SQL): {store.get('txn_count', user_id)}")
    print(f"   total_spend (SQL): \${store.get('total_spend', user_id)}")
    print(f"   distance_from_hq (Python): {store.get('distance_from_hq', user_id)} km")
    print(f"   risk_score (Hybrid): {store.get('risk_score', user_id)}")

print("\\n✨ Demo complete!")
`,
  },
  {
    id: 'event-driven',
    title: 'Event-Driven Features',
    description: 'Update features in real-time on events',
    category: 'feature-store',
    code: `# Event-Driven Features Example
# Demonstrates real-time feature updates via events

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List
import asyncio
import random
import uuid

@dataclass
class Event:
    """Represents an event in the system."""
    event_type: str
    entity_id: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

class EventBus:
    """Simple event bus for publishing/subscribing to events."""

    def __init__(self):
        self.handlers: Dict[str, List[Callable]] = {}
        self.event_log: List[Event] = []

    def subscribe(self, event_type: str, handler: Callable):
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        print(f"📡 Subscribed to: {event_type}")

    async def publish(self, event: Event):
        self.event_log.append(event)
        print(f"\\n📨 Event: {event.event_type} for {event.entity_id}")

        handlers = self.handlers.get(event.event_type, [])
        for handler in handlers:
            await handler(event)

class EventDrivenStore:
    """Feature store with event-driven updates."""

    def __init__(self, bus: EventBus):
        self.bus = bus
        self.features: Dict[str, Any] = {}
        self.triggers: Dict[str, str] = {}  # feature_name -> event_type

    def register_triggered_feature(
        self,
        name: str,
        trigger: str,
        handler: Callable
    ):
        """Register a feature that updates on events."""
        self.triggers[name] = trigger

        async def event_handler(event: Event):
            # Compute new value
            new_value = await handler(event)

            # Update cache
            cache_key = f"{name}:{event.entity_id}"
            old_value = self.features.get(cache_key, "N/A")
            self.features[cache_key] = new_value

            print(f"   🔄 {name}: {old_value} → {new_value}")

        self.bus.subscribe(trigger, event_handler)
        print(f"✅ Registered triggered feature: {name} (on: {trigger})")

    def get(self, name: str, entity_id: str) -> Any:
        cache_key = f"{name}:{entity_id}"
        return self.features.get(cache_key, None)

# Initialize
bus = EventBus()
store = EventDrivenStore(bus)

# --- FEATURE DEFINITIONS ---

# Feature: Last purchase amount (triggered by "purchase" events)
async def handle_last_purchase(event: Event) -> float:
    return event.payload["amount"]

store.register_triggered_feature(
    "last_purchase_amount",
    trigger="purchase",
    handler=handle_last_purchase
)

# Feature: Total purchases (accumulator)
async def handle_total_purchases(event: Event) -> int:
    current = store.get("total_purchases", event.entity_id) or 0
    return current + 1

store.register_triggered_feature(
    "total_purchases",
    trigger="purchase",
    handler=handle_total_purchases
)

# Feature: Total spend (accumulator)
async def handle_total_spend(event: Event) -> float:
    current = store.get("total_spend", event.entity_id) or 0.0
    return round(current + event.payload["amount"], 2)

store.register_triggered_feature(
    "total_spend",
    trigger="purchase",
    handler=handle_total_spend
)

# Feature: Last login timestamp
async def handle_last_login(event: Event) -> str:
    return event.timestamp.isoformat()

store.register_triggered_feature(
    "last_login",
    trigger="login",
    handler=handle_last_login
)

# --- DEMO: Simulate events ---
async def simulate_events():
    print("\\n🎬 Simulating events...\\n")

    events = [
        Event("login", "user_001", {"device": "mobile"}),
        Event("purchase", "user_001", {"amount": 99.99, "product": "Widget A"}),
        Event("purchase", "user_001", {"amount": 49.50, "product": "Widget B"}),
        Event("login", "user_002", {"device": "desktop"}),
        Event("purchase", "user_002", {"amount": 199.00, "product": "Gadget X"}),
        Event("purchase", "user_001", {"amount": 25.00, "product": "Accessory"}),
    ]

    for event in events:
        await bus.publish(event)
        await asyncio.sleep(0.1)  # Small delay for readability

    # Show final state
    print("\\n" + "=" * 50)
    print("📊 Final Feature State")
    print("=" * 50)

    for user_id in ["user_001", "user_002"]:
        print(f"\\n👤 {user_id}:")
        print(f"   last_login: {store.get('last_login', user_id)}")
        print(f"   last_purchase_amount: \${store.get('last_purchase_amount', user_id)}")
        print(f"   total_purchases: {store.get('total_purchases', user_id)}")
        print(f"   total_spend: \${store.get('total_spend', user_id)}")

    print(f"\\n📈 Total events processed: {len(bus.event_log)}")
    print("✨ Demo complete!")

# Run simulation (await works in Pyodide)
await simulate_events()
`,
  },
];

export const getExampleById = (id: string): Example | undefined => {
  return examples.find((e) => e.id === id);
};

export const getExamplesByCategory = (
  category: Example['category']
): Example[] => {
  return examples.filter((e) => e.category === category);
};
