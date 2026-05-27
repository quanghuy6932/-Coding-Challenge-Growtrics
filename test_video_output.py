import asyncio
import os
from src.infrastructure.persistence.in_memory import InMemoryJobRepository
from src.infrastructure.media.structured_engine import StructuredMediaEngine
from src.core.orchestrator import VideoJobOrchestrator
from config.settings import settings

async def test():
    repo = InMemoryJobRepository()
    engine = StructuredMediaEngine()
    orchestrator = VideoJobOrchestrator(repo, engine)
    
    query = 'How does the pH scale work?'
    job = await orchestrator.submit_video_request(query)
    print(f'[OK] Job submitted: {job.job_id}')
    print(f'[OK] Storage dir: {settings.STORAGE_DIR}')
    
    await orchestrator.start_background_generation(job.job_id)
    print(f'[OK] Generation completed')
    
    updated_job = await orchestrator.get_job_status(job.job_id)
    print(f'[OK] Job status: {updated_job.status}')
    if updated_job.artifact:
        print(f'[OK] Artifact path: {updated_job.artifact.audio_file_path}')
    
    # List storage folder
    if os.path.exists(settings.STORAGE_DIR):
        files = os.listdir(settings.STORAGE_DIR)
        print(f'\n[Files in storage directory]:')
        if files:
            for f in files:
                fpath = os.path.join(settings.STORAGE_DIR, f)
                size = os.path.getsize(fpath)
                print(f'  - {f} ({size} bytes)')
        else:
            print(f'  (empty)')
    else:
        print(f'[ERROR] Storage dir not found')

asyncio.run(test())
