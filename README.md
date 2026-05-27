# Growtrics AI Chemistry Video Request Service 🧪🎥

Mẫu sản phẩm Backend cao cấp (Production-grade Prototype) cho dịch vụ yêu cầu sinh video giáo dục tương tác về các khái niệm Hóa học dành cho học viên. Hệ thống sử dụng mô hình Kiến trúc Sạch (Clean/Hexagonal Architecture), quản lý vòng đời tác vụ thông qua Máy trạng thái (State Machine) bất đồng bộ, đảm bảo tính nhất quán tuyệt đối và tối ưu hóa chi phí vận hành.

---

## 🚀 Hướng dẫn Cài đặt & Vận hành (Quick Start)

Hệ thống được thiết kế tương thích hoàn toàn trên cả **Windows (PowerShell)**, **macOS** và **Linux**.

### 1. Khởi tạo môi trường ảo & Cài đặt thư viện
Mở terminal tại thư mục gốc của dự án và chạy các lệnh sau:

**Trên Windows (PowerShell):**
```powershell
# Tạo môi trường ảo
python -m venv venv

# Kích hoạt môi trường ảo
.\venv\Scripts\Activate

# Cập nhật pip và cài đặt dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Trên macOS / Linux:**
```bash
# Tạo môi trường ảo
python3 -m venv venv

# Kích hoạt môi trường ảo
source venv/bin/activate

# Cập nhật pip và cài đặt dependencies
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Cấu hình biến môi trường
Tạo file `.env` tại thư mục gốc dự án:

```bash
APP_ENV=development
LOG_LEVEL=INFO
STORAGE_DIR=./storage/artifacts
GENERATION_SIMULATION_LATENCY_SECS=4.0
MAX_GENERATION_RETRIES=3
```

Hoặc copy từ `.env.example`:
```bash
cp .env.example .env
```

### 3. Tạo thư mục lưu trữ artifacts
```powershell
# Windows
New-Item -ItemType Directory -Path "./storage/artifacts" -Force

# macOS / Linux
mkdir -p ./storage/artifacts
```

---

## 🎮 Chạy Server

Khởi động server FastAPI:

```powershell
# Windows
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

# macOS / Linux
python3 -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Server sẽ khởi chạy tại: **http://127.0.0.1:8000**

### Truy cập API Documentation
- **Swagger UI (tương tác):** http://127.0.0.1:8000/docs
- **ReDoc (đọc):** http://127.0.0.1:8000/redoc

---

## 🧪 Chạy Tests

### Chạy tất cả tests
```powershell
pytest
```

### Chạy tests cụ thể
```powershell
# API tests
pytest tests/test_api.py -v

# Orchestrator tests
pytest tests/test_orchestrator.py -v
```

### Chạy tests với verbose output
```powershell
pytest -v -s
```

---

## 📡 API Endpoints

### 1. Health Check
```http
GET /
```

**Response (200):**
```json
{
  "status": "healthy",
  "service": "AI Chemistry Video Request Service",
  "environment": "development",
  "api_docs_url": "/docs"
}
```

---

### 2. Tạo yêu cầu video (Create Job)
```http
POST /api/v1/videos
Content-Type: application/json

