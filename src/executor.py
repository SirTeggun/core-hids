import logging
from typing import Callable, Any, Tuple

logger = logging.getLogger(__name__)


class PipelineExecutor:
    @staticmethod
    def execute(
        step_function: Callable,
        *args: Any,
        default: Any = None,
        log_level: int = logging.ERROR,
        fatal_exceptions: Tuple[type, ...] = (),
        **kwargs: Any
    ) -> Any:
        if not callable(step_function):
            logger.error(
                "PipelineExecutor: non-callable received",
                extra={
                    "object_type": type(step_function).__name__,
                    "object_repr": repr(step_function)
                }
            )
            return default

        func_name = getattr(step_function, "__name__", None)
        if func_name is None:
            func_name = repr(step_function)

        try:
            return step_function(*args, **kwargs)
        except fatal_exceptions:
            raise
        except Exception as e:
            logger.log(
                log_level,
                "PipelineExecutor: error executing function",
                extra={
                    "function_name": func_name,
                    "args": _safe_repr(args),
                    "kwargs": _safe_repr(kwargs),
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
                exc_info=True,
            )
            return default


def _safe_repr(obj: Any, max_len: int = 200) -> str:
    try:
        repr_str = repr(obj)
        if len(repr_str) > max_len:
            return repr_str[:max_len] + "..."
        return repr_str
    except Exception:
        return f"<unrepresentable: {type(obj).__name__}>"