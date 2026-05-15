import logging
import sys

import structlog


def configure_logging(*, service: str, level: str = "INFO") -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _inject_service(service),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level.upper())),
        cache_logger_on_first_use=False,
    )


def _inject_service(service: str):
    def processor(_, __, event_dict):
        event_dict["service"] = service
        return event_dict
    return processor


def get_logger() -> structlog.BoundLogger:
    return structlog.get_logger()
