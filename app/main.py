from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="Unbake Lyrics Sync API", version="0.1.0")

# Imported late to avoid circular import at module load time.
from .routes import router  # noqa: E402

app.include_router(router)
