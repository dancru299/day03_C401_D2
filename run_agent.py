import os
from dotenv import load_dotenv
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider
from src.agent.agent import ReActAgent
from src.tools.expense_tools import EXPENSE_TOOLS_MAP

def run_agent_test():
    load_dotenv()
    provider_name = os.getenv("DEFAULT_PROVIDER", "openai").lower()
    
    print(f"🚀 Khởi động ReAct Agent (AI Expense Manager - {provider_name})")
    
    # 1. Khởi tạo LLM
    if provider_name == "openai":
        llm = OpenAIProvider(model_name="gpt-3.5-turbo")
    elif provider_name == "gemini":
        llm = GeminiProvider(model_name="gemini-1.5-flash")
    else:
        print("Vui lòng chọn provider openai hoặc gemini.")
        return

    # 2. Gắn Tool vào Agent
    agent = ReActAgent(llm=llm, tools=EXPENSE_TOOLS_MAP, max_steps=6)

    # 3. Test case thực tế
    print("\n--- TEST CASE ---")
    test_message = "Hôm nay tôi đổ 50k xăng và làm ly trà sữa 35k. Ghi sổ vào hôm nay 2026-04-06 nhé. Tính xem tôi tiêu hết % ngân sách chưa."
    print(f"\n👤 Bạn: {test_message}")
    
    print("\n" + "="*50)
    final_response = agent.run(test_message)
    print("="*50)
    
    print("\n🤖 [FINAL ANSWER] Chatbot trả lời:\n")
    print(final_response)
    print("\n✅ Vui lòng kiểm tra file report/transactions.csv để xem dữ liệu đã được ghi sổ chưa!")

if __name__ == "__main__":
    run_agent_test()
