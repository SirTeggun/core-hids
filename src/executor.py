import logging
from typing import Callable, Any, Tuple

logger = logging.getLogger(__name__)


class PipelineExecutor:
    """Centralized safe execution wrapper for pipeline steps."""

    @staticmethod
    def execute(
        step_function: Callable,
        *args: Any,
        default: Any = None,
        log_level: int = logging.ERROR,
        fatal_exceptions: Tuple[type, ...] = (),
        **kwargs: Any
    ) -> Any:
        """Execute a callable safely, returning `default` on non-fatal errors."""

        if not callable(step_function):
            logger.error("Non-callable passed to PipelineExecutor")
            return default

        try:
            return step_function(*args, **kwargs)
        except fatal_exceptions:
            raise
        except Exception as e:
            logger.log(
                log_level,
                "Error executing function",
                extra={
                    "function_name": getattr(step_function, "__name__", str(step_function)),
                    "error": str(e),
                },
                exc_info=True,
            )
            return default