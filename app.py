import os
import sys
import json
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider
from src.core.ollama_provider import OllamaProvider
from src.agent.agent import ReActAgent
from src.tools.expense_tools import EXPENSE_TOOLS_MAP, get_monthly_expense, get_budget, get_spending_by_category, get_today_expenses

app = Flask(__name__, static_folder="ui/static", template_folder="ui")

# Khởi tạo Agent một lần khi server start
provider_name = os.getenv("DEFAULT_PROVIDER", "openai").lower()
if provider_name == "openai":
    llm = OpenAIProvider(model_name="gpt-3.5-turbo")
elif provider_name == "gemini":
    llm = GeminiProvider(model_name="gemini-1.5-flash")
elif provider_name == "ollama":
    llm = OllamaProvider(   model_name=os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct-q3_k_L").strip(),
                         base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip())
else:
    llm = OpenAIProvider(model_name="gpt-3.5-turbo")

agent = ReActAgent(llm=llm, tools=EXPENSE_TOOLS_MAP, max_steps=6)

@app.route("/")
def index():
    return send_from_directory("ui", "index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Tin nhắn trống"}), 400
    try:
        response = agent.run(user_message)
        return jsonify({"reply": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/stats", methods=["GET"])
def stats():
    """Trả về dữ liệu thống kê chi tiêu cho sidebar"""
    try:
        monthly_raw = get_monthly_expense()
        # Bóc tách số từ string "Tổng chi trong tháng hiện tại là: 85000.0 VND"
        import re
        nums = re.findall(r"[\d.]+", monthly_raw)
        monthly_total = float(nums[0]) if nums else 0.0

        budget_raw = get_budget()
        nums = re.findall(r"[\d.]+", budget_raw)
        budget = float(nums[0]) if nums else 10000000.0

        pct = (monthly_total / budget * 100) if budget > 0 else 0

        category_raw = get_spending_by_category()
        # category_raw là string JSON-like: "Thống kê theo danh mục: {...}"
        cat_match = re.search(r"\{.*\}", category_raw)
        categories = json.loads(cat_match.group()) if cat_match else {}

        return jsonify({
            "monthly_total": monthly_total,
            "budget": budget,
            "percentage": round(pct, 1),
            "categories": categories
        })
    except Exception as e:
        return jsonify({"monthly_total": 0, "budget": 10000000, "percentage": 0, "categories": {}, "error": str(e)})

if __name__ == "__main__":
    print("🚀 Mở trình duyệt vào: http://localhost:5000")
    app.run(debug=True, port=5000)
