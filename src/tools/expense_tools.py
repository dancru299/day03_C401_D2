import os
import csv
from datetime import datetime
import json

DB_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'report', 'transactions.csv')

def _init_db():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['date', 'amount', 'category', 'note'])

def _read_db():
    _init_db()
    transactions = []
    with open(DB_FILE, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            transactions.append(row)
    return transactions

def add_expense(amount: float, category: str, note: str, date: str) -> str:
    """Lưu một khoản chi mới gồm số tiền, danh mục, ghi chú và thời gian."""
    _init_db()
    with open(DB_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([date, amount, category, note])
    return f"Đã lưu thành công chi phí {amount} VND cho {category} vào ngày {date}."

def get_monthly_expense() -> str:
    """Lấy tổng chi tiêu trong tháng hiện tại."""
    transactions = _read_db()
    current_month = datetime.now().strftime('%Y-%m')
    total = 0.0
    for t in transactions:
        t_date = t.get('date', '')
        if t_date.startswith(current_month):
            try:
                total += float(t.get('amount', 0))
            except ValueError:
                pass
    return f"Tổng chi trong tháng hiện tại là: {total} VND"

def get_budget() -> str:
    """Lấy ngân sách tháng của người dùng (Giả lập mặc định 10.000.000 VND)."""
    # Mặc định người dùng chi tối đa 10 triệu
    budget = 10000000.0
    return f"Ngân sách tháng định mức là {budget} VND."

def calculate_percentage(expense: float, budget: float) -> str:
    """Tính phần trăm ngân sách đã sử dụng."""
    if budget == 0:
        return "Lỗi chia cho 0. Ngân sách đang là 0."
    pct = (expense / float(budget)) * 100
    return f"Bạn đã sử dụng {pct:.2f}% ngân sách."

def categorize_expense(description: str) -> str:
    """Tự động phân loại khoản chi theo ghi chú."""
    desc = description.lower()
    if any(word in desc for word in ['ăn', 'uống', 'food', 'cà phê', 'highland', 'shopee']):
        return "Ăn uống"
    elif any(word in desc for word in ['xe', 'grab', 'gojek', 'xăng']):
        return "Đi lại"
    elif any(word in desc for word in ['phim', 'nhạc', 'chơi']):
        return "Giải trí"
    return "Khác"

def get_spending_by_category() -> str:
    """Thống kê chi tiêu theo từng danh mục."""
    transactions = _read_db()
    stats = {}
    current_month = datetime.now().strftime('%Y-%m')
    
    for t in transactions:
        if t.get('date', '').startswith(current_month):
            cat = t.get('category', 'Khác')
            amt = float(t.get('amount', 0))
            stats[cat] = stats.get(cat, 0) + amt
            
    return f"Thống kê theo danh mục: {json.dumps(stats, ensure_ascii=False)}"

# Định nghĩa giao diện Tool cho System Prompt
EXPENSE_TOOLS_MAP = [
    {
        "name": "add_expense",
        "description": "Lưu một khoản chi mới, nhận 4 tham số: amount (số thực), category (text), note (text) và date (text - 'YYYY-MM-DD')."
    },
    {
        "name": "get_monthly_expense",
        "description": "Lấy tổng chi tiêu trong tháng hiện hành. Trả về text."
    },
    {
        "name": "get_budget",
        "description": "Lấy ngân sách tháng mặc định. Trả về text."
    },
    {
        "name": "calculate_percentage",
        "description": "Tín phần trăm sử dụng. Nhận 2 tham số: expense (float) tổng tiền đã tiêu, budget (float) là ngân sách."
    },
    {
        "name": "categorize_expense",
        "description": "Gợi ý tự động danh mục dựa trên ghi chú (description). Nhận 1 tham số là description."
    },
    {
        "name": "get_spending_by_category",
        "description": "Trả về thống kê số tiền ở từng danh mục trong tháng. Không cần tham số."
    }
]

def map_tool_call(tool_name: str, args_str: str) -> str:
    """Hàm wrapper để chạy các lệnh Tool linh động từ string"""
    import ast
    try:
        # Nếu LLM trả về dạng list/tuple args. Ví dụ: (50000, 'Ăn uống', 'abc', '2023-11-10')
        if not args_str.strip():
            args = []
        elif args_str.strip().startswith('(') or args_str.strip().startswith('['):
            args = ast.literal_eval(args_str)
        else:
            # LLM có thể trả về dictionary **args
            if args_str.strip().startswith('{'):
                kwargs = ast.literal_eval(args_str)
                if tool_name == "add_expense":
                    return add_expense(**kwargs)
                elif tool_name == "calculate_percentage":
                    return calculate_percentage(**kwargs)
                elif tool_name == "categorize_expense":
                    return categorize_expense(**kwargs)
            else:
                args = [a.strip().strip("'").strip('"') for a in args_str.split(',')]
            
        if not isinstance(args, (list, tuple)):
            args = [args]
                
        if tool_name == "add_expense":
            amount = float(args[0])
            category = args[1]
            note = args[2] if len(args) > 2 else ""
            date = args[3] if len(args) > 3 else datetime.now().strftime('%Y-%m-%d')
            return add_expense(amount, category, note, date)
            
        elif tool_name == "get_monthly_expense":
            return get_monthly_expense()
            
        elif tool_name == "get_budget":
            return get_budget()
            
        elif tool_name == "calculate_percentage":
            return calculate_percentage(float(args[0]), float(args[1]))
            
        elif tool_name == "categorize_expense":
            return categorize_expense(args[0])
            
        elif tool_name == "get_spending_by_category":
            return get_spending_by_category()
            
        else:
            return f"❌ Lỗi: Tool '{tool_name}' không tồn tại!"
    except Exception as e:
        return f"❌ Lỗi thực thi Tool {tool_name} với tham số '{args_str}': {e}"
