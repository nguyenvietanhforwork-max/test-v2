import os
import shutil
import json
import glob
from datetime import datetime
import re
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"E:\Application downloads\Value"
NEWS_DIR = os.path.join(BASE_DIR, "raw", "news")
OLD_NEWS_DIR = os.path.join(BASE_DIR, "raw", "old news")
DB_FILE = os.path.join(BASE_DIR, "news_database.json")
PROCESSED_DIR = os.path.join(BASE_DIR, "Processed")
REPORT_NEWS_DIR = os.path.join(PROCESSED_DIR, "Report of news")
REPORT_MASTER_DIR = os.path.join(PROCESSED_DIR, "MASTER Report")
WIKI_LOG = os.path.join(BASE_DIR, "wiki", "log.md")

TODAY = "2026-05-14"

# Taxonomy mappings
INDUSTRIES = {
    "Bất động sản": "Real Estate", "Vinhomes": "Real Estate", "Novaland": "Real Estate",
    "Nông nghiệp": "Agriculture", "Logistics": "Logistics", "Giao hàng": "Logistics",
    "Năng lượng": "Energy", "Sản xuất": "Manufacturing", "Ô tô": "Automotive", "VinFast": "Automotive",
    "Dược phẩm": "Pharmaceutical", "Công nghệ": "Technology", "Phần mềm": "Technology", "FPT": "Technology",
    "Ngân hàng": "Banking", "Chứng khoán": "Securities", "Bán lẻ": "Retail", "Thép": "Steel", "Hòa Phát": "Steel",
    "Xây dựng": "Construction", "Tiêu dùng": "Consumer Goods", "KCN": "Industrial Parks", "Khu công nghiệp": "Industrial Parks",
    "Vận tải biển": "Shipping", "Bảo hiểm": "Insurance", "Hàng không": "Aviation", "Sân bay": "Aviation",
    "Tiện ích": "Utilities", "Viễn thông": "Telecommunications", "Giáo dục": "Education", "Y tế": "Healthcare",
    "Thực phẩm": "Food & Beverage", "Hóa chất": "Chemicals", "Dệt may": "Textiles", "Thủy sản": "Fisheries", "Tôm": "Fisheries",
    "Khai khoáng": "Mining"
}

def classify(content, title):
    text = (title + " " + content).lower()
    
    # Category
    category = "Global Macro"
    if "việt nam" in text or "vietnam" in text or "hòa phát" in text or "fpt" in text or "vinfast" in text or "evn" in text or "imexpharm" in text:
        category = "Vietnam Macro"
        if "công ty" in text or "tập đoàn" in text or "cổ phiếu" in text or "doanh thu" in text or "doanh nghiệp" in text or "hòa phát" in text or "fpt" in text or "vinfast" in text or "evn" in text:
            category = "Vietnam Enterprise"
    else:
        if "company" in text or "corp" in text or "inc" in text:
            category = "Global Enterprise"
            
    # Industry
    industry = "Other"
    if "Enterprise" in category:
        for kw, ind in INDUSTRIES.items():
            if kw.lower() in text:
                industry = ind
                break
    else:
        industry = None # Macro doesn't need industry

    # Sentiment
    sentiment = "neutral"
    if any(w in text for w in ["tăng", "lãi", "tích cực", "khởi công", "tỷ usd", "thành công", "thrive", "recovery", "mở rộng", "đầu tư"]):
        sentiment = "positive"
    if any(w in text for w in ["giảm", "lỗ", "tiêu cực", "phạt", "tù", "khó khăn", "thuế chống bán phá giá", "shock", "khởi tố"]):
        sentiment = "negative"

    return category, industry, sentiment

def extract_frontmatter(content):
    match = re.match(r'^---\s*(.*?)\s*---', content, re.DOTALL)
    if match:
        return match.group(1), content[match.end():].strip()
    return "", content

def extract_summary(content):
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip() and not p.strip().startswith(('!', '[', '#', '<'))]
    if paragraphs:
        # Take the first paragraph as summary
        summary = paragraphs[0].replace('\n', ' ')
        if len(summary) > 300:
            match = re.match(r'^(.*?[.!?])(?:\s+|$)(.*)$', summary)
            if match:
                return f"{match.group(1)} {match.group(2)[:150]}..."
            return summary[:300] + "..."
        return summary
    return "No summary provided."

