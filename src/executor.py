"""
Centralized safe execution gateway for CORE-HIDS pipeline.
Prevents single-module failures from breaking the detection workflow.
"""

import logging
from typing import Callable, Any, Tuple

logger = logging.getLogger(__name__)

class PipelineExecutor:
    """
    Provides a static method to safely execute any pipeline step.
    """

    @staticmethod
    def execute(
        step_function: Callable,
        *args: Any,
        default: Any = None,
        log_level: int = logging.ERROR,
        fatal_exceptions: Tuple[Exception, ...] = (),
        **kwargs: Any
    ) -> Any:
        """
        Execute a step function safely, catching non‑fatal exceptions.

        Args:
            step_function: The callable to execute.
            *args: Positional arguments for the callable.
            default: Value to return if an exception is caught.
            log_level: Logging level for the error message.
            fatal_exceptions: Tuple of exception types that should NOT be caught
                              (they will propagate normally).
            **kwargs: Keyword arguments for the callable.

        Returns:
            The result of step_function, or `default` if an exception was caught.
        """
        if not callable(step_function):
            logger.error(
                "PipelineExecutor received non-callable step_function",
                extra={"step_function": str(step_function)}
            )
            return default

        try:
            return step_function(*args, **kwargs)
        except fatal_exceptions:
            raise
        except Exception as e:
            func_name = getattr(step_function, "__name__", str(step_function))
            logger.log(
                log_level,
                "Error executing function",
                extra={
                    "function_name": func_name,
                    "error": str(e)
                },
                exc_info=True
            )
            return default