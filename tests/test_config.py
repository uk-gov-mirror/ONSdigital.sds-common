"""Tests for config helpers and Config class."""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from sds_common.config.config import Config, _LazyConfigProxy, get_config
from sds_common.config.config_helpers import ConfigHelpers
from sds_common.models.config_errors import EnvironmentVariableError


class TestConfigHelpers:
    def test_can_cast_to_bool_true(self):
        assert ConfigHelpers.can_cast_to_bool("true") is True
        assert ConfigHelpers.can_cast_to_bool("True") is True
        assert ConfigHelpers.can_cast_to_bool("TRUE") is True

    def test_can_cast_to_bool_false(self):
        assert ConfigHelpers.can_cast_to_bool("false") is True
        assert ConfigHelpers.can_cast_to_bool("False") is True

    def test_can_cast_to_bool_non_bool(self):
        assert ConfigHelpers.can_cast_to_bool("hello") is False
        assert ConfigHelpers.can_cast_to_bool("1") is False

    def test_get_bool_value_true(self):
        assert ConfigHelpers.get_bool_value("true") is True
        assert ConfigHelpers.get_bool_value("TRUE") is True

    def test_get_bool_value_false(self):
        assert ConfigHelpers.get_bool_value("false") is False
        assert ConfigHelpers.get_bool_value("something") is False

    def test_format_value_returns_bool_for_bool_string(self):
        assert ConfigHelpers.format_value("true") is True
        assert ConfigHelpers.format_value("false") is False

    def test_format_value_returns_string_for_non_bool(self):
        assert ConfigHelpers.format_value("hello") == "hello"

    def test_get_value_from_env_reads_set_variable(self):
        with patch.dict(os.environ, {"MY_VAR": "my_value"}):
            assert ConfigHelpers.get_value_from_env("MY_VAR") == "my_value"

    def test_get_value_from_env_returns_default_when_not_set(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MISSING_VAR", None)
            assert ConfigHelpers.get_value_from_env("MISSING_VAR", "default") == "default"

    def test_get_value_from_env_raises_when_not_set_and_no_default(self):
        from sds_common.models.config_errors import EnvironmentVariableError
        os.environ.pop("MISSING_VAR_2", None)
        with pytest.raises(EnvironmentVariableError) as exc_info:
            ConfigHelpers.get_value_from_env("MISSING_VAR_2")
        assert exc_info.value.variable_name == "MISSING_VAR_2"
        assert "MISSING_VAR_2" in str(exc_info.value)

    def test_get_value_from_env_converts_bool_strings(self):
        with patch.dict(os.environ, {"FLAG": "true"}):
            assert ConfigHelpers.get_value_from_env("FLAG") is True


class TestConfig:
    def test_config_reads_env_on_instantiation(self):
        with patch.dict(os.environ, {"PROJECT_ID": "my-project", "SDS_URL": "https://example.com", "SDS_LOADER_URL": "https://loader.test"}):
            cfg = Config()
        assert cfg.PROJECT_ID == "my-project"
        assert cfg.SDS_URL == "https://example.com"

    def test_config_raises_when_sds_url_not_set(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SDS_URL", None)
            os.environ.pop("SDS_LOADER_URL", None)
            with pytest.raises(EnvironmentVariableError):
                Config()

    def test_config_uses_defaults_when_env_not_set(self, base_config):
        assert base_config.PROJECT_ID == "test-project"
        assert base_config.SECRET_ID == "test-secret"

    def test_config_process_timeout_is_int(self, base_config):
        assert isinstance(base_config.PROCESS_TIMEOUT, int)
        assert base_config.PROCESS_TIMEOUT == 60

    def test_config_firestore_db_name_derived_from_project_id(self):
        with patch.dict(os.environ, {"PROJECT_ID": "proj-x", "SDS_URL": "https://sds.test", "SDS_LOADER_URL": "https://loader.test"}, clear=False):
            os.environ.pop("FIRESTORE_DB_NAME", None)
            cfg = Config()
        assert cfg.FIRESTORE_DB_NAME == "proj-x-sds"

    def test_config_bucket_names_derived_from_project_id(self):
        with patch.dict(os.environ, {"PROJECT_ID": "proj-x", "SDS_URL": "https://sds.test", "SDS_LOADER_URL": "https://loader.test"}, clear=False):
            for key in ("SCHEMA_BUCKET_NAME", "SCHEMA_STAGING_BUCKET_NAME", "DATASET_BUCKET_NAME"):
                os.environ.pop(key, None)
            cfg = Config()
        assert "proj-x" in cfg.SCHEMA_PUBLISH_BUCKET_NAME
        assert "proj-x" in cfg.DATASET_BUCKET_NAME

    def test_get_config_is_cached(self, base_config):
        get_config.cache_clear()
        c1 = get_config()
        c2 = get_config()
        assert c1 is c2

    def test_lazy_proxy_delegates_attribute(self, base_config):
        proxy = _LazyConfigProxy()
        # The proxy delegates to get_config(); just verify it has PROJECT_ID
        assert hasattr(proxy, "PROJECT_ID")

    def test_lazy_proxy_repr(self, base_config):
        proxy = _LazyConfigProxy()
        assert "Config" in repr(proxy)


class TestLazyConfigProxyDir:
    def test_dir_includes_config_attributes(self, base_config):
        proxy = _LazyConfigProxy()
        attrs = dir(proxy)
        assert "PROJECT_ID" in attrs
        assert "SDS_URL" in attrs


class TestGetLogLevel:
    def test_returns_info_by_default(self):
        import logging
        import os
        from sds_common.config.logging_config import get_log_level
        os.environ.pop("LOG_LEVEL", None)
        assert get_log_level() == logging.INFO

    def test_returns_debug_when_set(self):
        import logging
        from sds_common.config.logging_config import get_log_level
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            assert get_log_level() == logging.DEBUG
