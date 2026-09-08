# Minimal config loader — P1.T4
import os


def load():
    return {
        "base_url": os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434/v1"),
        "model_name": os.getenv("LOCAL_LLM_MODEL", "llama3"),
        "api_key_env": os.getenv("API_KEY_ENV", "none"),
    }
