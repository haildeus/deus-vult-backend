from src import LoggerWrapper

logger_wrapper = LoggerWrapper("api")
logger = logger_wrapper.logger

__all__ = ["logger"]
