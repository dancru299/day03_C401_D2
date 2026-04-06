import os
from dotenv import load_dotenv
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider

def run_baseline():
    load_dotenv()
    provider_name = os.getenv("DEFAULT_PROVIDER", "openai").lower()
    
    print(f"🤖 Khởi động CHATBOT BASELINE (Không có Tools - Provider: {provider_name})")
    print("=" * 60)

    # 1. Khởi tạo LLM
    try:
        if provider_name == "openai":
            if not os.getenv("OPENAI_API_KEY"):
                print("❌ Lỗi: Bạn chưa điền OPENAI_API_KEY trong file .env")
                return
            llm = OpenAIProvider(model_name="gpt-3.5-turbo")
        elif provider_name == "gemini":
            if not os.getenv("GEMINI_API_KEY"):
                print("❌ Lỗi: Bạn chưa điền GEMINI_API_KEY trong file .env")
                return
            llm = GeminiProvider(model_name="gemini-1.5-flash")
        else:
            print("❌ Lỗi: Provider không hợp lệ. Chọn openai hoặc gemini trong .env")
            return
    except Exception as e:
        print(f"❌ Lỗi khởi tạo Provider: {e}")
        return

    # 2. Test cases: Gửi tin nhắn biến động ngân hàng cho Chatbot KHÔNG có Tool
    test_cases = [
        "Hôm nay tôi đổ 50k xăng và làm ly trà sữa 35k. Ghi vào sổ chi tiêu giúp tôi và tính xem tôi đã tiêu hết bao nhiêu % ngân sách tháng chưa.",
        "Tôi vừa mua đồ ăn ShopeeFood 85k. Tháng này tôi có ngân sách 10 triệu. Tôi đã tiêu hết bao nhiêu rồi?",
    ]

    for i, prompt in enumerate(test_cases, 1):
        print(f"\n📌 TEST CASE {i}:")
        print(f"👤 User: {prompt}")
        print(f"\n🤖 Chatbot Baseline trả lời:")
        
        try:
            raw_result = llm.generate(prompt)
            # Bóc tách content từ dict response
            if isinstance(raw_result, dict):
                content = raw_result.get("content", "")
                usage = raw_result.get("usage", {})
                print(content)
                print(f"\n📊 [Telemetry] Tokens: {usage}")
            else:
                print(str(raw_result))
        except Exception as e:
            print(f"❌ Lỗi gọi API: {e}")

        print("\n" + "-" * 60)
        print("🔍 NHẬN XÉT (Phase 1 - Baseline Limitation):")
        print("  - Chatbot có thể HIỂU câu hỏi nhưng KHÔNG THỂ thực sự lưu dữ liệu.")
        print("  - Chatbot sẽ 'ảo giác' (hallucinate) là đã lưu hoặc đưa ra số liệu bịa đặt.")
        print("  - Không có file transactions.csv nào được tạo ra.")
        print("  => Cần ReAct Agent + Tools để giải quyết thực sự!")
        print("=" * 60)

if __name__ == "__main__":
    run_baseline()
