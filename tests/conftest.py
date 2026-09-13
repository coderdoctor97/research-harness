"""Conftest — shared pytest fixtures."""
# Point persisted UI state at a throwaway file BEFORE any harness import,
# so tests never touch (or reload) the real .harness-state.json.
import os
import tempfile

_TEST_STATE = os.path.join(tempfile.gettempdir(), "harness-test-state.json")
os.environ["HARNESS_STATE_FILE"] = _TEST_STATE
try:
    os.remove(_TEST_STATE)
except OSError:
    pass
