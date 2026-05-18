# Auto-sync GitHub - Hướng dẫn đầy đủ (cho người không chuyên)

Hệ thống auto-sync hoạt động giống Dropbox nhưng dùng GitHub. Theo dõi folder `raw/`, khi có file `.md` mới hoặc thay đổi → tự động commit + push lên repo.

> Repo đích: https://github.com/nguyenvietanhforwork-max/test-v2
> Folder theo dõi: `E:\Application downloads\Value\raw\` (chỉ file `.md`)

---

## 0. Mục lục nhanh

1. Cài Git
2. Clone / khởi tạo repo
3. Kết nối GitHub (PAT hoặc SSH)
4. File auto-sync.bat
5. Phiên bản PowerShell (khuyên dùng)
6. Chạy ẩn nền (hidden runner)
7. Auto-start qua Task Scheduler
8. Dừng script
9. Đổi interval sync
10. Tránh commit rác
11. Kiểm tra đang chạy
12. Debug khi push lỗi
13. Folder structure
14. Best practices

---

## 1. Cài Git trên Windows

Tải installer: <https://git-scm.com/download/win> → chọn **Standalone Installer 64-bit**.

Khi cài, để mặc định gần hết. Mấy mục đáng chú ý:

- **Default editor**: chọn Notepad (cho dễ).
- **Adjusting your PATH**: chọn `Git from the command line and also from 3rd-party software`.
- **HTTPS transport backend**: OpenSSL (mặc định).
- **Line endings**: `Checkout as-is, commit as-is` cho an toàn (tránh CRLF auto-convert phá file Markdown).
- **Credential helper**: chọn `Git Credential Manager` (sẽ tự bật cửa sổ đăng nhập GitHub khi push lần đầu).

Mở PowerShell (Win+R → `powershell`), kiểm tra:

```powershell
git --version
```

Phải in ra `git version 2.xx.x.windows.x`.

Cấu hình tên + email **một lần duy nhất**:

```powershell
git config --global user.name "Nguyen Viet Anh"
git config --global user.email "nguyenvietanhforwork@gmail.com"
```

---

## 2. Clone repo (hoặc khởi tạo)

Trường hợp folder `E:\Application downloads\Value\` đã có nội dung (file `.md` của bạn) và **chưa có `.git`** → khởi tạo tại chỗ:

```powershell
cd "E:\Application downloads\Value"
git init -b main
git remote add origin https://github.com/nguyenvietanhforwork-max/test-v2.git
```

Hoặc nếu folder trống, clone từ GitHub về:

```powershell
git clone https://github.com/nguyenvietanhforwork-max/test-v2.git "E:\Application downloads\Value"
```

(Bạn không cần làm thủ công bước này nếu chạy `first-time-setup.ps1` — script tự xử lý.)

---

## 3. Kết nối GitHub - chọn 1 trong 2 cách

### Cách A — Personal Access Token (PAT) — DỄ NHẤT, KHUYÊN DÙNG

1. Vào <https://github.com/settings/tokens> → **Generate new token (classic)**.
2. Note: `auto-sync-pc`. Expiration: 90 days hoặc No expiration.
3. Scopes: tick `repo` (toàn bộ).
4. Generate → **copy token** ra clipboard (sẽ không hiện lại).
5. Lần push đầu tiên, khi git hỏi **Username**: gõ `nguyenvietanhforwork-max`. Khi hỏi **Password**: **dán token vào** (không phải mật khẩu GitHub).
6. Git Credential Manager sẽ tự lưu lại, lần sau không cần nhập nữa.

### Cách B — SSH key (an toàn hơn nhưng phức tạp hơn)

```powershell
ssh-keygen -t ed25519 -C "nguyenvietanhforwork@gmail.com"
# Enter qua hết, không đặt passphrase cho tiện
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub | clip
```

Vào <https://github.com/settings/keys> → **New SSH key** → paste vào → Save.

Đổi remote sang SSH:

```powershell
git -C "E:\Application downloads\Value" remote set-url origin git@github.com:nguyenvietanhforwork-max/test-v2.git
```

(Đồng thời sửa `scripts\config.json` mục `RemoteUrl` sang dạng `git@github.com:...`.)

Test:

```powershell
ssh -T git@github.com
```

Phải hiện `Hi nguyenvietanhforwork-max! You've successfully authenticated...`.

---

## 4. File `auto-sync.bat` (BAT đơn giản)

Đã có sẵn tại `scripts\auto-sync.bat`. Đây là phiên bản loop tối giản — không có lock, không filter `.md`, không retry thông minh. Dùng khi không muốn PowerShell.

Chạy:

```cmd
cd /d "E:\Application downloads\Value\scripts"
auto-sync.bat
```

Sẽ thấy cửa sổ đen mở liên tục. Đóng cửa sổ = stop.

**KHUYÊN DÙNG**: Bỏ qua bản BAT, dùng PowerShell ở mục 5.

