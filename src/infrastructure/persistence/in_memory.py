import asyncio
from typing import List, Optional
from src.interfaces.repository import IJobRepository
from src.core.models import VideoJob

class InMemoryJobRepository(IJobRepository):
    """
    Adapter lưu trữ dữ liệu trực tiếp trong RAM.
    Được trang bị cơ chế khóa Async Lock chống tranh chấp tài nguyên (Race Condition).
    """
    def __init__(self):
        self._storage = {}
        self._lock = asyncio.Lock()

    async def save(self, job: VideoJob) -> VideoJob:
        """Lưu mới hoặc cập nhật trạng thái của Job vào RAM một cách an toàn."""
        async with self._lock:
            # Lưu bản sao deep copy của object để tránh thay đổi ngoài ý muốn ở luồng khác
            self._storage[job.job_id] = job.model_copy(deep=True)
            return job.model_copy(deep=True)

    async def get_by_id(self, job_id: str) -> Optional[VideoJob]:
        """Truy vấn thông tin Job theo ID."""
        async with self._lock:
            job = self._storage.get(job_id)
            if job:
                return job.model_copy(deep=True)
            return None

    async def list_all(self) -> List[VideoJob]:
        """Lấy toàn bộ danh sách các Job hiện có."""
        async with self._lock:
            return [job.model_copy(deep=True) for job in self._storage.values()]
