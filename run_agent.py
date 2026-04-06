import os
from dotenv import load_dotenv
import sys
import io

# Force UTF-8 encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider
from src.agent.agent import ReActAgent
from src.tools.expense_tools import EXPENSE_TOOLS_MAP
from loguru import logger

def run_agent_test():
    load_dotenv()
    provider_name = os.getenv("DEFAULT_PROVIDER", "openai").lower()
    
    print(f"🚀 Khởi động ReAct Agent (AI Expense Manager - {provider_name})")
    
    # 1. Khởi tạo LLM
    if provider_name == "openai":
        llm = OpenAIProvider(model_name="gpt-3.5-turbo")
    elif provider_name == "gemini":
        llm = GeminiProvider(model_name="gemini-2.5-flash-lite")
    else:
        print("Vui lòng chọn provider openai hoặc gemini.")
        return

    # 2. Gắn Tool vào Agent
    agent = ReActAgent(llm=llm, tools=EXPENSE_TOOLS_MAP, max_steps=6)

    # 3. Test case thực tế
    print("\n--- TEST CASE ---")
    test_message = "Tháng này tôi tiêu hết bao nhiêu rồi?"
    logger.info(f"\n👤 Bạn: {test_message}")
    
    print("\n" + "="*50)
    final_response = agent.run(test_message)
    print("="*50)
    
    logger.info("\n🤖 [FINAL ANSWER] Chatbot trả lời:\n: {final_response}")

if __name__ == "__main__":
    run_agent_test()
