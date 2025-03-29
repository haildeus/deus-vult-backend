import functools
import inspect
import logging
import sys
import time
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar, cast

from src.shared.config import shared_config

# Type variable for the decorated function's return type
R = TypeVar("R")


class LoggerWrapper:
    """
    Encapsulates logger setup and provides a debugging decorator.
    """

    def __init__(
        self,
        name: str = "shared-components",
        level: int = shared_config.log_level,
        log_format: str | None = None,
    ):
        """
        Initializes and configures a logger instance.

        Args:
            name: The name of the logger.
            level: The logging level (e.g., logging.DEBUG, logging.INFO).
            log_format: Optional custom log format string. Defaults to a detailed format.
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Prevent duplicate handlers if this name was somehow configured before
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)

        # Setup formatter
        if log_format is None:
            # Default detailed format good for debugging
            log_format = "%(levelname)s - %(asctime)s - %(name)s - [%(funcName)s:%(lineno)d] - %(message)s"
        formatter = logging.Formatter(log_format)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)
        self.logger.debug(
            f"Logger '{name}' initialized with level {logging.getLevelName(level)}."
        )

    def log_debug(
        self, func: Callable[..., R | Coroutine[Any, Any, R]]
    ) -> Callable[..., R | Coroutine[Any, Any, R]]:
        """
        Decorator factory: returns a decorator that logs function execution details at DEBUG level.

        Handles both synchronous and asynchronous functions. Logs entry, exit,
        arguments, return value, execution time, and exceptions.
        """
        func_name = func.__name__
        is_async = inspect.iscoroutinefunction(func)

        # The actual decorator being returned
        @functools.wraps(func)
        def decorator_wrapper(*args: Any, **kwargs: Any) -> R | Coroutine[Any, Any, R]:
            # --- sync/async execution logic ---
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            # Truncate long signatures
            max_sig_length = 1000
            signature = (
                (signature[:max_sig_length] + "...")
                if len(signature) > max_sig_length
                else signature
            )

            async def async_executor() -> R:
                """Executes and logs async functions."""
                self.logger.debug(f"Entering (async): {func_name}({signature})")
                start_time = time.perf_counter()
                try:
                    # Ensure we await the coroutine returned by the original async function
                    async_callable = cast(Callable[..., Coroutine[Any, Any, R]], func)
                    result = await async_callable(*args, **kwargs)
                    end_time = time.perf_counter()
                    duration = end_time - start_time
                    self.logger.debug(
                        f"Exiting (async): {func_name} (returned: {result!r}, duration: {duration:.4f}s)"
                    )
                    return result
                except Exception as e:
                    end_time = time.perf_counter()
                    duration = end_time - start_time
                    self.logger.debug(
                        f"Exception in (async) {func_name} after {duration:.4f}s: {e!r}",
                        exc_info=True,
                    )
                    raise

            def sync_executor() -> R:
                """Executes and logs sync functions."""
                self.logger.debug(f"Entering (sync): {func_name}({signature})")
                start_time = time.perf_counter()
                try:
                    sync_callable = cast(Callable[..., R], func)
                    result = sync_callable(*args, **kwargs)
                    end_time = time.perf_counter()
                    duration = end_time - start_time
                    self.logger.debug(
                        f"Exiting (sync): {func_name} (returned: {result!r}, duration: {duration:.4f}s)"
                    )
                    return result
                except Exception as e:
                    end_time = time.perf_counter()
                    duration = end_time - start_time
                    self.logger.debug(
                        f"Exception in (sync) {func_name} after {duration:.4f}s: {e!r}",
                        exc_info=True,
                    )
                    raise

            # --- Choose the executor based on type ---
            if is_async:
                # Return the coroutine object created by async_executor
                return async_executor()
            else:
                # Execute the sync function directly
                return sync_executor()

        # Return the callable wrapper created by @functools.wraps
        return decorator_wrapper  # type: ignore # Ignore for dynamic return


logger_wrapper = LoggerWrapper()
logger = logger_wrapper.logger
