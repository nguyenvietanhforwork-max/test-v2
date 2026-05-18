# Atlas — Deployment Guide (v3, 2026-05-18)

> **Mục tiêu:** Push code lên GitHub → website tự động cập nhật.
> **Stack:** GitHub → Vercel (dashboard) + GitHub Actions (pipeline) + (tùy chọn) Render (FastAPI backend).
> **Thời gian:** ~20 phút setup lần đầu. Sau đó mọi push tự động deploy.
> **Chi phí:** $0/tháng cho dashboard + pipeline. ~$7/tháng nếu bật API backend.

---

## Tổng quan luồng auto-update

```
   bạn push lên main
         │
         ▼
   ┌─────────────────────────────────────────┐
   │ GitHub Actions: deploy.yml (sanity)     │  ← validates JSON, dashboard exists, no junk
   └─────────────────────────────────────────┘
         │
         ▼
   ┌─────────────────────────────────────────┐
   │ Vercel auto-deploy (qua GitHub integ.)  │  ← builds & serves apps/dashboard/
   └─────────────────────────────────────────┘
         │
         ▼
   website mới có sẵn ~30 giây sau

   ┌─ riêng biệt ──────────────────────────────────────┐
   │ Mỗi ngày 06:00 ICT (+ khi raw/ thay đổi):         │
   │ GitHub Actions: pipeline.yml                      │
   │   clean → summarize → build_index → build_graph   │
   │   → commit content/reports + generated/ → push    │
   │   → kích Vercel deploy → dashboard refresh        │
   └───────────────────────────────────────────────────┘
```

---

## Bước 1 — Chạy cleanup-legacy.ps1 (PHẢI làm trước khi push)

Sao chép `news-dashboard-v2.html` thành `apps/dashboard/index.html` (canonical MVP) và dọn dẹp.

```powershell
cd "E:\Application downloads\Value"

# Dry-run trước, kiểm tra log:
powershell -ExecutionPolicy Bypass -File .\scripts\cleanup-legacy.ps1

# Nếu log OK, chạy thật:
powershell -ExecutionPolicy Bypass -File .\scripts\cleanup-legacy.ps1 -Apply

# Verify:
Test-Path .\apps\dashboard\index.html        # → True
(Get-Item .\apps\dashboard\index.html).Length # → ~80000+ bytes
```

> **Lưu ý:** Cleanup script **không xóa** code — chỉ di chuyển vào `legacy/`. Chỉ `node_modules` / `__pycache__` / `.next` bị xóa thật (vì có thể tạo lại).

---

## Bước 2 — Push v3 lên GitHub

```powershell
cd "E:\Application downloads\Value"

# Xem có gì sẽ commit (sanity check):
git status

# Nếu có file .env hoặc secret nào lộ ra → STOP, kiểm tra .gitignore trước!
# Xác nhận:
git check-ignore -v .env intelligence-platform/.env

# Stage & commit:
git add -A
git commit -m "feat: v3 restructure — AI-native intelligence platform

- Hybrid architecture (Research Wiki ⊂ Intelligence Platform)
- Canonical dashboard: apps/dashboard/index.html (was news-dashboard-v2.html)
- Modular prompts, semantic schemas, feedback intelligence
- Retire intelligence-platform/, apps/web/, infra/k8s/ → legacy/
- See outputs/architecture-decisions-2026-05-18.md (ADR-001 … ADR-011)"

# Push:
git push origin main
```

Nếu `git push` từ chối vì tag size lớn (do legacy/ có nhiều file), dùng:

```powershell
git push origin main --no-verify
```

---

## Bước 3 — Kết nối Vercel với GitHub repo

### Cách A — Vercel Dashboard (Web UI)

1. Vào **https://vercel.com/new**
2. Click **"Import Git Repository"**
3. Chọn repo Atlas của bạn → **Import**
4. Configure project:
   - **Framework Preset:** Other
   - **Root Directory:** `.` (không sửa)
   - **Build Command:** *(để trống — `vercel.json` đã cấu hình)*
   - **Output Directory:** *(để trống — `vercel.json` đã cấu hình)*
   - **Install Command:** *(để trống)*
