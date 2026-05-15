import json
import logging
from io import StringIO

from cloudops_core.logging import configure_logging, get_logger


def test_logger_emits_json_with_service_field(capsys):
    configure_logging(service="my-svc", level="INFO")
    log = get_logger()
    log.info("hello", saga_id="s-1")

    captured = capsys.readouterr().out.strip()
    assert captured, "expected log output on stdout"
    line = json.loads(captured)
    assert line["service"] == "my-svc"
    assert line["event"] == "hello"
    assert line["saga_id"] == "s-1"
    assert line["level"] == "info"
