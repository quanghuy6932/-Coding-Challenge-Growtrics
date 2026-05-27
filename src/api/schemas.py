from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class VideoRequestCreate(BaseModel):
    """Schema tiếp nhận yêu cầu sinh video từ phía Client."""
    query: str = Field(
        ..., 
        description="Câu hỏi khoa học hóa học cần giải thích.",
        json_schema_extra={"example": "Why do atoms form covalent bonds?"}
    )

class VideoJobResponse(BaseModel):
    """Schema phản hồi thông tin trạng thái và số liệu của một Job."""
    job_id: str
    query: str
    status: str
    created_at: datetime
    updated_at: datetime
    estimated_duration_secs: float
    cost_usd: float
    error_message: Optional[str] = None
    artifact_url: Optional[str] = None

class VideoJobListResponse(BaseModel):
    """Schema danh sách toàn bộ các Job."""
    jobs: List[VideoJobResponse]