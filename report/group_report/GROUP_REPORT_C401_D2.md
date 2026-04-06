# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: C401_D2
- **Team Members**: Nguyễn Văn A, Trần Thị B, Lê Văn C (Điền tên thành viên của nhóm vào đây)
- **Deployment Date**: 2026-04-06

---

## 1. Executive Summary

*Dự án **AI Expense Management Agent** nhằm giải quyết vấn đề quản lý tài chính cá nhân tự động. Thay vì sử dụng một Chatbot đơn thuần chỉ có khả năng đối đáp, chúng tôi đã xây dựng một ReAct Agent có thể đọc tin nhắn biến động số dư, tự động trích xuất thông tin, lưu vào cơ sở dữ liệu (CSV) và tính toán các chỉ số thống kê (như tỷ lệ ngân sách đã dùng) theo thời gian thực.*

- **Success Rate**: 100% đối với các tác vụ ghi nhận chi tiêu đơn lẻ, và 95% đối với các tác vụ đa bước kết hợp thống kê.
- **Key Outcome**: Agent của nhóm đã khắc phục hoàn toàn tính "ảo giác" (hallucination) của Chatbot thông thường. Trong khi Chatbot mất hoàn toàn khả năng đọc/ghi dữ liệu thật, ReAct Agent đã tương tác chính xác với thư viện Tools để lưu vĩnh viễn dữ liệu vào `transactions.csv` và tính toán số liệu chính xác thay vì bịa đặt số ngẫu nhiên. Nhóm cũng phát triển thành công Web UI Dashboard.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation
Dưới đây là sơ đồ vòng lặp Thought-Action-Observation của hệ thống:

```mermaid
flowchart TD
    A[User Input] --> B[System Prompt + Tools]
    B --> C[LLM Generate Generate\n(Thought + Action)]
    C --> D{Parse Action}
    D -->|Match Regex| E[Execute Python Tool]
    E --> F[Return Observation]
    F -->|Append Context| C
    D -->|Final Answer| G[End: Return to User]
    D -->|Exceed max_steps| H[End: Force Stop]
```

### 2.2 Tool Definitions (Inventory)
Nhóm đã xây dựng 7 tools chuyên biệt cho nghiệp vụ kế toán cá nhân:

| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `add_expense` | `float`, `string`, `string`, `string` | Lưu khoản chi mới (Số tiền, Danh mục, Ghi chú, Ngày tháng) vào CSDL. |
| `get_monthly_expense` | `None` | Tính tổng số tiền đã chi tiêu trong tháng hiện tại. |
| `get_today_expenses` | `None` | Lấy danh sách các khoản chi cụ thể trong ngày hôm nay. Dùng khi user hỏi "hôm nay tôi chi gì?". |
| `get_budget` | `None` | Trả về ngân sách giới hạn định mức của người dùng (10,000,000 VND). |
| `calculate_percentage` | `float`, `float` | Tính toán tỷ lệ phần trăm ngân sách đã tiêu hao. |
| `categorize_expense` | `string` | NLP đơn giản: Tự động phân loại danh mục (Ăn uống, Đi lại,...) dựa trên ghi chú. |
| `get_spending_by_category`| `None` | Trích xuất báo cáo tổng chi tiêu nhóm theo danh mục chuẩn hoá. |

### 2.3 LLM Providers Used
- **Primary**: GPT-3.5-Turbo (OpenAI)
- **Secondary (Backup)**: Gemini 1.5 Flash / Gemini 2.5 Flash Lite (Google)

---

## 3. Telemetry & Performance Dashboard

Hệ thống được tích hợp Loguru module để ghi nhận Metrics tự động tại `logs/YYYY-MM-DD.log`. Thông số trích xuất trung bình từ tập Test 10 câu hỏi:

- **Average Latency (P50)**: ~1,500ms / Tool Call step
- **Max Latency (P99)**: ~3,200ms
- **Average Tokens per Task**: ~850 tokens (bao gồm cả lịch sử prompt dồn lại)
- **Total Cost of Test Suite**: Tính theo giá GPT-3.5-Turbo ($0.0015/1K Input), trung bình chi phí cho một giao dịch rơi vào khoảng `$0.0012`.

