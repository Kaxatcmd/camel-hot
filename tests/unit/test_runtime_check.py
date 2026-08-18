"""Unit tests for the packaged audio runtime diagnostics."""

import importlib

from audio_analysis import runtime_check


def test_check_analysis_runtime_reports_import_failure(monkeypatch):
    original_import_module = importlib.import_module

    def failing_import(module_name):
        if module_name == "scipy":
            raise ImportError("missing scientific binary")
        return original_import_module(module_name)

    monkeypatch.setattr(runtime_check.importlib, "import_module", failing_import)

    errors = runtime_check.check_analysis_runtime()

    assert errors == ["scipy: ImportError: missing scientific binary"]