5. Click **Deploy**. Build đầu tiên mất ~30 giây.
6. Sau khi deploy thành công, copy URL (vd: `https://atlas-xxx.vercel.app`) — đó là production URL.

### Cách B — Vercel CLI (nhanh hơn nếu đã cài)

```bash
npm i -g vercel
cd "E:\Application downloads\Value"
vercel link
vercel --prod
```

### Tùy chỉnh sau khi link

- **Custom domain** (tùy chọn): Vercel Dashboard → Project → Settings → Domains → Add → ví dụ `intelligence-letter.com`
- **Git auto-deploy** đã bật mặc định — mọi push lên `main` sẽ trigger deploy
- **Preview deploys**: mọi PR sẽ tạo preview URL riêng (không đè production)

---

## Bước 4 — Thêm Vercel Deploy Hook vào dashboard (tùy chọn)

Dashboard có nút "Sync" gọi Vercel deploy hook để force rebuild. Để bật:

1. Vercel Dashboard → Project → Settings → **Git** → **Deploy Hooks**
2. Click **Create Hook** → Name: `dashboard-sync`, Branch: `main` → **Create Hook**
3. Copy URL hook (dạng `https://api.vercel.com/v1/integrations/deploy/prj_xxx/yyy`)
4. Mở `apps/dashboard/index.html`, tìm:
   ```js
   const VERCEL_DEPLOY_HOOK = "";
   ```
   Dán URL vào trong dấu ngoặc kép.
5. Commit + push:
   ```powershell
   git add apps/dashboard/index.html
   git commit -m "feat(dashboard): wire Vercel deploy hook"
   git push
   ```

Bây giờ nút "Sync" trên dashboard trigger rebuild luôn.

---

## Bước 5 — Cấu hình GitHub Secrets cho pipeline

Pipeline workflow (`.github/workflows/pipeline.yml`) cần API keys để chạy `summarize.py` + `generate_embeddings.py`.

1. GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
2. Thêm các secret sau:

