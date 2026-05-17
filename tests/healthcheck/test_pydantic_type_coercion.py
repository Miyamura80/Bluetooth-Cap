"""
Test pydantic-settings automatic type coercion.
This ensures that environment variables (which are always strings) are properly
converted to the correct Python types as defined in the config models.
"""

import importlib
import sys


def test_pydantic_type_coercion(monkeypatch):
    """
    Test that pydantic-settings automatically coerces environment variable strings
    to the correct types (int, float, bool) as defined in the Pydantic models.
    """
    common_module = sys.modules["common.global_config"]

    # Boolean coercion tests
    monkeypatch.setenv("LOGGING__VERBOSE", "false")  # String -> bool
    monkeypatch.setenv("LOGGING__FORMAT__SHOW_TIME", "1")  # String '1' -> bool True
    monkeypatch.setenv("LOGGING__LEVELS__DEBUG", "true")  # String -> bool
    monkeypatch.setenv("LOGGING__LEVELS__INFO", "0")  # String '0' -> bool False

    # Reload the config module to pick up the new environment variables
    importlib.reload(common_module)
    config = common_module.global_config

    # Verify boolean coercion
    assert isinstance(config.logging.verbose, bool), "verbose should be bool"
    assert config.logging.verbose is False, "verbose should be False"

    assert isinstance(config.logging.format.show_time, bool), "show_time should be bool"
    assert config.logging.format.show_time is True, (
        "show_time should be True (from '1')"
    )

    assert isinstance(config.logging.levels.debug, bool), "debug should be bool"
    assert config.logging.levels.debug is True, "debug should be True"

    assert isinstance(config.logging.levels.info, bool), "info should be bool"
    assert config.logging.levels.info is False, "info should be False (from '0')"

    # Reload the original config to avoid side effects on other tests
    importlib.reload(common_module)
