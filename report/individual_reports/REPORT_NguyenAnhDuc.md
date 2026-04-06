# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Anh Đức
- **Role**: Lead Agentic Developer
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

Vai trò của em là thiết kế và xây dựng vòng lặp tư duy ReAct (Thought-Action-Observation) cốt lõi tại file `src/agent/agent.py`. Em chịu trách nhiệm Regex parsing để lấy lệnh từ LLM và luân chuyển dữ liệu với Tools. 

- **Modules Implemented**: `src/agent/agent.py`
- **Code Highlights**:
```python
# Sửa lỗi mô hình Open Source cứng đầu sinh ra Action: None
elif "Action: None" in result or "Action: none" in result:
    thought_match = re.search(r"Thought:\s*(.*?)(Action:|$)", result, re.DOTALL | re.IGNORECASE)
    if thought_match:
        final_answer = thought_match.group(1).strip()
```
- **Documentation**: Hệ thống trích xuất chuỗi đầu ra từ LLM bằng regular expression, sau đó gửi tới module trung gian `map_tool_call()`. Quá trình này đòi hỏi hàm logic chặt chẽ để LLM không bị ngắt quãng giữa chừng khi parse lỗi.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Server liên tục Crash với lỗi `TypeError: expected string or bytes-like object, got 'dict'` khi Agent mới bắt đầu chạy và nhận phản hồi đầu tiên. Ngoài ra, khi chuyển sang dùng LLM Ollama Local, mô hình lại trả về chuỗi `Action: None` gây rác giao diện chat.
- **Diagnosis**: 
  1. API `llm.generate()` do thư viện nội bộ trả về một Dict chứa cả thông số Token chứ không phải là String thuần. Dẫn đến hàm `re.search()` bị sụp đổ.
  2. Các mô hình OS khá "cứng nhắc" với template, thường khăng khăng dùng format cũ thay vì trả về `Final Answer:`.
- **Solution**: Trích xuất lấy content thực trước: `result = raw_result.get("content", "")`. Đồng thời, bổ sung một luồng bắt exception `elif "Action: None"` để cưỡng ép lấy Thought hiện tại chuyển thành Final Answer.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: Nhờ block `Thought`, Agent giống như có một "giấy nháp" để phân tích xem user đang yêu cầu những gì, thiếu tham số nào để truyền vào Tool, do đó độ vấp váp giảm đi đáng kể.
2. **Reliability**: Chatbot sẽ nói dối 100% trong tác vụ tương tác phần mềm (phiên bản baseline báo cáo là "đã ghi sổ" dù không chạy một dòng lệnh io lưu file nào).
3. **Observation**: Rất thường xuyên, Observation sinh ra thông báo lỗi (như "Tool không tồn tại"). Nhờ ReAct loop, LLM tự động nhìn thấy lỗi này và thay đổi lệnh gọi (self-correction) liên tiếp cho tới khi được.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Thay vì Regular Expression truyền thống dễ gặp lỗi lặt vặt (như sai dấu phẩy, thiếu ngoặc kép), nâng cấp LLM lên khả năng Structure Data Output (JSON Mode/Function Calling của mô hình tân tiến).
- **Safety**: Bổ sung bộ lọc reflection - trước khi thực hiện các Action "nguy hiểm" như xoá hay chuyển tiền thật, Agent cần gọi prompt xác nhận (Confirmation Prompt) nội bộ.
- **Performance**: Thiết kế Streaming Generator để gửi từng token "Suy nghĩ..." xuống client thay vì bắt UI chờ 3-5 giây đóng băng.
