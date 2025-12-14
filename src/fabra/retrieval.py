from typing import Any, Callable, List, Optional, Dict, Union, cast
from dataclasses import dataclass, field
import functools
import structlog
from datetime import timedelta
import time

logger = structlog.get_logger()


@dataclass
class Retriever:
    name: str
    func: Callable[..., List[Dict[str, Any]]]
    backend: str = "custom"
    cache_ttl: Optional[timedelta] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash(self.name)


class RetrieverRegistry:
    def __init__(self) -> None:
        self.retrievers: Dict[str, Retriever] = {}

    def register(self, retriever: Retriever) -> None:
        if retriever.name in self.retrievers:
            logger.warning(f"Overwriting existing retriever: {retriever.name}")
        self.retrievers[retriever.name] = retriever
        logger.info(f"Registered retriever: {retriever.name}")

    def get(self, name: str) -> Optional[Retriever]:
        return self.retrievers.get(name)


def retriever(
    backend: str = "custom",
    cache_ttl: Optional[Union[str, timedelta]] = None,
    name: Optional[str] = None,
    index: Optional[str] = None,
    top_k: int = 5,
) -> Any:
    """
    Decorator to register a function as a Retriever.

    Args:
        backend: "custom" (Python) or "postgres" (SQL).
        cache_ttl: Optional TTL for caching results.
        name: Optional override for retriever name.
        index: (Optional) Index name to automatically search. If set, function body is ignored (or run as pre-process?).
               For MVP: If index is set, we use auto-wiring and ignore function body unless it returns specific query override?
               Simpler: Auto-wiring completely replaces body logic if body is empty?
               Let's assume auto-wiring overrides execution but uses args as query.
        top_k: Number of results to return for auto-wiring.
    """

    def decorator(
        func: Callable[..., List[Dict[str, Any]]],
    ) -> Callable[..., List[Dict[str, Any]]]:
        # Resolve effective name
        r_name = name or func.__name__

        # Parse TTL
        parsed_ttl = None
        if cache_ttl:
            # Basic string parsing fallback if not a timedelta
            if isinstance(cache_ttl, timedelta):
                parsed_ttl = cache_ttl

        ret_obj = Retriever(
            name=r_name,
            func=func,
            backend=backend,
            cache_ttl=parsed_ttl,
            description=func.__doc__,
        )

        # Attach to function for inspection
        setattr(func, "_fabra_retriever", ret_obj)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
            # Check for injected cache backend
            store_backend = getattr(ret_obj, "_cache_backend", None)

            # Note: Sync wrapper cannot easily support Auto-Wiring because Store.search is async.
            # If user uses index=..., they SHOULD use async def.
            # We will handle this limitation in validation or runtime error.

            # If caching is enabled and backend is available
            if ret_obj.cache_ttl and store_backend:
                try:
                    import json
                    import hashlib

                    # Simple cache key generation
                    # We hash args/kwargs.
                    # Note: this requires picklable/jsonable args.
                    key_parts = [r_name, str(args), str(kwargs)]
                    key_str = json.dumps(key_parts, sort_keys=True, default=str)
                    key_hash = hashlib.sha256(key_str.encode("utf-8")).hexdigest()
                    _cache_key = f"fabra:retriever:{r_name}:{key_hash}"

                    # ... Sync wrapper cache logic omitted for brevity as we prioritize Async ...

                except Exception as e:
                    logger.warning(f"Cache key generation failed: {e}")

            from typing import cast

            return cast(List[Dict[str, Any]], list(func(*args, **kwargs)))

        # Helper for DAG Resolution
        async def _resolve_args(args: Any, kwargs: Any) -> Any:
            store_ref = getattr(ret_obj, "_fabra_store_ref", None)
            if not store_ref:
                return args, kwargs

            # Need entity_id to resolve
            entity_id = kwargs.get("entity_id")
            if not entity_id:
                return args, kwargs

            from fabra.graph import DependencyResolver

            resolver = DependencyResolver(store_ref)

            new_args = list(args)
            new_kwargs = kwargs.copy()

            # Resolve Kwargs
            for k, v in new_kwargs.items():
                if isinstance(v, str) and "{" in v and "}" in v:
                    try:
                        resolved = await resolver.execute_dag(v, entity_id)
                        new_kwargs[k] = resolved
                    except Exception as e:
                        logger.warning(
                            f"DAG resolution failed for kwarg {k}", error=str(e)
                        )

            return tuple(new_args), new_kwargs

        # Async Wrapper Support
        import inspect

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
                # 1. Resolve DAG Dependencies
                args, kwargs = await _resolve_args(args, kwargs)

                store_backend = getattr(ret_obj, "_cache_backend", None)

                # Check Cache
                cache_key = None
                if ret_obj.cache_ttl and store_backend:
                    try:
                        import json
                        import hashlib

                        key_parts = [r_name, str(args), str(kwargs)]
                        key_str = json.dumps(key_parts, sort_keys=True, default=str)
                        key_hash = hashlib.sha256(key_str.encode("utf-8")).hexdigest()
                        cache_key = f"fabra:retriever:{r_name}:{key_hash}"

                        # Try fetch
                        cached = await store_backend.get(cache_key)
                        if cached:
                            logger.info(f"Retriever Cache Hit: {r_name}")
                            parsed = cast(List[Dict[str, Any]], json.loads(cached))
                            try:
                                from fabra.context import record_retriever_usage

                                query_str = ""
                                if args and isinstance(args[0], str):
                                    query_str = args[0]
                                elif isinstance(kwargs.get("query"), str):
                                    query_str = cast(str, kwargs.get("query"))

                                record_retriever_usage(
                                    retriever_name=r_name,
                                    query=query_str,
                                    results_count=len(parsed)
                                    if isinstance(parsed, list)
                                    else 0,
                                    latency_ms=0.0,
                                    index_name=index,
                                    chunks=[
                                        item
                                        if isinstance(item, dict)
                                        else {"content": str(item)}
                                        for item in (
                                            parsed if isinstance(parsed, list) else []
                                        )
                                    ],
                                )
                            except Exception as e:
                                logger.debug(
                                    "record_retriever_usage_failed",
                                    retriever_name=r_name,
                                    error=str(e),
                                )
                            return parsed
                    except Exception as e:
                        logger.warning(f"Retriever Caching Error: {e}")

                # Execute Logic
                result: List[Dict[str, Any]] = []
                started = time.perf_counter()

                # AUTO-WIRING LOGIC
                if index is not None:
                    # We need the store reference
                    store_ref = getattr(ret_obj, "_fabra_store_ref", None)
                    if store_ref:
                        # Assumption: First arg is query string
                        query = args[0] if args else kwargs.get("query")
                        if not isinstance(query, str):
                            logger.warning(
                                "Auto-wiring requires string query as first arg or 'query' kwarg."
                            )
                            # Fallback to function execution?
                            result = await func(*args, **kwargs)
                        else:
                            # Execute Search on Store
                            try:
                                result = await store_ref.search(index, query, top_k)
                            except NotImplementedError:
                                logger.error(
                                    "Store search not implemented or available."
                                )
                                result = []

                            # Allow function to post-process?
                            # For now, completely replace.
                    else:
                        logger.warning(
                            "Retriever has 'index' but no store reference. Skipping auto-wiring."
                        )
                        result = await func(*args, **kwargs)
                else:
                    # Normal Execution
                    result = await func(*args, **kwargs)

                latency_ms = (time.perf_counter() - started) * 1000.0

                # Best-effort lineage capture (only records if we're inside a @context call).
                try:
                    from fabra.context import record_retriever_usage

                    def normalize_chunks(items: Any) -> List[Dict[str, Any]]:
                        if not isinstance(items, list):
                            return []
                        chunks: List[Dict[str, Any]] = []
                        for i, item in enumerate(items):
                            if isinstance(item, dict):
                                meta: Dict[str, Any] = {}
                                raw_meta = item.get("metadata")
                                if isinstance(raw_meta, dict):
                                    meta = raw_meta
                                chunks.append(
                                    {
                                        "chunk_id": item.get("chunk_id")
                                        or meta.get("chunk_id")
                                        or f"chunk_{i}",
                                        "document_id": item.get("document_id")
                                        or meta.get("document_id")
                                        or meta.get("source_id")
                                        or item.get("id")
                                        or "unknown",
                                        "content": item.get("content")
                                        or meta.get("content")
                                        or "",
                                        "content_hash": meta.get("content_hash")
                                        or item.get("content_hash"),
                                        "indexed_at": meta.get("ingestion_timestamp")
                                        or meta.get("indexed_at")
                                        or meta.get("created_at"),
                                        "similarity_score": item.get("score")
                                        or item.get("similarity_score")
                                        or 0.0,
                                        "source_url": meta.get("source_url")
                                        or meta.get("url"),
                                    }
                                )
                            else:
                                chunks.append(
                                    {
                                        "chunk_id": f"chunk_{i}",
                                        "document_id": "unknown",
                                        "content": str(item),
                                    }
                                )
                        return chunks

                    query_str = ""
                    if args and isinstance(args[0], str):
                        query_str = args[0]
                    elif isinstance(kwargs.get("query"), str):
                        query_str = cast(str, kwargs.get("query"))

                    record_retriever_usage(
                        retriever_name=r_name,
                        query=query_str,
                        results_count=len(result) if isinstance(result, list) else 0,
                        latency_ms=latency_ms,
                        index_name=index,
                        chunks=normalize_chunks(result),
                    )
                except Exception as e:
                    logger.debug(
                        "record_retriever_usage_failed",
                        retriever_name=r_name,
                        error=str(e),
                    )

                # Store in Cache
                if cache_key and store_backend:
                    try:
                        ttl_sec = int(ret_obj.cache_ttl.total_seconds())  # type: ignore
                        await store_backend.set(
                            cache_key, json.dumps(result), ex=ttl_sec
                        )
                    except Exception as e:
                        logger.warning(f"Retriever Cache Write Error: {e}")

                return result

            return async_wrapper  # type: ignore[return-value]

        # Sync Wrapper
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
            if index:
                raise RuntimeError(
                    "Auto-wiring with 'index' requires 'async def' retriever."
                )

            # Sync cannot await DAG resolution simply.
            # Limitation: DAG Wiring only supported for Async Retrievers in V1.

            has_template = any(isinstance(v, str) and "{" in v for v in kwargs.values())
            if has_template:
                logger.warning(
                    "sync_retriever_dag_skipped",
                    reason="DAG resolution requires async retriever",
                )

            result = func(*args, **kwargs)

            import inspect

            if inspect.isawaitable(result):
                # Safety check: if user wrapped an async func but it wasn't detected as coroutinefunction
                # (e.g. partial or other callable), we can't await it here.
                raise RuntimeError(
                    "Sync retriever returned awaitable. Use async def for async retrievers."
                )

            return cast(List[Dict[str, Any]], list(result))

        return sync_wrapper

    return decorator
