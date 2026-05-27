import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.router import router as video_router
from config.settings import settings

# Khởi tạo ứng dụng FastAPI với đầy đủ siêu dữ liệu phục vụ API Docs
app = FastAPI(
    title="Growtrics AI Chemistry Video Request Service",
    description=(
        "Backend prototype service allowing learners to request educational chemistry videos. "
        "Processes media generation tasks asynchronously through a strict state machine."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Cấu hình CORS Middleware để sẵn sàng kết nối với bất kỳ Client nhẹ nào (Postman, Frontend, Script)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tích hợp hệ thống phân luồng API Routing của phân hệ Video Service
app.include_router(video_router)

@app.get("/", tags=["Hệ thống"])
async def root_health_check():
    """Endpoint kiểm tra trạng thái hoạt động tổng thể của máy chủ (Health Check)."""
    return {
        "status": "healthy",
        "service": "AI Chemistry Video Request Service",
        "environment": settings.APP_ENV,
        "api_docs_url": "/docs"
    }

if __name__ == "__main__":
    # Khởi chạy máy chủ ASGI Uvicorn phục vụ phát triển cục bộ
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
