import os
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import FileResponse
 
from src.api.schemas import VideoRequestCreate, VideoJobResponse, VideoJobListResponse
from src.api.dependencies import get_orchestrator
from src.core.orchestrator import VideoJobOrchestrator
from src.core.models import JobStatus
from src.core.exceptions import JobNotFoundException, GenerationPipelineException
from config.settings import settings
 
router = APIRouter(prefix="/api/v1/videos", tags=["AI Video Request Service"])
 
 
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
 
def _map_job_to_response(job) -> VideoJobResponse:
    """Maps a core VideoJob entity to the API response schema."""
    artifact_url = None
    if job.status == JobStatus.COMPLETED:
        artifact_url = f"/api/v1/videos/{job.job_id}/artifact"
 
    return VideoJobResponse(
        job_id=job.job_id,
        query=job.query,
        status=job.status.value,
        created_at=job.created_at,
        updated_at=job.updated_at,
        estimated_duration_secs=job.estimated_duration_secs,
        cost_usd=job.cost_usd,
        error_message=job.error_message,
        artifact_url=artifact_url,
    )
 
 
# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
 
@router.post(
    "",
    response_model=VideoJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a chemistry concept video request",
)
async def create_video_job(
    payload: VideoRequestCreate,
    background_tasks: BackgroundTasks,
    orchestrator: VideoJobOrchestrator = Depends(get_orchestrator),
):
    """
    Accepts a chemistry concept query and enqueues an async video-generation job.
    Returns 202 immediately with the new job ID and SUBMITTED status.
    Poll GET /{job_id} to track progress; retrieve the video via GET /{job_id}/artifact.
    """
    try:
        job = await orchestrator.submit_video_request(payload.query)
        background_tasks.add_task(orchestrator.start_background_generation, job.job_id)
        return _map_job_to_response(job)
    except GenerationPipelineException as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err.message)
 
 
@router.get(
    "",
    response_model=VideoJobListResponse,
    summary="List all video jobs",
)
async def list_all_jobs(
    orchestrator: VideoJobOrchestrator = Depends(get_orchestrator),
):
    """Returns the full list of submitted video jobs with their current statuses."""
    jobs = await orchestrator.list_all_jobs()
    return VideoJobListResponse(jobs=[_map_job_to_response(j) for j in jobs])
 
 
@router.get(
    "/{job_id}",
    response_model=VideoJobResponse,
    summary="Get status of a specific video job",
)
async def get_job_status(
    job_id: str,
    orchestrator: VideoJobOrchestrator = Depends(get_orchestrator),
):
    """Returns current state, progress metadata, and artifact URL once completed."""
    try:
        job = await orchestrator.get_job_status(job_id)
        return _map_job_to_response(job)
    except JobNotFoundException as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err.message)
 
 
@router.get(
    "/{job_id}/artifact",
    summary="Download the generated video artifact (MP4)",
)
async def get_video_artifact(
    job_id: str,
    orchestrator: VideoJobOrchestrator = Depends(get_orchestrator),
):
    """
    Downloads the generated .mp4 video artifact for a completed job.
 
    Returns:
        200 + MP4 file stream if job is COMPLETED and file exists.
        202 if job is still processing.
        404 if job ID is unknown.
        500 if the file is missing from the artifact store (data integrity error).
    """
    try:
        job = await orchestrator.get_job_status(job_id)
    except JobNotFoundException as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err.message)
 
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=f"Artifact not ready. Current job status: '{job.status.value}'. "
                   f"Poll GET /api/v1/videos/{job_id} until status is 'completed'.",
        )
 
    # The artifact path is stored on the manifest
    video_path = None
    if job.artifact and job.artifact.audio_file_path:
        video_path = job.artifact.audio_file_path
 
    # Fallback: derive path from job_id (backward compat)
    if not video_path:
        video_path = os.path.join(settings.STORAGE_DIR, f"{job_id}.mp4")
 
    if not os.path.exists(video_path):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Job is marked COMPLETED but the video file is missing from the artifact store. "
                "This indicates a storage integrity error."
            ),
        )
 
    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        filename=f"chemistry_{job_id}.mp4",
    )