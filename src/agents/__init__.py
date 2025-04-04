from src.shared.logging import LoggerWrapper

logger_wrapper = LoggerWrapper("agents")
logger = logger_wrapper.logger

__all__ = ["logger"]
