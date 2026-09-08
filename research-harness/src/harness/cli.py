# CLI REPL — Phase 1, P1.T3
# Read line → send → print; /quit exits; connection errors → one-line message, no traceback.

from harness.llm.client import LLMClient, LLMConnectionError


def main():
    c = LLMClient()
    while True:
        try:
            line = input("> ")
        except EOFError:
            break
        if line.strip() == "/quit":
            break
        try:
            print(c.chat(line))
        except LLMConnectionError as exc:
            print("Connection error — is the LLM server running?")


if __name__ == "__main__":
    main()
