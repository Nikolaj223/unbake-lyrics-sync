from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from .schemas import CreateLyricsJobRequest, LyricsPayload, LyricsJobStatusResponse

JobStatus = Literal["queued", "processing", "completed", "failed"]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class JobRecord:
    job_id: str
    request: CreateLyricsJobRequest
    status: JobStatus = "queued"
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    result: LyricsPayload | None = None
    error: str | None = None

    def to_response(self) -> LyricsJobStatusResponse:
        return LyricsJobStatusResponse(
            job_id=self.job_id,
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at,
            result=self.result,
            error=self.error,
        )


class InMemoryJobRepository:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}

    def create(self, record: JobRecord) -> JobRecord:
        self._jobs[record.job_id] = record
        return record

    def get(self, job_id: str) -> JobRecord | None:
        return self._jobs.get(job_id)

    def mark_processing(self, job_id: str) -> JobRecord:
        record = self._require(job_id)
        record.status = "processing"
        record.updated_at = utcnow()
        return record

    def mark_completed(self, job_id: str, result: LyricsPayload) -> JobRecord:
        record = self._require(job_id)
        record.status = "completed"
        record.result = result
        record.error = None
        record.updated_at = utcnow()
        return record

    def mark_failed(self, job_id: str, error: str) -> JobRecord:
        record = self._require(job_id)
        record.status = "failed"
        record.error = error
        record.updated_at = utcnow()
        return record

    def _require(self, job_id: str) -> JobRecord:
        record = self.get(job_id)
        if record is None:
            raise KeyError(f"Unknown job_id: {job_id}")
        return record
