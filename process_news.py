import os
import shutil
from datetime import datetime
import json
import glob
import sys

# Configure stdout to use utf-8 to avoid UnicodeEncodeError on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Cấu hình các đường dẫn
BASE_DIR = r"E:\Application downloads\Value"
NEW_NEWS_DIR = os.path.join(BASE_DIR, "raw", "new news")
OLD_NEWS_DIR = os.path.join(BASE_DIR, "raw", "old news")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
DB_FILE = os.path.join(BASE_DIR, "news_database.json")
DASHBOARD_FILE = os.path.join(BASE_DIR, "dashboard.html")

def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)

def load_db():
    init_db()
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def generate_dashboard(db_data):
    # Tạo HTML Dashboard
    html_template = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>News Dashboard</title>
        <style>
            :root {
                --primary: #2563eb;
                --bg: #f8fafc;
                --text: #0f172a;
                --card-bg: #ffffff;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: var(--bg);
                color: var(--text);
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 1000px;
                margin: 0 auto;
            }
            h1 {
                text-align: center;
                color: var(--primary);
                font-size: 2.5rem;
                margin-bottom: 2rem;
            }
            .news-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 20px;
            }
            .news-card {
                background: var(--card-bg);
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                transition: transform 0.2s, box-shadow 0.2s;
                display: flex;
                flex-direction: column;
            }
            .news-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 15px rgba(0,0,0,0.1);
            }
            .news-date {
                font-size: 0.85rem;
                color: #64748b;
                margin-bottom: 10px;
            }
            .news-title {
                font-size: 1.25rem;
                font-weight: 600;
                margin: 0 0 10px 0;
                color: var(--text);
            }
            .news-summary {
                font-size: 0.95rem;
                color: #475569;
                line-height: 1.5;
                flex-grow: 1;
            }
            .empty-state {
                text-align: center;
                padding: 50px;
                color: #64748b;
                grid-column: 1 / -1;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📰 News Dashboard</h1>
            <div class="news-grid">
                {cards}
            </div>
        </div>
    </body>
    </html>
    """

    cards_html = ""
    if not db_data:
        cards_html = "<div class='empty-state'>Chưa có tin tức nào được cập nhật.</div>"
    else:
        # Sắp xếp từ mới nhất đến cũ nhất
        sorted_data = sorted(db_data, key=lambda x: x['processed_at'], reverse=True)
        for item in sorted_data:
            cards_html += f"""
            <div class="news-card">
                <div class="news-date">{item['processed_at']}</div>
                <h2 class="news-title">{item['title']}</h2>
                <div class="news-summary">{item['summary']}...</div>
            </div>
            """

    final_html = html_template.replace("{cards}", cards_html)
    with open(DASHBOARD_FILE, 'w', encoding='utf-8') as f:
        f.write(final_html)

def process_news():
    db_data = load_db()
    today_str = datetime.now().strftime("%Y-%m-%d")
    report_file_path = os.path.join(REPORTS_DIR, f"report_{today_str}.md")
    
    files = glob.glob(os.path.join(NEW_NEWS_DIR, "*"))
    
    if not files:
        print("Không có tin tức mới để xử lý.")
        # Vẫn tạo lại dashboard trong trường hợp chạy lần đầu
        generate_dashboard(db_data)
        return

    new_items = []
    
    # 1. Đọc và thu thập thông tin
    for file_path in files:
        if os.path.isfile(file_path):
            filename = os.path.basename(file_path)
            title = os.path.splitext(filename)[0]
            
            summary = ""
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    # Lấy 150 ký tự đầu làm summary
                    summary = content[:150].replace('\n', ' ')
            except Exception as e:
                summary = f"Không thể đọc nội dung: {e}"
            
            processed_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            item = {
                "title": title,
                "summary": summary,
                "filename": filename,
                "processed_at": processed_time
            }
            new_items.append(item)
            db_data.append(item)
            
            # Chuyển file sang old news
            dest_path = os.path.join(OLD_NEWS_DIR, filename)
            # Xử lý trường hợp file đã tồn tại trong old news
            if os.path.exists(dest_path):
                base, ext = os.path.splitext(filename)
                dest_path = os.path.join(OLD_NEWS_DIR, f"{base}_{int(datetime.now().timestamp())}{ext}")
            
            shutil.move(file_path, dest_path)
            print(f"Đã chuyển: {filename}")

    # 2. Cập nhật báo cáo ngày
    with open(report_file_path, 'a', encoding='utf-8') as f:
        # Nếu file mới được tạo, không có dữ liệu
        if os.path.getsize(report_file_path) == 0:
            f.write(f"# Báo cáo tin tức ngày {today_str}\n\n")
        
        for item in new_items:
            f.write(f"## {item['title']}\n")
            f.write(f"**Thời gian xử lý:** {item['processed_at']}\n\n")
            f.write(f"> {item['summary']}...\n\n")
            f.write("---\n\n")
            
    print(f"Đã cập nhật báo cáo ngày: {report_file_path}")

    # 3. Lưu database
    save_db(db_data)
    
    # 4. Cập nhật Dashboard HTML
    generate_dashboard(db_data)
    print("Đã cập nhật dashboard.html")

if __name__ == "__main__":
    process_news()