---

## 5. Phiên bản PowerShell (`auto-sync.ps1`) — KHUYÊN DÙNG

Đã có sẵn tại `scripts\auto-sync.ps1`. Khác biệt so với BAT:

- Chỉ commit khi có thay đổi `.md` trong `raw/` (tránh commit rác)
- Lock single-instance (không chạy 2 lần song song)
- Retry push 5 lần với exponential backoff (5s → 10s → 20s → 40s → 80s)
- Network check trước khi push (mất mạng → bỏ qua chứ không fail)
- Log rotate (file log không phình to vô hạn)
- Status JSON cho dashboard
- Pull --rebase --autostash trước push (tránh conflict đơn giản)

### Test một vòng (RunOnce)

```powershell
cd "E:\Application downloads\Value\scripts"
powershell -ExecutionPolicy Bypass -File auto-sync.ps1 -RunOnce -Verbose
```

Expected output: vài dòng `[INFO]` rồi thoát. Không có `FATAL`.

### Chạy liên tục (foreground, có cửa sổ)

```powershell
powershell -ExecutionPolicy Bypass -File auto-sync.ps1
```

Đóng cửa sổ = dừng. Để chạy ẩn, xem mục 6.

---

## 6. Chạy ẩn nền (không hiện terminal đen)

Dùng `run-hidden.vbs` làm launcher. Cách nhanh nhất:

```cmd
cd /d "E:\Application downloads\Value\scripts"
start-sync.bat
```

`start-sync.bat` gọi `wscript.exe run-hidden.vbs`, file VBS này gọi `powershell.exe -WindowStyle Hidden -File auto-sync.ps1`. Không có cửa sổ nào hiện ra. Lock file `logs\auto-sync.lock` xác nhận đang chạy.

---

## 7. Auto-start cùng Windows (Task Scheduler)

Đăng ký một lần:

```powershell
cd "E:\Application downloads\Value\scripts"
powershell -ExecutionPolicy Bypass -File install-task.ps1
```

Script tạo task `AutoSyncGitHub`:

- Trigger: **AtLogOn** của user hiện tại
- Delay: 1 phút (đợi mạng + Credential Manager sẵn sàng)
- Action: chạy `wscript.exe run-hidden.vbs` (ẩn cửa sổ)
- Restart: 3 lần × 5 phút nếu crash
- Không cần quyền Admin (chạy dưới user)

Quản lý: nhấn Win → gõ "Task Scheduler" → Library → `AutoSyncGitHub`.

Gỡ bỏ:

```powershell
powershell -ExecutionPolicy Bypass -File uninstall-task.ps1
```

---

## 8. Dừng script

```cmd
cd /d "E:\Application downloads\Value\scripts"
stop-sync.bat
```

Script đọc PID từ `logs\auto-sync.lock`, `taskkill /F /PID <pid>`, xoá lock.

Muốn dừng vĩnh viễn (không auto-start nữa): chạy thêm `uninstall-task.ps1`.

---

## 9. Đổi interval sync

Mở `scripts\config.json`, sửa số:

```json
"IntervalSeconds": 60
```

- `10` = mỗi 10 giây (rất tích cực, đẩy mạng)
- `30` = nửa phút
- `60` = 1 phút (mặc định, hợp lý)
- `300` = 5 phút (tiết kiệm, ít commit)

Sau khi sửa: `stop-sync.bat` → `start-sync.bat` để áp dụng.

---

## 10. Tránh commit rác (không có thay đổi)

`auto-sync.ps1` xử lý tự động bằng 3 lớp:

1. `git status --porcelain -- raw/` → nếu trống → bỏ qua cycle.
2. Sau filter `.md` → nếu 0 file → bỏ qua.
3. Sau `git add` → `git diff --cached --name-only` → nếu 0 file → bỏ qua.

Nghĩa là chỉ khi có file `.md` thật sự thay đổi mới tạo commit. Không bao giờ có commit "Auto-sync" rỗng.

Khi `QuietWhenNoChanges: true` (mặc định) trong config, script cũng không spam log mỗi cycle "không có thay đổi". Log chỉ có dòng khi thật sự sync.

---

## 11. Kiểm tra script đang chạy

```cmd
cd /d "E:\Application downloads\Value\scripts"
check-status.bat
```

Sẽ hiện:

- `[TRANG THAI] Dang chay - PID=xxxx` hoặc `Khong chay`
- Nội dung `status.json` (counters, last attempt, recent events)
- 20 dòng log cuối

Hoặc mở **dashboard** trong trình duyệt:

```cmd
start "" "E:\Application downloads\Value\outputs\sync-dashboard.html"
```

Auto-refresh 10s, đọc trực tiếp `logs\status.json`.

---

## 12. Debug khi git push lỗi

Mở `logs\auto-sync.log` → xem dòng `[ERROR]` hoặc `[WARN]` gần nhất.