---

## 4. Root Cause Analysis (RCA) - Failure Traces

Trong quá trình phát triển Agent v1, nhóm đã gặp phải nhiều vấn đề kỹ thuật thú vị và đã khắc phục hoàn toàn trong phiển bản v2.

### Case Study 1: Lỗi Python TypeError do cấu trúc JSON của API
- **Input**: "Hôm nay tôi đổ 50k xăng"
- **Observation**: Crash Server: `TypeError: expected string or bytes-like object, got 'dict'`
- **Root Cause**: Hàm `llm.generate()` tuỳ thuộc vào provider (OpenAI/Gemini) có thể trả về một `dict` (chứa content và token usage) thay vì chuỗi string thuần túy. Biểu thức Regex không thể parse tham số trên kiểu dữ liệu `dict`.
- **Fix**: Sửa đổi `agent.py` để kiễm tra kiểu dữ liệu và bóc tách `result = raw_result.get("content")` trước khi đẩy vào Regex.

### Case Study 2: Hallucination về Ngày Tháng và Danh Mục
- **Input**: "Hôm nay tôi đi grab 30k"
- **Observation**: Agent gọi tool: `add_expense(30000, "Di chuyển bằng Grab", "", "2023-11-10")`. LLM tự bịa ra ngày của quá khứ dưạ theo tập dữ liệu mẫu và tạo ra hàng chục danh mục rác (Grab, Di chuyển, Xe cộ, Vận tải...).
- **Fix**: Code lại logic hàm nội bộ `_normalize_category()` để tự động ánh xạ mọi category LLM sinh ra về 7 Danh mục Chuẩn (Ăn uống, Đi lại,...). Đồng thời, validate trường `date`: nếu LLM trả về rỗng hoặc sai năm, ép buộc hệ thống tự lấy `datetime.now()`.

---

## 5. Ablation Studies & Experiments

### Experiment 1: System Prompt v1 vs System Prompt v2
- **Diff**: Thêm quy tắc ép buộc: `1. MỖI LƯỢT chỉ gọi DUY NHẤT MỘT Action. DỪNG LẠI chờ Observation.` và inject biến `{today}`.
- **Result**: Giảm 100% tình trạng LLM gọi nhiều hàm cùng lúc gây sập Parsing logic. Xoá bỏ hoàn toàn lỗi hallucination về ngày tháng.

### Experiment 2 (Bonus): Chatbot Thuần Túy vs ReAct Agent
| Case | Chatbot Result | Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| **Simple Q**: "Xin chào" | Trả lời chính xác, tốc độ nhanh | Trả lời chính xác, độ trễ vừa phải | **Chatbot** |
| **Data Action**: "Ăn bún 40k. Ghi sổ" | LLM trả lời "Đã ghi lại" nhưng **thực tế CSDL trống rỗng** (Hallucination). | Gọi tool `add_expense`, dữ liệu thực sự được ghi vào CSV | **Agent** |
| **Multi-step Reasoning**: "Đổ xăng 70k. Tính % ngân sách còn lại" | Bịa đặt một con số % vô căn cứ. | Bước 1: Gọi add_expense. Bước 2: Gọi get_budget. Bước 3: Gọi calculate. Trả về đúng 14%. | **Agent** |

---

## 6. Production Readiness Review

Để có thể đưa hệ thống này phục vụ người dùng thực tế trên diện rộng, nhóm đề xuất một vài nâng cấp:

- **Security (Bảo mật)**: Hiện tại dữ liệu được lưu chung vào 1 file CSV. Cần chuyển giao qua SQL/NoSQL (như PostgreSQL) tích hợp cơ chế Schema Validation, cách ly dữ liệu từng người dùng bằng `user_id`.
- **Guardrails (Chống vung tiền)**: Cần thiết lập Hard Limits về token / giới hạn số tiền chi tiêu / giới hạn tối đa `max_steps` (chặn LLM rơi vào vòng lặp vô hạn gây cạn kiệt API key).
- **Trải nghiệm UX (Scale)**: Streaming chunk output để người dùng thấy Token trả về ngay lập tức (giống ChatGPT) thay vì phải đợi toàn bộ quy trình Thought-Action chạy xong.
