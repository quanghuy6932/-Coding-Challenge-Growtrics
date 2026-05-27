import asyncio
import logging
import os
from datetime import datetime, timezone
 
from src.interfaces.repository import IJobRepository
from src.interfaces.engine import IMediaGenerationEngine
from src.core.models import VideoJob, JobStatus
from src.core.exceptions import JobNotFoundException, GenerationPipelineException
from config.settings import settings
 
logger = logging.getLogger(__name__)
 
 
class VideoJobOrchestrator:
 
    def __init__(self, repository: IJobRepository, media_engine: IMediaGenerationEngine):
        self.repository = repository
        self.media_engine = media_engine
        os.makedirs(settings.STORAGE_DIR, exist_ok=True)
 
    # ------------------------------------------------------------------
    # Public: accept a new video request
    # ------------------------------------------------------------------
 
    async def submit_video_request(self, query: str) -> VideoJob:
        """
        Creates a new VideoJob in SUBMITTED state and persists it.
        Returns immediately — background processing is triggered separately.
        """
        job = VideoJob(query=query, status=JobStatus.SUBMITTED)
        await self.repository.save(job)
        logger.info(f"[Job {job.job_id}] Submitted — query: '{query}'")
        return job
 
    # ------------------------------------------------------------------
    # Background worker: drives the full generation pipeline
    # ------------------------------------------------------------------
 
    async def start_background_generation(self, job_id: str):
        """
        Executes the full video generation pipeline for a given job.
        Called as a FastAPI BackgroundTask — runs after the 202 response is sent.
 
        State transitions:
          SUBMITTED → PROCESSING → COMPLETED
                                 → FAILED (on unrecoverable error)
        """
        job = await self.repository.get_by_id(job_id)
        if not job:
            logger.error(f"[Job {job_id}] Not found in repository — worker exiting.")
            return
 
        # --- Transition to PROCESSING ---
        try:
            job.transition_to(JobStatus.PROCESSING)
            await self.repository.save(job)
            logger.info(f"[Job {job_id}] Processing started.")
        except Exception as state_err:
            logger.error(f"[Job {job_id}] Failed to transition to PROCESSING: {state_err}")
            return
 
        # --- Retry loop with exponential backoff ---
        attempts = 0
        max_retries = settings.MAX_GENERATION_RETRIES
        manifest = None
        last_error: Exception | None = None
 
        while attempts < max_retries:
            try:
                attempts += 1
                logger.info(f"[Job {job_id}] Generation attempt {attempts}/{max_retries}")
 
                manifest = await self.media_engine.generate_educational_content(
                    query=job.query,
                    job_id=job_id,
                )
                break  # success — exit retry loop
 
            except GenerationPipelineException as g_err:
                if g_err.error_code == "UNSUPPORTED_STEM_TOPIC":
                    # Non-retryable: guardrail violation — fail immediately
                    logger.warning(f"[Job {job_id}] Guardrail rejected query: {g_err.message}")
                    last_error = g_err
                    break
 
                last_error = g_err
                logger.warning(
                    f"[Job {job_id}] Attempt {attempts} failed ({g_err.error_code}): {g_err.message}"
                )
                if attempts < max_retries:
                    backoff = 2.0 ** attempts
                    logger.info(f"[Job {job_id}] Retrying in {backoff:.1f}s...")
                    await asyncio.sleep(backoff)
 
            except Exception as unexpected_err:
                last_error = unexpected_err
                logger.exception(f"[Job {job_id}] Unexpected error on attempt {attempts}: {unexpected_err}")
                if attempts < max_retries:
                    await asyncio.sleep(2.0 ** attempts)
 
        # --- Persist outcome ---
        if manifest is not None:
            await self._complete_job(job_id, manifest)
        else:
            await self._fail_job(job_id, last_error)
 
    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------
 
    async def get_job_status(self, job_id: str) -> VideoJob:
        job = await self.repository.get_by_id(job_id)
        if not job:
            raise JobNotFoundException(job_id)
        return job
 
    async def list_all_jobs(self) -> list[VideoJob]:
        return await self.repository.list_all()
 
    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
 
    async def _complete_job(self, job_id: str, manifest) -> None:
        """Marks a job COMPLETED and attaches the generated manifest."""
        job = await self.repository.get_by_id(job_id)
        if not job:
            return
 
        job.artifact = manifest
        job.estimated_duration_secs = manifest.total_duration_secs
        job.cost_usd = manifest.production_cost_usd
        job.transition_to(JobStatus.COMPLETED)
        await self.repository.save(job)
 
        logger.info(
            f"[Job {job_id}] COMPLETED — "
            f"duration={manifest.total_duration_secs}s, "
            f"cost=${manifest.production_cost_usd:.4f}, "
            f"artifact={manifest.audio_file_path}"
        )
 
    async def _fail_job(self, job_id: str, error: Exception | None) -> None:
        """Marks a job FAILED and records the error message."""
        job = await self.repository.get_by_id(job_id)
        if not job:
            return
 
        error_msg = str(error) if error else "Unknown generation failure"
        job.error_message = error_msg
        job.status = JobStatus.FAILED
        job.updated_at = datetime.now(timezone.utc)
        await self.repository.save(job)
 
        logger.error(f"[Job {job_id}] FAILED — {error_msg}")