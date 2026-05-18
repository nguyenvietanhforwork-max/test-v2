# Deploy local — News dashboard

Hướng dẫn dựng toàn bộ stack trên máy bằng docker-compose, lấy tin từ `E:/Application downloads/Value/raw/`.

## Yêu cầu

- Docker Desktop (Windows: WSL2 backend) đang chạy
- ~6 GB RAM rảnh, ~5 GB disk cho images
- (Tùy chọn) `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` nếu muốn agents tóm tắt + phân loại tự động. Để trống vẫn chạy được dashboard, chỉ là tin sẽ ở dạng raw không có summary.

## Khởi động (1 lệnh)

Windows PowerShell:
```powershell
cd "E:\Application downloads\Value\intelligence-platform"
pwsh ./scripts/start-local.ps1
```

macOS / Linux / WSL:
```bash
cd "/path/to/intelligence-platform"
./scripts/start-local.sh
```

Script sẽ:
1. Kiểm tra Docker, kiểm tra `.env`, kiểm tra `VAULT_PATH`
2. `docker compose build` rồi `up -d` toàn bộ services
3. Đợi `http://localhost:8000/healthz` và `http://localhost:3000` lên
4. `POST /v1/ingest/refresh` để watcher quét lại toàn bộ `raw/` ngay
5. Mở trình duyệt vào dashboard

## Cổng dịch vụ

| Service       | URL                              | Mô tả                                  |
|---------------|----------------------------------|----------------------------------------|
| Dashboard     | http://localhost:3000            | News dashboard (Next.js)               |
| API           | http://localhost:8000/docs       | FastAPI Swagger                        |
| WebSocket     | ws://localhost:8000/ws           | Realtime push để dashboard cập nhật    |
| n8n           | http://localhost:5678            | Visual workflow editor                 |
| Meilisearch   | http://localhost:7700            | Full-text search                       |
| Postgres      | localhost:5432 (intelligence/dev)| pgvector                               |
| Redis         | localhost:6379                   | queue / pubsub                         |

## Luồng dữ liệu khi thêm tin mới

```
E:/Application downloads/Value/raw/news/*.md
        │
        ▼   (watchdog detects file, 250ms debounce)
services/ingestion ─── POST /v1/ingest ───► apps/api
                                              │
                                              ├─► Postgres (raw row)
                                              ├─► Redis pub: news.ingested
                                              └─► WS broadcast → dashboard
                                                              (UI auto-prepends headline)
        │
        ▼   (if ANTHROPIC_API_KEY set)
services/agents picks up the job → classify + summarize
                                              │
                                              └─► UPDATE row → WS broadcast → headline animates with summary
```

Nội dung trong `raw/old news/` **không** được watcher theo dõi (đó là archive). Chỉ các thư mục `news/`, `PDF Files/`, `Social Media Post/` mới được tự động ingest.

## Thêm tin mới — 3 cách

1. **Kéo file vào `raw/news/`** (cách thường dùng) — Web Clipper, drag-drop, vv.
2. **Gọi POST trực tiếp**:
   ```bash
   curl -X POST http://localhost:8000/v1/ingest \
        -H "Content-Type: application/json" \
        -d '{"title":"...","content":"...","source":"manual"}'
   ```
3. **Force re-scan toàn bộ raw/**:
   ```bash
   curl -X POST http://localhost:8000/v1/ingest/refresh
   ```

Trong mọi trường hợp, dashboard sẽ nhận push qua WebSocket và prepend headline mới — không cần F5.

## Xem logs

```powershell
# tất cả
docker compose -f infra/docker/docker-compose.yml --env-file .env logs -f

# chỉ watcher (xem tin có vào hay không)
docker compose -f infra/docker/docker-compose.yml --env-file .env logs -f watcher

# chỉ API
docker compose -f infra/docker/docker-compose.yml --env-file .env logs -f api
```

## Dừng

```powershell
pwsh ./scripts/stop-local.ps1
```

Volumes (`pgdata`, `meilidata`, `n8ndata`) được giữ lại để lần sau khởi động không mất tin đã ingest. Nếu muốn xoá sạch:

```powershell
docker compose -f infra/docker/docker-compose.yml --env-file .env down -v
```

## Troubleshooting

**Dashboard mở nhưng trống / 0 tin.**
- Check `docker compose ... logs watcher` — xem có dòng `ingest.ok` không.
- Nếu watcher báo `vault_path does not exist`: mở `.env` và sửa `VAULT_PATH=` cho đúng (phải dùng `/` chứ không phải `\`, ví dụ `E:/Application downloads/Value`).
- Force quét lại: `curl -X POST http://localhost:8000/v1/ingest/refresh`.

**Watcher không thấy file mới trên Windows.**
- Docker Desktop với WSL2 thỉnh thoảng miss filesystem events từ ổ Windows. Workaround: cứ vài phút full scan tự chạy. Hoặc dùng `/v1/ingest/refresh`. Nếu nhiều, chuyển vault vào WSL filesystem.

**Build dashboard hỏng "Cannot find module ..."**.
- `docker compose ... build --no-cache dashboard`. Next 15 + monorepo workspaces đôi khi cần build lại sạch.

**Agents container restart loop, log báo "ANTHROPIC_API_KEY missing"**.
- Bình thường nếu chưa thêm key. Dashboard vẫn chạy không cần agents. Hoặc thêm key vào `.env` rồi `docker compose ... up -d agents`.

**Postgres healthcheck mãi không pass.**
- Chờ thêm ~30s ở lần đầu (migrations chạy lần đầu mất một lúc). Nếu vẫn lỗi: `docker compose ... down -v` và start lại.

**Port 3000 / 5432 đã có app khác chiếm.**
- Sửa mapping port trong `infra/docker/docker-compose.yml` (ví dụ `"3001:3000"`) và đổi `NEXT_PUBLIC_API_BASE_URL` tương ứng trong `.env`.

## Khi nào nâng cấp lên production?

Local stack dùng Postgres + Redis trong container nội bộ — không có replication, không có RLS, không có TLS. Để chạy thật:
- Tạo Supabase project, copy `DATABASE_URL` và keys vào `.env`
- Tạo Upstash Redis
- Theo `docs/DEPLOYMENT.md` để deploy lên Vercel + Railway

Local stack này dành cho: dev, demo, hoặc chạy single-user trên máy cá nhân.
