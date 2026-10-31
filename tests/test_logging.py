from __future__ import annotations

import io
import json
import logging

from app.core.logging import JsonFormatter, configure_logging, request_id_ctx


def _logger_with_buffer() -> tuple[logging.Logger, io.StringIO]:
    buffer = io.StringIO()
    handler = logging.StreamHandler(buffer)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("nmi.test.logging")
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)
    return logger, buffer


def test_emits_single_line_json_with_core_fields() -> None:
    logger, buffer = _logger_with_buffer()
    logger.info("hello %s", "world")

    line = buffer.getvalue().strip()
    assert "\n" not in line
    payload = json.loads(line)
    assert payload["message"] == "hello world"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "nmi.test.logging"
    assert "timestamp" in payload
    assert "request_id" not in payload


def test_includes_request_id_when_set() -> None:
    logger, buffer = _logger_with_buffer()
    token = request_id_ctx.set("req-123")
    try:
        logger.info("inside request")
    finally:
        request_id_ctx.reset(token)

    assert json.loads(buffer.getvalue())["request_id"] == "req-123"


def test_includes_extra_fields() -> None:
    logger, buffer = _logger_with_buffer()
    logger.info("with extras", extra={"dependency": "redis", "status_code": 503})

    payload = json.loads(buffer.getvalue())
    assert payload["dependency"] == "redis"
    assert payload["status_code"] == 503


def test_includes_exception_details() -> None:
    logger, buffer = _logger_with_buffer()
    try:
        raise ValueError("boom")
    except ValueError:
        logger.exception("failed")

    payload = json.loads(buffer.getvalue())
    assert "ValueError: boom" in payload["exception"]


def test_configure_logging_is_idempotent_and_sets_level() -> None:
    configure_logging("WARNING")
    configure_logging("WARNING")
    root = logging.getLogger()
    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0].formatter, JsonFormatter)
    assert root.level == logging.WARNING
    configure_logging("INFO")
