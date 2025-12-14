import os
from abc import ABC, abstractmethod

__all__ = [
    "BaseConfig",
    "DevConfig",
    "ProdConfig",
    "get_config",
    "get_store_factory",
    "get_redis_url",
    "get_duckdb_path",
    "OfflineStore",
    "OnlineStore",
    "DuckDBOfflineStore",
    "InMemoryOnlineStore",
    "PostgresOfflineStore",
    "RedisOnlineStore",
]

from fabra.store.offline import OfflineStore, DuckDBOfflineStore
from fabra.store.online import OnlineStore, InMemoryOnlineStore

# Try to import production stores (dependencies might not be installed in dev)
try:
    from fabra.store.postgres import PostgresOfflineStore
except ImportError:
    PostgresOfflineStore = None  # type: ignore

try:
    from fabra.store.redis import RedisOnlineStore
except ImportError:
    RedisOnlineStore = None  # type: ignore


def get_redis_url() -> str:
    """Returns the configured Redis URL or a sensible default for local dev."""
    return os.environ.get("FABRA_REDIS_URL", "redis://localhost:6379")


def get_duckdb_path() -> str:
    """
    Returns the configured DuckDB file path.

    Defaults to a durable per-user location so Context IDs survive restarts.
    Set `FABRA_DUCKDB_PATH=:memory:` to force in-memory behavior.
    """
    configured = os.environ.get("FABRA_DUCKDB_PATH")
    if configured:
        return configured

    home = os.path.expanduser("~")
    return os.path.join(home, ".fabra", "fabra.duckdb")


def _ensure_parent_dir(file_path: str) -> None:
    if file_path == ":memory:":
        return
    parent = os.path.dirname(file_path)
    if parent:
        os.makedirs(parent, exist_ok=True)


class BaseConfig(ABC):
    @abstractmethod
    def get_offline_store(self) -> OfflineStore:
        pass

    @abstractmethod
    def get_online_store(self) -> OnlineStore:
        pass


class DevConfig(BaseConfig):
    def get_offline_store(self) -> OfflineStore:
        duckdb_path = get_duckdb_path()
        _ensure_parent_dir(duckdb_path)
        return DuckDBOfflineStore(database=duckdb_path)

    def get_online_store(self) -> OnlineStore:
        # Auto-detect Redis
        redis_url = os.environ.get("FABRA_REDIS_URL") or os.environ.get("REDIS_URL")

        if redis_url and RedisOnlineStore is not None:
            return RedisOnlineStore(redis_url=redis_url)

        return InMemoryOnlineStore()


class ProdConfig(BaseConfig):
    def get_offline_store(self) -> OfflineStore:
        if PostgresOfflineStore is None:
            raise ImportError(
                "PostgresOfflineStore not available. Install 'asyncpg' and 'sqlalchemy'."
            )

        url = os.environ.get("FABRA_POSTGRES_URL")
        if not url:
            raise ValueError(
                "FABRA_POSTGRES_URL environment variable is required for production."
            )
        return PostgresOfflineStore(connection_string=url)

    def get_online_store(self) -> OnlineStore:
        if RedisOnlineStore is None:
            raise ImportError("RedisOnlineStore not available. Install 'redis'.")

        url = os.environ.get("FABRA_REDIS_URL")
        if not url:
            raise ValueError(
                "FABRA_REDIS_URL environment variable is required for production."
            )
        return RedisOnlineStore(redis_url=url)


def get_config() -> BaseConfig:
    env = os.environ.get("FABRA_ENV", "development").lower()
    if env == "production":
        return ProdConfig()
    return DevConfig()


def get_store_factory() -> tuple[OfflineStore, OnlineStore]:
    """Helper to get both stores at once."""
    config = get_config()
    return config.get_offline_store(), config.get_online_store()
