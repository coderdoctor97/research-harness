# Config tests — P2.T6 / P1.T6 integration
from harness.config import load_config


def test_load_has_keys():
    cfg = load_config()
    assert cfg.base_url is not None
    assert cfg.model_name is not None
