"""
app/main.py

This is the SHARED entrypoint of the whole backend — every module's
router gets included here. Since this file is shared, always give the
team a heads-up in chat before editing it (see README rule #2).

Below, only the auth and organizations routers (Member 1's scope) are
wired in as an example. Other members will add their own:
    from app.exams.routes import router as exams_router
    app.include_router(exams_router)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.auth.routes import router as auth_router
from app.organizations.routes import router as organizations_router

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

# Other members will add their routers here, e.g.:
# app.include_router(exams_router)
# app.include_router(questions_router)
# app.include_router(attempts_router)
# app.include_router(security_router)
# app.include_router(analytics_router)


@app.get("/health")
def health_check():
    """Simple endpoint to confirm the API is up (used by docker-compose/CI)."""
    return {"status": "ok", "app": settings.APP_NAME}
