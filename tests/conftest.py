"""Shared test fixtures."""

import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _set_dummy_api_keys():
    """Set dummy API keys so validation passes in unit tests."""
    os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-dummy")
    os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")
    os.environ.setdefault("DEEPSEEK_API_KEY", "test-dummy")
