"""Structured logging with correlation IDs via structlog.

Scalability note: In production, ship logs to a central aggregator
(Loki, ELK, Cloud Logging) by adding a structlog processor or using
a logging handler that writes to stdout in JSON (already done here).
"""

from __future__ import annotations

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any

import structlog

request_id_var: ContextVar[str] = ContextVar("request_id", default="")
tenant_id_var: ContextVar[str] = ContextVar("tenant_id", default="")
student_id_var: ContextVar[str] = ContextVar("student_id", default="")


def add_correlation_ids(
    logger: Any, method: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    request_id = request_id_var.get("")
    if request_id:
        event_dict["request_id"] = request_id
    tenant_id = tenant_id_var.get("")
    if tenant_id:
        event_dict["tenant_id"] = tenant_id
    student_id = student_id_var.get("")
    if student_id:
        event_dict["student_id"] = student_id
    return event_dict


def configure_logging(log_level: str = "INFO", log_format: str = "console") -> None:
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        add_correlation_ids,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
    ]

    if log_format == "json":
        renderer: Any = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )


def new_request_id() -> str:
    rid = str(uuid.uuid4())
    request_id_var.set(rid)
    return rid


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)
