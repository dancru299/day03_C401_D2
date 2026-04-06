import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.ollama_provider import OllamaProvider


def test_ollama_provider():
    load_dotenv()
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct-q3_k_L").strip()

    print("--- Testing Ollama Provider ---")
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")

    if not base_url:
        print("❌ Error: OLLAMA_BASE_URL is missing in .env")
        return

    if not model:
        print("❌ Error: OLLAMA_MODEL is missing in .env")
        return

    try:
        provider = OllamaProvider(model_name=model, base_url=base_url)

        prompt = "Explain what an AI Agent is in one sentence."
        print(f"\nUser: {prompt}")
        print("Assistant: ", end="", flush=True)

        for chunk in provider.stream(prompt):
            print(chunk, end="", flush=True)
        print("\n\n✅ Ollama Provider is working correctly!")

    except Exception as e:
        print(f"\n❌ Error during execution: {e}")


if __name__ == "__main__":
    test_ollama_provider()