{
  "query": "Why do atoms form covalent bonds?"
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "job_a1b2c3d4e5f6",
  "query": "Why do atoms form covalent bonds?",
  "status": "submitted",
  "created_at": "2025-05-27T10:30:45.123Z",
  "updated_at": "2025-05-27T10:30:45.123Z",
  "estimated_duration_secs": 0.0,
  "cost_usd": 0.0,
  "error_message": null,
  "artifact_url": null
}
```

---

### 3. Lấy danh sách tất cả jobs
```http
GET /api/v1/videos
```

**Response (200):**
```json
{
  "jobs": [
    {
      "job_id": "job_a1b2c3d4e5f6",
      "query": "Why do atoms form covalent bonds?",
      "status": "completed",
      "created_at": "2025-05-27T10:30:45.123Z",
      "updated_at": "2025-05-27T10:30:55.456Z",
      "estimated_duration_secs": 50.0,
      "cost_usd": 0.020,
      "error_message": null,
      "artifact_url": "/api/v1/videos/job_a1b2c3d4e5f6/artifact"
    }
  ]
}
```

---

### 4. Kiểm tra trạng thái Job
```http
GET /api/v1/videos/{job_id}
```

**Response (200):**
```json
{
  "job_id": "job_a1b2c3d4e5f6",
  "query": "Why do atoms form covalent bonds?",
  "status": "processing",
  "created_at": "2025-05-27T10:30:45.123Z",
  "updated_at": "2025-05-27T10:30:50.234Z",
  "estimated_duration_secs": 0.0,
  "cost_usd": 0.0,
  "error_message": null,
  "artifact_url": null
}
```

---

### 5. Tải video artifact
```http
GET /api/v1/videos/{job_id}/artifact
```

**Response (200):**
- Content-Type: `video/mp4`
- Body: Binary MP4 file stream

**Trường hợp lỗi:**
- **(202)** Job chưa hoàn thành — tiếp tục poll
- **(404)** Job ID không tồn tại
- **(500)** File video bị mất (data integrity error)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────┐
│           FastAPI Application Layer              │
│  • POST /api/v1/videos  (submit job)             │
│  • GET  /api/v1/videos  (list jobs)              │
│  • GET  /api/v1/videos/{id}  (status)            │
│  • GET  /api/v1/videos/{id}/artifact (download)  │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│    Domain Layer (Core Business Logic)            │
│  • VideoJob (State Machine)                      │
│  • JobStatus (SUBMITTED → PROCESSING → COMPLETED)
│  • VideoJobOrchestrator (Async Coordinator)      │
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌──────────────────┐  ┌──────────────────┐
│  Ports (Interfaces)                    │
│  • IJobRepository│  │IMediaGenerationEngine│
│  • Contracts     │  │• Contracts       │
└──────────────────┘  └──────────────────┘
        │                     │
        ▼                     ▼
┌──────────────────┐  ┌──────────────────────────────┐
│ Persistence      │  │ Media Generation Adapters    │
│ • InMemoryJobRep │  │ • StructuredMediaEngine      │
│ • Asyncio Lock   │  │ • VideoRenderer (PIL+Moviepy)
└──────────────────┘  └──────────────────────────────┘
        │                     │
        ▼                     ▼
    RAM Storage         {job_id}.mp4
   (per session)    {job_id}_manifest.json
```

### Async Job Lifecycle

```
1. Client: POST /api/v1/videos {"query": "..."}
                          ↓
2. API: Validate request → Create VideoJob (SUBMITTED) → Return 202
                          ↓
3. Background Task Scheduled (BackgroundTasks)
                          ↓
4. Worker: Fetch job → Transition to PROCESSING
                          ↓
5. Engine: Generate manifest (KB lookup + render video)
                          ↓
6. Retry Loop: (max 3 attempts with exponential backoff)
   - Guardrail check (UNSUPPORTED_STEM_TOPIC → FAILED immediately)
   - Transient error → retry with 2^attempt seconds delay
                          ↓
7. Completion: job.artifact = manifest → COMPLETED → persist
   OR
   Failure: job.error_message = error → FAILED → persist
                          ↓
8. Client: Poll GET /api/v1/videos/{job_id}
                          ↓
9. When COMPLETED: GET /api/v1/videos/{job_id}/artifact → stream MP4
```

---

## 📊 Knowledge Base (Built-in Topics)

Hệ thống hiện hỗ trợ 3 chủ đề hóa học được chứng thực sẵn:

| Query | Duration | Cost | Status |
|-------|----------|------|--------|
| "How does the pH scale work?" | 60 secs | $0.015 | ✅ |
| "Why do atoms form covalent bonds?" | 50 secs | $0.020 | ✅ |
| "What is the difference between ionic and covalent bonding?" | 75 secs | $0.035 | ✅ |

**Truy vấn khác** sẽ trả về lỗi **400 Bad Request** với thông báo guardrail.

---

## 📁 Cấu trúc Dự Án

