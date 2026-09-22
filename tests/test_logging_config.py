"""Tests for GCP logging configuration helpers."""
import importlib
import json
import logging

import sds_common.config.logging_config as lc
from sds_common.config.logging_config import GcpJsonFormatter, configure_gcp_logging, get_log_level


class TestGetLogLevel:
    def test_returns_info_by_default(self, monkeypatch):
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        assert get_log_level() == logging.INFO

    def test_returns_debug_when_set(self, monkeypatch):
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        assert get_log_level() == logging.DEBUG

    def test_returns_warning_when_set(self, monkeypatch):
        monkeypatch.setenv("LOG_LEVEL", "WARNING")
        assert get_log_level() == logging.WARNING


class TestGcpJsonFormatter:
    def _make_record(self, msg="test message", level=logging.INFO, exc_info=None):
        record = logging.LogRecord(
            name="test.logger",
            level=level,
            pathname="",
            lineno=0,
            msg=msg,
            args=(),
            exc_info=exc_info,
        )
        return record

    def test_outputs_valid_json(self):
        formatter = GcpJsonFormatter()
        output = formatter.format(self._make_record())
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_severity_field_matches_level(self):
        formatter = GcpJsonFormatter()
        output = json.loads(formatter.format(self._make_record(level=logging.WARNING)))
        assert output["severity"] == "WARNING"

    def test_message_field_is_present(self):
        formatter = GcpJsonFormatter()
        output = json.loads(formatter.format(self._make_record(msg="hello world")))
        assert output["message"] == "hello world"

    def test_logger_field_is_present(self):
        formatter = GcpJsonFormatter()
        output = json.loads(formatter.format(self._make_record()))
        assert output["logger"] == "test.logger"

    def test_traceback_included_when_exc_info_present(self):
        formatter = GcpJsonFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            import sys
            record = self._make_record(exc_info=sys.exc_info())
        output = json.loads(formatter.format(record))
        assert "traceback" in output
        assert "ValueError" in output["traceback"]

    def test_no_traceback_field_without_exception(self):
        formatter = GcpJsonFormatter()
        output = json.loads(formatter.format(self._make_record()))
        assert "traceback" not in output

    def test_stack_trace_auto_included_for_warning(self):
        formatter = GcpJsonFormatter()
        output = json.loads(formatter.format(self._make_record(level=logging.WARNING)))
        assert "stackTrace" in output

    def test_stack_trace_auto_included_for_error(self):
        formatter = GcpJsonFormatter()
        output = json.loads(formatter.format(self._make_record(level=logging.ERROR)))
        assert "stackTrace" in output

    def test_stack_trace_not_auto_included_for_info(self):
        formatter = GcpJsonFormatter()
        output = json.loads(formatter.format(self._make_record(level=logging.INFO)))
        assert "stackTrace" not in output

    def test_stack_trace_not_auto_included_for_debug(self):
        formatter = GcpJsonFormatter()
        output = json.loads(formatter.format(self._make_record(level=logging.DEBUG)))
        assert "stackTrace" not in output

    def test_stack_trace_explicit_stack_info_overrides(self):
        formatter = GcpJsonFormatter()
        record = self._make_record(level=logging.DEBUG)
        record.stack_info = "Stack (most recent call last):\n  File 'test.py', line 1, in <module>"
        output = json.loads(formatter.format(record))
        assert "stackTrace" in output
        assert "test.py" in output["stackTrace"]


class TestConfigureGcpLogging:
    def test_sets_json_formatter_on_root_logger(self):
        configure_gcp_logging()
        root = logging.getLogger()
        assert any(isinstance(h.formatter, GcpJsonFormatter) for h in root.handlers)

    def test_uses_default_log_level(self, monkeypatch):
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        configure_gcp_logging()
        assert logging.getLogger().level == logging.INFO

    def test_accepts_explicit_level(self):
        configure_gcp_logging(level=logging.DEBUG)
        assert logging.getLogger().level == logging.DEBUG

    def test_log_output_is_valid_json(self, capfd):
        configure_gcp_logging(level=logging.DEBUG)
        logging.getLogger("test.output").warning("test warning message")
        captured = capfd.readouterr()
        parsed = json.loads(captured.err)
        assert parsed["severity"] == "WARNING"
        assert parsed["message"] == "test warning message"

    def test_auto_configured_on_import_when_no_handlers(self):
        root = logging.getLogger()
        assert any(isinstance(h.formatter, GcpJsonFormatter) for h in root.handlers)

    def test_does_not_add_handlers_when_already_configured(self):
        initial_count = len(logging.getLogger().handlers)
        importlib.reload(lc)
        assert len(logging.getLogger().handlers) == initial_count