| Tên secret | Giá trị | Bắt buộc? |
|---|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` từ console.anthropic.com | ✅ Có (cho summarize) |
| `OPENAI_API_KEY` | `sk-...` từ platform.openai.com | Tùy chọn (chỉ dùng cho embeddings) |

3. Click **Add secret** cho mỗi key.

> **Tip:** Không cần thêm `GITHUB_TOKEN` — Actions tự cấp sẵn, đủ quyền push commit về main.

---

## Bước 6 — Cấp quyền GitHub Actions push về main

Mặc định Actions có thể push, nhưng nếu repo bật branch protection:

1. Repo → **Settings** → **Actions** → **General** → kéo xuống **Workflow permissions**
2. Chọn **"Read and write permissions"**
3. Tick **"Allow GitHub Actions to create and approve pull requests"** (nếu chưa)
4. **Save**

---

## Bước 7 — Test pipeline thủ công

Trước khi đợi schedule chạy, trigger thủ công 1 lần để kiểm tra:

1. GitHub repo → **Actions** tab
2. Bên trái, click **"Intelligence Pipeline"**
3. Bên phải, click **"Run workflow"** → chọn branch `main` → **Run workflow**
4. Đợi ~5–10 phút. Click vào run để xem log từng stage.
5. Nếu xanh hết: kiểm tra `content/reports/` và `generated/index.json` có thay đổi không (Actions sẽ commit về `main` nếu có generation mới).
6. Vercel sẽ tự deploy commit đó → website refresh.

---

## Bước 8 — Verify auto-update hoạt động

Test scenario thực tế:

1. Drop một file markdown mới vào `raw/news/2026-05-18/test-article.md` ở local
2. Commit + push:
   ```powershell
   git add raw/news/2026-05-18/test-article.md
   git commit -m "test: trigger pipeline with new clipping"
   git push
   ```
3. Vào GitHub Actions tab — **Intelligence Pipeline** sẽ chạy (vì push touches `raw/**`)
4. Sau ~5 phút: kiểm tra `content/reports/` đã có report mới chưa
5. Sau ~1 phút nữa: Vercel deploy commit mới → website thấy report mới
6. Đăng website → article phải xuất hiện trong dashboard

Nếu thấy article mới trên website — auto-update đã hoạt động ✅

---

## Bước 9 — (Tùy chọn) Deploy FastAPI backend lên Render

Backend chỉ cần thiết nếu muốn:
- Live WebSocket updates
- Feedback POST endpoint
- Semantic search qua pgvector / Meilisearch

Nếu chỉ cần dashboard static với pipeline — bỏ qua bước này.

Để deploy:

1. Render.com → **New** → **Blueprint**
2. Connect GitHub repo
3. Render đọc `render.yaml` → tạo 4 services: api, worker, beat, pdf
4. Thêm env vars (mỗi service): `ANTHROPIC_API_KEY`, `POSTGRES_URL`, `REDIS_URL`, `MEILI_HOST`, etc.
5. **Apply** → đợi ~10 phút.
6. API URL sẽ ở dạng `https://atlas-api-xxx.onrender.com`
7. Update dashboard's API endpoint (nếu dashboard fetch API):
   ```js
   const API_BASE = "https://atlas-api-xxx.onrender.com/api/v1";
   ```

---

## Bảng tóm tắt URLs / commands

| Mục đích | URL / lệnh |
|---|---|
| Vercel project | https://vercel.com/dashboard |
| GitHub Actions | https://github.com/`<user>`/`<repo>`/actions |
| Pipeline manual trigger | Actions tab → Intelligence Pipeline → Run workflow |
| Force redeploy dashboard | Click "Sync" trên dashboard (sau khi wire deploy hook) |
| Check deploy logs | Vercel Dashboard → Project → Deployments → Click commit |
| Rollback | Vercel → Deployments → Click commit cũ → "Promote to Production" |

---

## Troubleshooting

### "Vercel deploy failed: Module not found"
→ `vercel.json` build command dùng `cp` — chỉ chạy trên Linux. Vercel build runner là Ubuntu nên OK. Nếu vẫn lỗi, kiểm tra `outputDirectory` trỏ đúng `apps/dashboard`.

### "Actions: permission denied khi git push"
→ Bước 6 — bật "Read and write permissions" trong Settings → Actions.

### "Dashboard không thấy report mới sau pipeline chạy"
→ Mở DevTools Console trên website → xem `[liveUpdate]` log. Nếu thấy "schema mismatch" → `build_index.py` đang emit shape khác với dashboard mong đợi (xem `apps/dashboard/data/index.json` so với `const ITEMS` shape).

### "Pipeline rate limited bởi Anthropic"
→ Bình thường nếu xử lý nhiều file một lúc. Workflow đã có `concurrency: cancel-in-progress: false` để tránh chồng chéo. Cân nhắc tăng `timeout-minutes`.

### "GitHub Action chạy nhưng không commit gì"
→ Bình thường nếu không có file mới trong `raw/` từ lần chạy trước. Workflow log sẽ ghi "No changes to commit."

### "raw/ files tôi push không trigger pipeline"
→ Kiểm tra `.github/workflows/pipeline.yml` `paths:` filter — chỉ trigger nếu `raw/**`, `cleaned/**`, `prompts/**`, `scripts/**`, hoặc `schemas/**` thay đổi. Nếu push file ngoài các path này → không trigger (đúng ý đồ — tránh chạy pipeline không cần thiết).

---

## Bảo trì hàng tháng

- Xem `feedback/analytics/per-prompt-version.json` — prompt version nào đang win
- Bump version trong `prompts/summarization/topic-sentence-bullets.md` khi muốn thử style mới
- Kiểm tra `legacy/` còn cần preserve hay có thể xóa hẳn (sau backup)
- Update `requirements.txt` nếu Anthropic/OpenAI SDK ra version mới có breaking changes

---

## Tài liệu liên quan

- `README.md` — overview
- `ARCHITECTURE.md` — kiến trúc v3
- `CLAUDE.md` — hướng dẫn AI agents
- `MIGRATION.md` — chi tiết những gì retired vào `legacy/`
- `outputs/architecture-decisions-2026-05-18.md` — ADR-001 … ADR-011
- `outputs/transformation-report-2026-05-18.md` — final transformation report