```
Growtrics/
├── main.py                          # FastAPI entrypoint
├── requirements.txt                 # Dependencies
├── README.md                        # This file
├── .env.example                     # Environment template
├── .env                             # Environment config (local)
│
├── config/
│   └── settings.py                  # Pydantic BaseSettings config
│
├── src/
│   ├── api/
│   │   ├── router.py               # API endpoints (POST, GET, GET/{id}, GET/{id}/artifact)
│   │   ├── schemas.py              # Pydantic request/response DTOs
│   │   └── dependencies.py         # Dependency injection (singletons)
│   │
│   ├── core/
│   │   ├── orchestrator.py         # VideoJobOrchestrator (async coordinator)
│   │   ├── models.py               # Domain entities (VideoJob, JobStatus, VideoSegment, manifest)
│   │   └── exceptions.py           # Custom exception hierarchy
│   │
│   ├── interfaces/
│   │   ├── repository.py           # IJobRepository port
│   │   └── engine.py               # IMediaGenerationEngine port
│   │
│   └── infrastructure/
│       ├── persistence/
│       │   └── in_memory.py        # InMemoryJobRepository adapter
│       │
│       └── media/
│           ├── structured_engine.py # StructuredMediaEngine (KB + validator)
│           └── video_renderer.py   # Slide PNG + MP4 assembly (PIL, numpy, moviepy)
│
├── tests/
│   ├── test_api.py                 # API integration tests
│   └── test_orchestrator.py        # Orchestrator async tests
│
└── storage/
    └── artifacts/                  # Generated MP4 files & manifests
        ├── job_xxx.mp4
        └── job_xxx_manifest.json
```

---

## 🔧 Troubleshooting

### **"ModuleNotFoundError: No module named 'moviepy'"**
```powershell
pip install moviepy>=2.0.0
```

### **"Font not found" (video rendering warning)**
Renderer sẽ fallback to default PIL font. Không ảnh hưởng đến tính năng.

### **Port 8000 đã được sử dụng**
```powershell
# Sử dụng port khác
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

### **Storage directory permission denied**
Kiểm tra quyền ghi (write permission) trên thư mục `./storage/artifacts`:
```powershell
# Windows
icacls "./storage/artifacts" /grant "%USERNAME%":F /T
```

### **Tests timeout (video rendering quá lâu)**
Giảm `GENERATION_SIMULATION_LATENCY_SECS` trong `config/settings.py`:
```python
GENERATION_SIMULATION_LATENCY_SECS: float = 0.1  # 100ms thay vì 4.0s
```

---

## 📚 API Testing với cURL

### 1. Health check
```bash
curl -X GET http://127.0.0.1:8000/
```

### 2. Tạo video request
```bash
curl -X POST http://127.0.0.1:8000/api/v1/videos \
  -H "Content-Type: application/json" \
  -d '{"query": "How does the pH scale work?"}'
```

### 3. Kiểm tra status
```bash
curl -X GET http://127.0.0.1:8000/api/v1/videos/{job_id}
```

### 4. Tải video
```bash
curl -X GET http://127.0.0.1:8000/api/v1/videos/{job_id}/artifact \
  -o output.mp4
```

---

## 🔐 Security Notes

- **CORS:** Cho phép all origins (`"*"`) cho phát triển cục bộ. **Sản xuất:** Cập nhật `allow_origins` trong `main.py`
- **Database:** In-memory (per-session). **Sản xuất:** Thay bằng PostgreSQL adapter
- **Authentication:** Không có hiện tại. **Sản xuất:** Thêm JWT/OAuth2 vào `src/api/security.py`

---

## 📈 Mở rộng hệ thống

### Thêm topic hóa học mới
Cập nhật `_KNOWLEDGE_BASE` trong `src/infrastructure/media/structured_engine.py`:
```python
_KNOWLEDGE_BASE: dict[str, dict] = {
    "your new chemistry question?": {
        "concept_query": "Your new chemistry question?",
        "domain_topic": "Chemistry",
        "total_duration_secs": 60.0,
        "production_cost_usd": 0.025,
        "timeline": [
            {
                "timestamp_start": 0.0,
                "timestamp_end": 60.0,
                "title": "Section Title",
                "voiceover_script": "Full narration...",
                "visual_elements": ["Element 1", "Element 2"],
            }
        ],
    },
    # ...existing topics
}
```

### Tích hợp LLM (OpenAI GPT-4 / Claude)
1. Thay thế `_KNOWLEDGE_BASE` lookup bằng LLM call
2. Thêm OpenAI dependency vào `requirements.txt`
3. Cập nhật error handling cho token limit / rate limits

### Tích hợp TTS (Text-to-Speech)
1. Gọi OpenAI TTS API trên `segment.voiceover_script`
2. Lưu audio file
3. Thêm audio track vào video assembly trong `video_renderer.py`

---

## 📞 Support

**Tác giả:** Growtrics AI Team  
**Phiên bản:** 1.0.0  
**Ngôn ngữ:** Python 3.9+  
**Framework:** FastAPI 0.111.0  

---

## 📝 License

MIT License — Xem `LICENSE` file
