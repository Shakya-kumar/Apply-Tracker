from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.integrations import router as integrations_router
from app.api.jobs import router as jobs_router
from app.api.profile import router as profile_router
from app.api.resumes import router as resumes_router
from app.api.tailoring import router as tailoring_router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(profile_router, prefix=settings.api_v1_prefix)
app.include_router(resumes_router, prefix=settings.api_v1_prefix)
app.include_router(jobs_router, prefix=settings.api_v1_prefix)
app.include_router(dashboard_router, prefix=settings.api_v1_prefix)
app.include_router(integrations_router, prefix=settings.api_v1_prefix)
app.include_router(tailoring_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}
