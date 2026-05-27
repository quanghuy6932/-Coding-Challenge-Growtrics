from abc import ABC, abstractmethod
from typing import List, Optional
from src.core.models import VideoJob


class IJobRepository(ABC):
    """Cổng giao tiếp (Port) quy định các thao tác lưu trữ và truy vấn Job trạng thái."""

    @abstractmethod
    async def save(self, job: VideoJob) -> VideoJob:
        """Lưu hoặc cập nhật một job. Trả về job sau khi persist."""
        pass

    @abstractmethod
    async def get_by_id(self, job_id: str) -> Optional[VideoJob]:
        """Lấy job theo ID. Trả None nếu không tìm thấy."""
        pass

    @abstractmethod
    async def list_all(self) -> List[VideoJob]:
        """Lấy danh sách tất cả jobs."""
        pass