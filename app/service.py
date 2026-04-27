from __future__ import annotations

from uuid import uuid4

from .pipeline.orchestrator import LyricsSyncOrchestrator
from .repository import InMemoryJobRepository, JobRecord
from .schemas import CreateLyricsJobRequest, LyricsJobAcceptedResponse, LyricsJobStatusResponse


class LyricsSyncJobService:
    def __init__(self, repository: InMemoryJobRepository, orchestrator: LyricsSyncOrchestrator) -> None:
        self.repository = repository
        self.orchestrator = orchestrator

    def submit_job(self, request: CreateLyricsJobRequest) -> LyricsJobAcceptedResponse:
        job_id = str(uuid4())
        record = JobRecord(job_id=job_id, request=request)
        self.repository.create(record)
        return LyricsJobAcceptedResponse(
            job_id=job_id,
            status="queued",
            status_url=f"/v1/lyrics/jobs/{job_id}",
        )

    def process_job(self, job_id: str) -> None:
        record = self.repository.mark_processing(job_id)
        try:
            result = self.orchestrator.run(record.request)
            self.repository.mark_completed(job_id, result)
        except Exception as error:  # pragma: no cover - error path is intentionally broad
            self.repository.mark_failed(job_id, str(error))

    def get_job(self, job_id: str) -> LyricsJobStatusResponse | None:
        record = self.repository.get(job_id)
        return record.to_response() if record else None
