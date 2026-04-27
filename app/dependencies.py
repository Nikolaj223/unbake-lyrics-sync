from __future__ import annotations

from functools import lru_cache

from .config import get_settings
from .pipeline.orchestrator import LyricsSyncOrchestrator
from .pipeline.preprocessing import AudioPreprocessor
from .pipeline.retrieval import LRCLibRetriever
from .pipeline.transcription import WhisperXTranscriber
from .repository import InMemoryJobRepository
from .service import LyricsSyncJobService


@lru_cache(maxsize=1)
def get_job_service() -> LyricsSyncJobService:
    settings = get_settings()
    repository = InMemoryJobRepository()
    orchestrator = LyricsSyncOrchestrator(
        preprocessor=AudioPreprocessor(
            tmp_dir=settings.tmp_dir,
            max_audio_duration_sec=settings.max_audio_duration_sec,
        ),
        transcriber=WhisperXTranscriber(settings),
        retriever=LRCLibRetriever(settings.catalog_base_url),
    )
    return LyricsSyncJobService(repository=repository, orchestrator=orchestrator)
