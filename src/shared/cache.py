import asyncio
import hashlib
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar, cast

import orjson
from diskcache import Cache  # type: ignore

from src.shared.config import Logger

logger = Logger("cache").logger

# Type variables for better type safety
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])

# Global cache instance
_cache_instance = None


def get_disk_cache() -> Cache:
    """Get or create the disk cache instance."""
    global _cache_instance
    if _cache_instance is None:
        cache_dir = Path(__file__).parent.parent / ".cache"
        # Ensure cache directory exists
        cache_dir.mkdir(parents=True, exist_ok=True)
        _cache_instance = Cache(str(cache_dir))
        assert _cache_instance is not None, "Failed to create disk cache instance"
    return _cache_instance


def serialize_value(value: Any) -> bytes:
    """Serialize a value to bytes for caching."""
    try:
        if hasattr(value, "model_dump"):  # Pydantic model
            result = orjson.dumps(value.model_dump())
        elif hasattr(value, "__dict__"):  # Regular class instance
            result = orjson.dumps(value.__dict__)
        else:  # Other types
            result = orjson.dumps(value, default=str)

        assert isinstance(result, bytes), "Serialization did not produce bytes"
        return result
    except Exception as e:
        logger.error(f"Serialization error: {str(e)}")
        # Fallback to string serialization
        return orjson.dumps(str(value))


def deserialize_value(value: Any) -> Any:
    """Deserialize a value from bytes."""
    if value is None:
        return None

    if isinstance(value, (bytes | bytearray | str)):
        try:
            return orjson.loads(value)
        except Exception as e:
            logger.error(f"Deserialization error: {str(e)}")
            return value
    return value


def _generate_cache_key(
    func: Callable[..., Any], param_name: str | None, kwargs: dict[str, Any]
) -> str:
    """Generate a cache key for the function call."""
    key_parts = [func.__module__, func.__name__]
    assert all(isinstance(part, str) for part in key_parts), "Key parts must be strings"

    # Add parameter value to key if specified
    if param_name and param_name in kwargs:
        param_value = kwargs[param_name]
        if param_value is not None:
            # Handle various parameter types appropriately
            try:
                if hasattr(param_value, "model_dump"):  # Pydantic V2+
                    param_hash = hashlib.md5(
                        orjson.dumps(param_value.model_dump())
                    ).hexdigest()
                elif hasattr(param_value, "dict"):  # Pydantic V1
                    param_hash = hashlib.md5(
                        orjson.dumps(param_value.dict())
                    ).hexdigest()
                elif isinstance(param_value, (str | int | float | bool)):
                    param_hash = str(param_value)
                else:
                    try:
                        # Try standard orjson serialization first
                        param_hash = hashlib.md5(orjson.dumps(param_value)).hexdigest()
                    except TypeError:
                        # Fallback to string representation if not serializable
                        param_hash = str(param_value)

                key_parts.append(f"{param_name}={param_hash}")
            except Exception as e:
                logger.error(
                    f"Error creating cache key component for {param_name}: {str(e)}"
                )
                # Add a safe version of the parameter to the key
                key_parts.append(f"{param_name}=<complex_object>")

    cache_key = ":".join(key_parts)
    assert isinstance(cache_key, str), "Cache key must be a string"
    return cache_key


def _get_from_cache(cache: Cache, cache_key: str) -> Any | None:
    """Attempt to retrieve and deserialize data from cache."""
    cached_data = cast(bytes | None, cache.get(cache_key))  # type: ignore
    if cached_data is not None:
        logger.debug(f"Cache hit for {cache_key}")
        return deserialize_value(cached_data)
    logger.debug(f"Cache miss for {cache_key}")
    return None


def _set_to_cache(cache: Cache, cache_key: str, result: Any, ttl: int) -> None:
    """Serialize and store data into the cache."""
    serialized_result = serialize_value(result)
    assert isinstance(serialized_result, bytes), "Serialized result must be bytes"
    success = cast(bool, cache.set(cache_key, serialized_result, expire=ttl))  # type: ignore
    assert success, "Failed to set cache value"


def disk_cache(
    param_name: str | None = None,
    ttl: int = 3600,  # 1 hour default
) -> Callable[[F], F]:
    """
    Cache decorator using diskcache.

    Args:
        param_name: The parameter name to include in the cache key
        ttl: Time to live for cache entries in seconds

    Returns:
        Decorated function with caching
    """
    assert ttl > 0, "Cache TTL must be positive"

    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_key = _generate_cache_key(func, param_name, kwargs)
            try:
                cache = get_disk_cache()
                cached_result = _get_from_cache(cache, cache_key)
                if cached_result is not None:
                    return cached_result

                # Cache miss, execute async function
                result = await func(*args, **kwargs)

                # Store the result
                _set_to_cache(cache, cache_key, result, ttl)
                return result
            except Exception as e:
                logger.error(f"Caching error for async {cache_key}: {str(e)}")
                # Fall back to calling the function without caching
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_key = _generate_cache_key(func, param_name, kwargs)
            try:
                cache = get_disk_cache()
                cached_result = _get_from_cache(cache, cache_key)
                if cached_result is not None:
                    return cached_result

                # Cache miss, execute sync function
                result = func(*args, **kwargs)

                # Store the result
                _set_to_cache(cache, cache_key, result, ttl)
                return result
            except Exception as e:
                logger.error(f"Caching error for sync {cache_key}: {str(e)}")
                # Fall back to calling the function without caching
                return func(*args, **kwargs)

        # Return the appropriate wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    return decorator