Các tình huống thường gặp:

| Triệu chứng | Nguyên nhân | Cách fix |
|---|---|---|
| `Authentication failed` | Token sai/hết hạn | Tạo PAT mới, push thử bằng tay 1 lần để Credential Manager lưu lại |
| `Could not resolve host: github.com` | Mất mạng | Đợi mạng có lại, script tự retry |
| `failed to push some refs` `non-fast-forward` | Repo trên GitHub có commit mới mà local chưa pull | Bật `PullBeforePush: true` (mặc định đã bật). Nếu vẫn lỗi → có conflict thật, fix bằng tay |
| `error: pathspec ... did not match any files` | Path có ký tự đặc biệt hoặc đã bị xoá | Bỏ qua, cycle sau sẽ ổn |
| `FATAL: From https://...` | Bug `2>&1` + `ErrorActionPreference=Stop` | Đã được xử lý bằng `Invoke-Git` mới (Out-String -Stream + EAP scope) |
| `Da co instance khac dang chay` | Lock file kẹt | `stop-sync.bat`, hoặc xoá `logs\auto-sync.lock` rồi start lại |

Đẩy verbose ra console để xem trực tiếp:

```powershell
powershell -ExecutionPolicy Bypass -File auto-sync.ps1 -RunOnce -Verbose
```

Push tay để test auth nhanh:

```powershell
cd "E:\Application downloads\Value"
git push origin main
```

---

## 13. Folder structure đề xuất

```
E:\Application downloads\Value\
├── .git\                          (git metadata)
├── .gitignore                     (ignore logs/, *.lock, dashboard)
├── raw\                           (FOLDER ĐƯỢC SYNC - chỉ .md)
│   └── *.md                       (file Obsidian/Web Clipper)
├── wiki\, outputs\, ...           (nội dung khác - KHÔNG sync)
├── logs\                          (sinh ra khi chạy)
│   ├── auto-sync.log              (text log, có rotate)
│   ├── status.json                (snapshot trạng thái cho dashboard)
│   └── auto-sync.lock             (PID lock single-instance)
├── outputs\
│   └── sync-dashboard.html        (mở trong browser)
├── scripts\
│   ├── config.json                (cấu hình)
│   ├── auto-sync.ps1              (engine chính)
│   ├── auto-sync.bat              (BAT fallback)
│   ├── run-hidden.vbs             (launcher ẩn)
│   ├── start-sync.bat
│   ├── stop-sync.bat
│   ├── check-status.bat
│   ├── first-time-setup.ps1
│   ├── install-task.ps1
│   └── uninstall-task.ps1
├── SETUP-GUIDE.md                 (file này)
└── HANDOFF.md                     (handoff cũ - có thể xoá)
```

---

## 14. Best practices

- **Tách `raw/` cho input thô** (web clip, Obsidian export). Chỉ folder này được sync. Mọi file khác (`wiki/`, `outputs/`, build artefacts) thì không.
- **Không sửa file đang được auto-sync từ 2 máy cùng lúc**. Pull --rebase xử lý được conflict đơn giản, nhưng conflict thực sự vẫn phải sửa tay.
- **Dùng PAT thay vì SSH** nếu bạn chỉ làm việc trên 1-2 máy → đỡ phải copy key.
- **`IntervalSeconds: 60`** là sweet spot. Dưới 30s sẽ làm GitHub khó chịu nếu folder lớn.
- **Đừng commit file binary lớn** (ảnh, PDF, video) vào `raw/`. Repo sẽ phình to nhanh. Dùng Git LFS hoặc lưu chỗ khác.
- **Backup PAT** vào password manager. Mất là phải tạo lại.
- **Khi xoá folder `logs/`**, script tự tạo lại. An toàn để dọn dẹp.
- **Tránh đặt repo trong path có ký tự lạ** (Unicode, dấu cách quá nhiều). `E:\Application downloads\Value\` có dấu cách — đã được test OK với quotes trong tất cả script.
- **Đọc dashboard mỗi sáng** để biết có cycle nào fail. `ConsecutiveFails` tăng → có gì đó hỏng kéo dài → check log.

---

## Tham khảo nhanh - các lệnh hay dùng

```cmd
:: Setup lần đầu
powershell -ExecutionPolicy Bypass -File scripts\first-time-setup.ps1

:: Test 1 lần
powershell -ExecutionPolicy Bypass -File scripts\auto-sync.ps1 -RunOnce -Verbose

:: Chạy nền
scripts\start-sync.bat

:: Kiểm tra
scripts\check-status.bat

:: Dừng
scripts\stop-sync.bat

:: Auto-start cùng Windows
powershell -ExecutionPolicy Bypass -File scripts\install-task.ps1

:: Gỡ auto-start
powershell -ExecutionPolicy Bypass -File scripts\uninstall-task.ps1

:: Dashboard
start "" outputs\sync-dashboard.html
```
