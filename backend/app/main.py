"""
app/main.py

This is the SHARED entrypoint of the whole backend — every module's
router gets included here. Since this file is shared, always give the
team a heads-up in chat before editing it (see README rule #2).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.auth.routes import router as auth_router
from app.organizations.routes import router as organizations_router
from app.exams.routes import router as exams_router

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(organizations_router)
app.include_router(exams_router)

# Other members will add their routers here, e.g.:
# app.include_router(questions_router)
# app.include_router(attempts_router)
# app.include_router(security_router)
# app.include_router(analytics_router)


@app.get("/health")
def health_check():
    """Simple endpoint to confirm the API is up (used by docker-compose/CI)."""
    return {"status": "ok", "app": settings.APP_NAME}


# --- Question bank (Member 3) ---
from app.questions.router import router as questions_router  # noqa: E402
app.include_router(questions_router, prefix="/api/v1")

from app.attempts.routes import router as attempts_router  # noqa: E402
from app.grading.routes import router as results_router  # noqa: E402
app.include_router(attempts_router)
app.include_router(results_router)
