from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from .dependencies import get_job_service
from .schemas import CreateLyricsJobRequest, LyricsJobAcceptedResponse, LyricsJobStatusResponse
from .service import LyricsSyncJobService

router = APIRouter()


@router.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/v1/lyrics/jobs", response_model=LyricsJobAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
def create_job(
    request: CreateLyricsJobRequest,
    background_tasks: BackgroundTasks,
    service: LyricsSyncJobService = Depends(get_job_service),
) -> LyricsJobAcceptedResponse:
    accepted = service.submit_job(request)
    background_tasks.add_task(service.process_job, accepted.job_id)
    return accepted


@router.get("/v1/lyrics/jobs/{job_id}", response_model=LyricsJobStatusResponse)
def get_job(job_id: str, service: LyricsSyncJobService = Depends(get_job_service)) -> LyricsJobStatusResponse:
    result = service.get_job(job_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return result
