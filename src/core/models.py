from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, UUID4
import uuid

class JobStatus(str, Enum):
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoSegment(BaseModel):
    """Đại diện cho một phân cảnh cụ thể trong dòng thời gian của video giáo dục."""
    timestamp_start: float = Field(..., description="Thời điểm bắt đầu phân cảnh (giây)")
    timestamp_end: float = Field(..., description="Thời điểm kết thúc phân cảnh (giây)")
    title: str = Field(..., description="Tiêu đề phân cảnh")
    voiceover_script: str = Field(..., description="Kịch bản lời thoại chi tiết mà AI sẽ đọc (hoặc giả lập đọc)")
    visual_elements: List[str] = Field(..., description="Danh sách các phần tử đồ họa xuất hiện trên màn hình (ví dụ: 'Mô hình phân tử H2O', 'Đồ thị pH')")


class VideoArtifactManifest(BaseModel):
    """Cấu trúc dữ liệu chi tiết của sản phẩm video hoàn chỉnh."""
    concept_query: str = Field(..., description="Câu hỏi gốc của học viên")
    domain_topic: str = Field("Chemistry", description="Chủ đề khoa học (mở rộng hệ STEM)")
    total_duration_secs: float = Field(..., description="Tổng thời lượng video")
    production_cost_usd: float = Field(..., description="Chi phí thực tế ước tính để tạo ra video")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    timeline: List[VideoSegment] = Field(..., description="Chuỗi các phân cảnh bài học chi tiết từ đầu đến cuối")
    audio_file_path: Optional[str] = Field(None, description="Đường dẫn file âm thanh tổng hợp nếu có")
    meta_tags: Dict[str, Any] = Field(default_factory=dict, description="Metadata mở rộng để lưu thông tin mô hình AI")


class VideoJob(BaseModel):
    """Thực thể cốt lõi quản lý vòng đời và trạng thái của một lượt yêu cầu video."""
    job_id: str = Field(default_factory=lambda: f"job_{uuid.uuid4().hex[:12]}")
    query: str
    status: JobStatus = JobStatus.SUBMITTED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_duration_secs: float = 0.0
    cost_usd: float = 0.0
    error_message: Optional[str] = None
    artifact: Optional[VideoArtifactManifest] = None

    def transition_to(self, new_status: JobStatus):
        """Hàm dịch chuyển trạng thái an toàn (State Machine Engine)."""
        # Rào chắn bảo vệ logic dịch chuyển trạng thái
        if self.status == JobStatus.COMPLETED or self.status == JobStatus.FAILED:
            raise RuntimeError(f"Cannot change state of a finished job. Current status: {self.status}")
        
        self.status = new_status
        self.updated_at = datetime.utcnow()