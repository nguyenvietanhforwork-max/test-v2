# Production-Grade AI Intelligence Platform Architecture Prompt

Bạn là một Principal AI Systems Architect + Fullstack Engineer + Data Pipeline Designer.

Nhiệm vụ của bạn là redesign toàn bộ hệ thống xử lý knowledge/news intelligence của tôi dựa trên Obsidian Vault, raw data ingestion, automated report generation và dashboard analytics.

# CONTEXT

Tôi đang xây dựng một hệ thống intelligence workflow gồm:
- Crawl news bằng Obsidian Web Clipper trên Microsoft Edge
- Lưu raw data trong Obsidian Vault
- Dùng AI để:
  - phân loại dữ liệu
  - research mở rộng
  - tạo report tự động
  - tạo dashboard theo thời gian thực
  - export PDF reports
  - trace-back source

Hãy thiết kế cho tôi:
1. System Architecture
2. Internal Processing Workflow
3. Folder Logic
4. Data Pipeline
5. AI Processing Flow
6. Database Schema
7. Dashboard UX/UI
8. Backend APIs
9. Automation Engine
10. PDF Report Engine
11. Frontend Structure
12. Deployment Architecture
13. File Naming Convention
14. Background Jobs
15. Real-time Sync Logic
16. Agent Workflow
17. Scalability Strategy

---

# CURRENT VAULT STRUCTURE

```txt
/raw
    /news
    /old news
    /PDF Files
    /Social Media Post

/wiki
    /Doanh nghiệp Việt Nam
    /Doanh nghiệp Quốc tế
    /Vĩ mô Việt Nam
    /Vĩ mô Quốc tế
        /Bất động sản
        /Nông nghiệp - chăn nuôi
        /Logistic
        /Năng lượng
        /Sản xuất
        /Ô tô
        /Dược phẩm
        ...

/Processed
    /Report of news
    /Report of Social Media Post
    /Report of PDF Files
    /MASTER Report

/AGENTS.md
```

---

# SYSTEM RULES

- raw is immutable
- Never edit files in raw
- After processing:
  - move processed news into:
    `/raw/old news/YYYY-MM-DD/`
- Wiki is AI-owned knowledge layer
- AGENTS.md stores operational memory and schemas
- System must auto-detect new industries and create folders automatically

---

# REQUIRED AUTOMATION FLOW

I want a FULLY AUTOMATED INTERNAL PROCESS.

Whenever:
- new files appear inside:
  `/raw/news`

The system should automatically:

## STEP 1
Detect new files

## STEP 2
Extract:
- title
- source
- publish date
- content
- URL
- tags
- company names
- industries
- countries
- macro topics

## STEP 3
Classify content into:
- Vietnam Corporate News
- International Corporate News
- Vietnam Macro
- International Macro

For Vietnam Corporate News:
- automatically classify by industries

## STEP 4
Generate structured summaries:
- First sentence = main thesis/topic sentence
- Remaining sentences:
  - supporting arguments
  - supporting ideas
  - implications
  - market impacts
  - notable data points

## STEP 5
Create daily reports:
- Report of news
- Report of Social Media Post
- Report of PDF Files
- MASTER Report

## STEP 6
Generate PDF version automatically

## STEP 7
Update Dashboard automatically

## STEP 8
Move processed files into:
- `/raw/old news/YYYY-MM-DD/`

---

# REPORT FORMAT REQUIREMENTS

The report format should resemble:
- professional institutional market intelligence reports
- investment fund morning briefs
- macroeconomic strategic reports

Reference tone:
- concise
- analytical
- executive-level
- information dense

Each report section must contain:
- Main Thesis
- Key Supporting Points
- Implications
- Related Companies
- Industry Effects
- Source Citations
- Original Source Links

---

# DASHBOARD REQUIREMENTS

Design a modern intelligence dashboard website inspired by:
https://www.soulslab.co/

The design language should include:
- premium dark UI
- smooth motion
- glassmorphism
- minimal typography
- modular card system
- elegant charts
- modern gradients
- cinematic transitions
- responsive layouts

---

# DASHBOARD FEATURES

Create a website dashboard with these features:

## 1. DAILY NEWS INTELLIGENCE VIEW
- Group news by date
- Expand/collapse sections
- Show biggest headline capturing daily thesis
- Click to expand detailed report
- Filter by:
  - industry
  - macro
  - geography
  - companies
  - themes

## 2. TRACE-BACK FEATURE
For each news item:
- open original web source
- open source inside Obsidian vault
- open generated report
- open related wiki notes

## 3. REALTIME REFRESH BUTTON
- manual refresh button
- trigger backend sync
- detect newly added files
- regenerate reports
- update dashboard instantly

## 4. PDF REPORT CENTER
- view reports by day
- preview PDFs
- download PDFs
- version history

## 5. SEARCH + KNOWLEDGE GRAPH
- semantic search
- relationship mapping
- company-industry-topic linking

## 6. INDUSTRY SEGMENTATION
Vietnam Corporate News:
- grouped by industry

Other groups:
- Vietnam Macro
- International Macro
- International Companies

---

# TECH STACK

Recommend best architecture.

## Frontend
- Next.js
- Tailwind
- Framer Motion
- shadcn/ui

## Backend
- FastAPI or NestJS

## Database
- PostgreSQL
- pgvector

## Automation
- LangGraph
- Temporal
- n8n
- Airflow
- Watchdog

## AI
- OpenAI API
- Claude API
- embeddings
- RAG pipeline

## PDF
- Puppeteer
- React PDF

## Search
- Meilisearch or Elasticsearch

## Realtime
- WebSockets
- Supabase Realtime

---

# OUTPUT FORMAT

Provide:

1. FULL SYSTEM ARCHITECTURE
2. COMPLETE FOLDER STRUCTURE
3. DATA FLOW DIAGRAM
4. DATABASE SCHEMA
5. API DESIGN
6. AI AGENT DESIGN
7. DASHBOARD WIREFRAME DESCRIPTION
8. AUTOMATION PIPELINE
9. REPORT GENERATION FLOW
10. PDF GENERATION FLOW
11. BACKEND SERVICE BREAKDOWN
12. FRONTEND COMPONENT STRUCTURE
13. STATE MANAGEMENT DESIGN
14. FILE PROCESSING LOGIC
15. OBSIDIAN INTEGRATION METHOD
16. DEPLOYMENT PLAN
17. SECURITY MODEL
18. SCALABILITY STRATEGY
19. EVENT-DRIVEN ARCHITECTURE
20. SUGGESTED REPOSITORY STRUCTURE

Generate the response as if you are designing a production-grade institutional intelligence platform used by hedge funds and strategy teams.