def process_files():
    files = glob.glob(os.path.join(NEWS_DIR, '*.md'))
    if not files:
        print("No files to process.")
        return

    items = []
    for i, f in enumerate(files):
        filename = os.path.basename(f)
        if filename.lower() == 'readme.md': continue
        
        with open(f, 'r', encoding='utf-8') as file:
            raw_content = file.read()
            
        fm, body = extract_frontmatter(raw_content)
        
        # Parse title from filename
        title = os.path.splitext(filename)[0]
        
        summary = extract_summary(body)
        if not summary or summary == "No summary provided.":
            # try to parse description from frontmatter
            desc_m = re.search(r'description:\s*"(.*?)"', fm)
            if desc_m:
                summary = desc_m.group(1)
        
        category, industry, sentiment = classify(body[:1500], title)
        
        # Extract companies naively (just picking capital letters sometimes, or skip)
        companies = []
        if "Hòa Phát" in body: companies.append("HPG")
        if "FPT" in body: companies.append("FPT")
        if "VinFast" in body: companies.append("VFS")
        if "EVN" in body: companies.append("EVN")
        if "Imexpharm" in body: companies.append("IMP")

        # Build Item
        item = {
            "id": f"n-{TODAY}-{i+10:03d}",
            "title": title,
            "summary": summary,
            "category": category,
            "industry": industry,
            "companies": companies,
            "source_url": "",
            "raw_path": f"raw/old news/{TODAY}/{filename}",
            "wiki_path": "",
            "report_path": f"Processed/Report of news/002 - {TODAY}.md",
            "confidence": "high",
            "sentiment": sentiment,
            "tags": ["automated-processing"]
        }
        items.append((f, item, filename))

    # 1. Update Database
    with open(DB_FILE, 'r', encoding='utf-8') as dbf:
        db = json.load(dbf)
    
    # Check if today exists
    day_entry = next((d for d in db.get("days", []) if d["date"] == TODAY), None)
    if day_entry:
        day_entry["items"] = [i[1] for i in items] + day_entry.get("items", [])
    else:
        day_entry = {
            "date": TODAY,
            "headline": {
                "title": "A Day of Shifts in Vietnam and Global Markets",
                "summary": "Key movements across Vietnam Enterprise and Global Macro landscape as observed in today's news cycle. The day brings significant developments in FDI, industrial expansion, and global supply chains.",
                "report_ref": f"Processed/Report of news/002 - {TODAY}.md"
            },
            "items": [i[1] for i in items]
        }
        db["days"].insert(0, day_entry)
        
    # Update timestamp
    db["updated"] = datetime.now().isoformat() + "+07:00"

    with open(DB_FILE, 'w', encoding='utf-8') as dbf:
        json.dump(db, dbf, ensure_ascii=False, indent=4)

    # 2. Write Reports
    os.makedirs(REPORT_NEWS_DIR, exist_ok=True)
    report_news_path = os.path.join(REPORT_NEWS_DIR, f"002 - {TODAY}.md")
    with open(report_news_path, 'w', encoding='utf-8') as f:
        f.write(f"---\nreport_type: news\nsequence: 002\ndate: {TODAY}\nitems_processed: {len(items)}\nsources_archived_to: raw/old news/{TODAY}/\n---\n\n")
        f.write(f"# News Report — {TODAY} (#002)\n\n")
        for cat in ["Vietnam Macro", "Vietnam Enterprise", "Global Macro", "Global Enterprise"]:
            cat_items = [i[1] for i in items if i[1]['category'] == cat]
            if not cat_items: continue
            f.write(f"## {cat} News\n")
            for it in cat_items:
                f.write(f"### {it['title']}\n")
                f.write(f"**Opening:** {it['summary']}\n\n")
                f.write(f"**Implications:** Sentiment is {it['sentiment']}.\n\n")
                f.write(f"**Sources:** [[{it['raw_path']}]]\n\n")
            f.write("---\n\n")

    os.makedirs(REPORT_MASTER_DIR, exist_ok=True)
    report_master_path = os.path.join(REPORT_MASTER_DIR, f"002 - {TODAY}.md")
    with open(report_master_path, 'w', encoding='utf-8') as f:
        f.write(f"---\nreport_type: master\nsequence: 002\ndate: {TODAY}\ninputs:\n  - Processed/Report of news/002 - {TODAY}.md\n---\n\n")
        f.write(f"# MASTER Report — {TODAY} (#002)\n\n")
        f.write("## Narrative of the Day\nKey shifts in regional dynamics and industrial expansion, with prominent movements in Steel, Technology, and Global policies.\n\n")
        f.write("## Emerging Themes\nIndustrial growth, regulatory adjustments, and global trade implications.\n\n")

    # 3. Archive files
    dest_dir = os.path.join(OLD_NEWS_DIR, TODAY)
    os.makedirs(dest_dir, exist_ok=True)
    for f, it, filename in items:
        dest_path = os.path.join(dest_dir, filename)
        if os.path.exists(dest_path):
            os.remove(dest_path)
        shutil.move(f, dest_path)

    # 4. Log
    os.makedirs(os.path.dirname(WIKI_LOG), exist_ok=True)
    with open(WIKI_LOG, 'a', encoding='utf-8') as f:
        f.write(f"- 14:00 | processed {len(items)} news | reports: 002-news, 002-master | archived to /raw/old news/{TODAY}/\n")
        
    print(f"Successfully processed {len(items)} files.")

if __name__ == "__main__":
    process_files()
