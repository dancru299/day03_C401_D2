import os
import re
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

class ReActAgent:
    """
    ReAct-style Agent that follows the Thought-Action-Observation loop.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        """
        Implement the system prompt that instructs the agent to follow ReAct format.
        """
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""
Bạn là một trợ lý AI quản lý chi tiêu (AI Expense Management Agent).
Nhiệm vụ của bạn là lấy thông tin từ báo cáo của người dùng và gọi các lệnh thích hợp trên hệ thống.

NGÀY HÔM NAY LÀ: {today}
Khi người dùng nói "hôm nay", "chiều nay", "sáng nay",... luôn dùng ngày: {today}

CÁC DANH MỤC CHUẨN (chỉ dùng đúng các tên này): Ăn uống, Đi lại, Mua sắm, Giải trí, Giáo dục, Hoá đơn, Sức khoẻ, Khác

Bạn có quyền truy cập vào các công cụ (Tools) sau:
{tool_descriptions}

QUY TẮC QUAN TRỌNG:
1. MỖI LƯỢT chỉ gọi DUY NHẤT MỘT Action. KHÔNG BAO GIỜ gọi nhiều Action cùng lúc.
2. Sau mỗi Action, DỪNG LẠI chờ Observation từ hệ thống rồi mới tiếp tục.
3. BẠN KHÔNG TỰ TẠO RA Observation. Hệ thống sẽ cung cấp Observation.
4. Khi người dùng hỏi "hôm nay/chiều nay có chi gì không", hãy dùng get_today_expenses().
5. Khi ghi khoản chi, luôn truyền date="{today}" hoặc date="" để hệ thống tự lấy.
6. Khi người dùng hỏi tổng chi tiêu, hãy dùng get_monthly_expense() để lấy CON SỐ THỰC TẾ, KHÔNG tự bịa.
7. TUYỆT ĐỐI KHÔNG được ghi "Action: None". NẾU KHÔNG CẦN DÙNG TOOL NỮA, BẮT BUỘC dùng từ khoá "Final Answer: " để trả lời.

FORMAT BẮT BUỘC:
Thought: (Suy nghĩ về bước tiếp theo)
Action: tool_name(tham_số)

Ví dụ:
Action: add_expense(50000, "Ăn uống", "Phở bò", "{today}")
Action: get_today_expenses()
Action: get_monthly_expense()

Khi hoàn thành, kết thúc bằng:
Final Answer: câu trả lời tiếng Việt cho người dùng.
"""

    def run(self, user_input: str) -> str:
        """
        ReAct loop logic:
        1. Generate Thought + Action.
        2. Parse Action and execute Tool.
        3. Append Observation to prompt and repeat until Final Answer.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        
        # History string
        current_prompt = f"User: {user_input}\n"
        steps = 0
        final_answer = None

        while steps < self.max_steps:
            # Sinh suy luận
            print(f"\n[Agent Step {steps+1}] Suy nghĩ...")
            
            raw_result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
            
            # raw_result là dict {"content": "...", "usage": {...}, ...}
            # Cần bóc tách phần text thực sự để xử lý
            if isinstance(raw_result, dict):
                result = raw_result.get("content", "")
                usage = raw_result.get("usage", {})
                latency = raw_result.get("latency_ms", 0)
                logger.log_event("LLM_RESPONSE", {"usage": usage, "latency_ms": latency})
            else:
                result = str(raw_result)
            
            print(f"-- LLM RAW -->\n{result}\n<------------")
            current_prompt += f"{result}\n"
            
            # Phân tích Action từ kết quả (Dùng regex tìm dòng Action: func_name(...))
            action_match = re.search(r"Action:\s*([a-zA-Z0-9_]+)\((.*)\)", result, re.IGNORECASE)
            
            if action_match:
                tool_name = action_match.group(1).strip()
                args_str = action_match.group(2).strip()
                
                print(f"[Run Tool] {tool_name}({args_str})")
                
                # Chạy thực tế Tool
                obs_result = self._execute_tool(tool_name, args_str)
                print(f"[Observation] {obs_result}")
                
                observation_line = f"Observation: {obs_result}\n"
                current_prompt += observation_line
                
            elif "Final Answer:" in result:
                # Nếu đã có Final Answer -> Thoát loop
                ans_match = re.search(r"Final Answer:\s*(.*)", result, re.DOTALL | re.IGNORECASE)
                if ans_match:
                    final_answer = ans_match.group(1).strip()
                else:
                    final_answer = result.split("Final Answer:")[-1].strip()
                break
                
            elif "Action: None" in result or "Action: none" in result:
                # Bắt lỗi khi LLM Open Source lỡ sinh ra Action: None
                thought_match = re.search(r"Thought:\s*(.*?)(Action:|$)", result, re.DOTALL | re.IGNORECASE)
                if thought_match:
                    final_answer = thought_match.group(1).strip()
                else:
                    final_answer = result.replace("Action: None", "").strip()
                break

            else:
                # LLM trả lời tùy tiện không lọt Form -> Gắn Final Answer luôn
                final_answer = result
                break

            steps += 1
            
        logger.log_event("AGENT_END", {"steps": steps})
        return final_answer if final_answer else "Cảnh báo: Agent đã chạm đến giới hạn Max Steps mà chưa chốt câu trả lời."

    def _execute_tool(self, tool_name: str, args_str: str) -> str:
        """
        Helper method to map requested string to actual code tool execution.
        """
        # Xác minh công cụ có trong tools được cấp phép ở constructor ko
        is_tool_allowed = False
        for t in self.tools:
            if t['name'] == tool_name:
                is_tool_allowed = True
                break
                
        if not is_tool_allowed:
            return f"❌ Tool '{tool_name}' không được cho phép hoặc không tồn tại."
            
        from src.tools.expense_tools import map_tool_call
        return map_tool_call(tool_name, args_str)
