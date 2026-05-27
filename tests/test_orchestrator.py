import pytest
import asyncio
import os
from src.infrastructure.persistence.in_memory import InMemoryJobRepository
from src.infrastructure.media.structured_engine import StructuredMediaEngine
from src.core.orchestrator import VideoJobOrchestrator
from src.core.models import JobStatus
from src.core.exceptions import JobNotFoundException, GenerationPipelineException
from config.settings import settings

@pytest.mark.asyncio
async def test_job_submission_and_lifecycle():
    """Kiểm thử luồng tiếp nhận Job và dịch chuyển trạng thái tuần tự."""
    # Khởi tạo hạ tầng độc lập cho môi trường Test
    repo = InMemoryJobRepository()
    engine = StructuredMediaEngine()
    orchestrator = VideoJobOrchestrator(repo, engine)
    
    # Cấu hình giảm thời gian delay xuống tối thiểu để test chạy nhanh
    settings.GENERATION_SIMULATION_LATENCY_SECS = 0.1

    # 1. Test Gửi yêu cầu (Submit)
    query = "How does the pH scale work?"
    job = await orchestrator.submit_video_request(query)
    
    assert job.job_id is not None
    assert job.status == JobStatus.SUBMITTED
    assert job.query == query

    # 2. Chạy Worker ngầm và kiểm tra chuyển dịch trạng thái hoàn tất
    await orchestrator.start_background_generation(job.job_id)
    
    updated_job = await orchestrator.get_job_status(job.job_id)
    assert updated_job.status == JobStatus.COMPLETED
    assert updated_job.estimated_duration_secs == 60.0
    assert updated_job.cost_usd == 0.015
    assert updated_job.artifact is not None
    assert updated_job.artifact.concept_query == query
    assert updated_job.artifact.total_duration_secs == 60.0
    assert updated_job.artifact.production_cost_usd == 0.015

@pytest.mark.asyncio
async def test_unsupported_topic_guardrail():
    """Kiểm thử rào chắn bảo vệ (Guardrail) khi gửi câu hỏi sai chủ đề hóa học."""
    repo = InMemoryJobRepository()
    engine = StructuredMediaEngine()
    orchestrator = VideoJobOrchestrator(repo, engine)
    
    # Gửi câu hỏi về toán học (không nằm trong 3 câu hỏi quy định)
    invalid_query = "What is 1 + 1?"
    job = await orchestrator.submit_video_request(invalid_query)
    
    # Chạy xử lý ngầm, hệ thống phải bắt được lỗi guardrail và chuyển trạng thái FAILED
    await orchestrator.start_background_generation(job.job_id)
    
    failed_job = await orchestrator.get_job_status(job.job_id)
    assert failed_job.status == JobStatus.FAILED
    assert "Unsupported STEM topic" in failed_job.error_message
