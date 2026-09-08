# Config tests — P2.T6 / P1.T6 integration
from harness.config import load

def test_load_has_keys():
    cfg = load()
    assert "base_url" in cfg
    assert "model_name" in cfg
