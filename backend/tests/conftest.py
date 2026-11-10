import os
import pytest
from app.services.llm_adapter import LLMAdapter, LLMConfig


@pytest.fixture(autouse=True)
def force_mock_llm(monkeypatch):
    """Ensures offline test suite uses deterministic mock solver without making paid/network API calls."""
    monkeypatch.setenv("LLM_PROVIDER", "mock")


@pytest.fixture
def mock_adapter():
    """Provides a deterministic mock LLM adapter for offline testing."""
    return LLMAdapter(config=LLMConfig(provider="mock"))

