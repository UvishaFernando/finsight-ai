"""
Shared pytest configuration.

Each test file manages its own DB override inside its own autouse fixture.
This conftest simply ensures overrides are cleared between files so there
is no cross-contamination when running the full suite together.
"""
import pytest
from app.main import app


@pytest.fixture(scope="function", autouse=True)
def clear_overrides_after_test():
    """
    Runs after every test. Clears FastAPI dependency overrides so
    the next test always starts with a clean override state.
    Each test file re-registers its own DB override in its own fixture.
    """
    yield
    app.dependency_overrides.clear()
