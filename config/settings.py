import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Định nghĩa thư mục lưu trữ file kết quả (Artifacts)
    STORAGE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../storage/artifacts"))
    
    # Giả lập thời gian xử lý AI (để kiểm tra cơ chế Async)
    GENERATION_SIMULATION_LATENCY_SECS: float = 4.0
    MAX_GENERATION_RETRIES: int = 3

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()