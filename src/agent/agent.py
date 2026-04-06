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
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""
Bạn là một trợ lý AI quản lý chi tiêu (AI Expense Management Agent). 
Nhiệm vụ của bạn là lấy thông tin từ báo cáo của người dùng và gọi các lệnh thích hợp trên hệ thống.
Bạn có quyền truy cập vào các công cụ (Tools) sau:

{tool_descriptions}

LUÔN LUÔN VÀ BẮT BUỘC trả lời THEO CHUẨN FORMAT sau:
Thought: (Suy nghĩ của bạn về việc phải làm gì tiếp theo, hoặc mục tiêu cần hoàn thành)
Action: (Tên Tool muốn gọi, nối liền với ngoặc đơn chứa tham số). Ví dụ: get_budget() hoặc categorize_expense("Ăn uống") hoặc add_expense(50000, "Ăn uống", "Highland", "2023-11-10"). Quan trọng: Tham số chữ phải có dấu ngoặc kép.
Observation: (Hệ thống sẽ trả lại Observation cho bạn. BẠN KHÔNG TỰ TẠO RA OBSERVATION).

Lặp lại Thought/Action/Observation cho tới khi bạn hoàn thành nghiệp vụ.
Khi đã hoàn thành, hoặc nếu người dùng chỉ hỏi bâng quơ không liên quan chi tiêu, BẮT BUỘC kết thúc theo format:
Final Answer: câu trả lời tiếng Việt cuối cùng dành cho người dùng.
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
