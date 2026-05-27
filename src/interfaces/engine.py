from abc import ABC, abstractmethod
from src.core.models import VideoArtifactManifest


class IMediaGenerationEngine(ABC):
    """Port cho Media Generation Engine — interface để sinh manifest từ query."""

    @abstractmethod
    async def generate_educational_content(
        self, query: str, job_id: str
    ) -> VideoArtifactManifest:
        """
        Sinh VideoArtifactManifest từ chemistry concept query.
        
        Args:
            query: Chemistry concept question
            job_id: Job ID để truy vấn/logging
            
        Returns:
            VideoArtifactManifest chứa timeline, cost, metadata, v.v.
            
        Raises:
            GenerationPipelineException: nếu sinh manifest thất bại
        """
        pass