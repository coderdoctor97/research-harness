"""Quick verification of api_key_env / none handling."""
import os
os.environ["TEST_KEY"] = "secret"

from harness.llm.client import LLMClient

# 1. api_key_env set, no direct api_key -> resolves from env
c = LLMClient(base_url="http://x", model_name="m", api_key_env="TEST_KEY")
assert c.api_key == "secret"

# 2. api_key_env = "none" -> no auth
c2 = LLMClient(base_url="http://x", model_name="m", api_key_env="none")
assert c2.api_key is None
assert "Authorization" not in c2._headers()

# 3. direct api_key overrides env
c3 = LLMClient(base_url="http://x", model_name="m", api_key="direct", api_key_env="TEST_KEY")
assert c3.api_key == "direct"

# 4. api_key = None + api_key_env missing -> None
c4 = LLMClient(base_url="http://x", model_name="m")
assert c4.api_key is None

print("api_key_env verification passed.")
