import functools
import inspect
import logging
import sys
import time
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar, cast

import colorlog

from src.shared.config import shared_config

# Type variable for the decorated function's return type
R = TypeVar("R")

LOG_COLORS = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}


class LoggerWrapper:
    """
    Encapsulates logger setup and provides a debugging decorator.
    """

    def __init__(
        self,
        name: str = "shared-components",
        level: int = shared_config.log_level,
        log_format: str | None = None,
        date_format: str | None = None,
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
        console_handler = colorlog.StreamHandler(sys.stdout)

        # Setup formatter
        if log_format is None:
            # Default detailed format good for debugging
            log_format = "%(log_color)s%(levelname)-8s%(reset)s | %(asctime)s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
        if date_format is None:
            date_format = "%Y-%m-%d %H:%M:%S"
        formatter = colorlog.ColoredFormatter(
            fmt=log_format,
            datefmt=date_format,
            reset=True,
            log_colors=LOG_COLORS,
            secondary_log_colors={},  # You can color specific parts of the message too
            style="%",  # Use %-style formatting
        )
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

        # --- Define the appropriate wrapper based on whether func is async ---

        if is_async:
            # Define an ASYNC wrapper for ASYNC functions
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> R:
                args_repr = [repr(a) for a in args]
                kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
                signature = ", ".join(args_repr + kwargs_repr)
                max_sig_length = 1000
                signature = (
                    (signature[:max_sig_length] + "...")
                    if len(signature) > max_sig_length
                    else signature
                )

                self.logger.debug(f"Entering (async): {func_name}({signature})")
                start_time = time.perf_counter()
                try:
                    # Await the original async function
                    # No need for cast here, await handles the coroutine nature
                    result = await func(*args, **kwargs)
                    end_time = time.perf_counter()
                    duration = end_time - start_time
                    # Be careful logging potentially large results
                    result_repr = repr(result)
                    max_repr_len = 500 # Limit logged result size
                    result_log = (result_repr[:max_repr_len] + '...') if len(result_repr) > max_repr_len else result_repr
                    self.logger.debug(
                        f"Exiting (async): {func_name} (returned: {result_log}, duration: {duration:.4f}s)"
                    )
                    return result # Return the actual result
                except Exception as e:
                    end_time = time.perf_counter()
                    duration = end_time - start_time
                    self.logger.exception( # Use logger.exception to include traceback info automatically
                        f"Exception in (async) {func_name} after {duration:.4f}s: {e!r}"
                    )
                    # No need for exc_info=True with logger.exception
                    raise # Re-raise the exception

            # Return the async wrapper function itself
            return async_wrapper # type: ignore # Ignore type checking for dynamic return

        else:
            # Define a SYNC wrapper for SYNC functions
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> R:
                args_repr = [repr(a) for a in args]
                kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
                signature = ", ".join(args_repr + kwargs_repr)
                max_sig_length = 1000
                signature = (
                    (signature[:max_sig_length] + "...")
                    if len(signature) > max_sig_length
                    else signature
                )

                self.logger.debug(f"Entering (sync): {func_name}({signature})")
                start_time = time.perf_counter()
                try:
                    # Call the original sync function
                    # No need for cast here either
                    result = func(*args, **kwargs)
                    end_time = time.perf_counter()
                    duration = end_time - start_time
                    # Be careful logging potentially large results
                    result_repr = repr(result)
                    max_repr_len = 500 # Limit logged result size
                    result_log = (result_repr[:max_repr_len] + '...') if len(result_repr) > max_repr_len else result_repr
                    self.logger.debug(
                        f"Exiting (sync): {func_name} (returned: {result_log}, duration: {duration:.4f}s)"
                    )
                    return result # type: ignore
                except Exception as e:
                    end_time = time.perf_counter()
                    duration = end_time - start_time
                    self.logger.exception( # Use logger.exception
                        f"Exception in (sync) {func_name} after {duration:.4f}s: {e!r}"
                    )
                    raise # Re-raise the exception

            # Return the sync wrapper function itself
            return sync_wrapper # type: ignore # Ignore type checking for dynamic return


logger_wrapper = LoggerWrapper()
logger = logger_wrapper.logger
