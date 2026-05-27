from src.infrastructure.persistence.in_memory import InMemoryJobRepository
from src.infrastructure.media.structured_engine import StructuredMediaEngine
from src.core.orchestrator import VideoJobOrchestrator

# Khởi tạo Singletons để giữ dữ liệu đồng nhất xuyên suốt vòng đời ứng dụng
_global_repository = InMemoryJobRepository()
_global_media_engine = StructuredMediaEngine()
_global_orchestrator = VideoJobOrchestrator(_global_repository, _global_media_engine)


def get_orchestrator() -> VideoJobOrchestrator:
    """Dependency Provider cấp phát thực thể điều phối Orchestrator cho các API Routers."""
    return _global_orchestrator