"""
App entrypoint. Owned by Member 1 (backend/app/core).
Each module below registers its own router — add yours in your own
module's __init__.py / router.py, don't edit other modules' routers here.
"""
from fastapi import FastAPI

app = FastAPI(title="CampusCert API")

# from app.auth.router import router as auth_router
# from app.organizations.router import router as org_router
# from app.exams.router import router as exams_router
# from app.questions.router import router as questions_router
# from app.attempts.router import router as attempts_router
# from app.security.router import router as security_router
# from app.analytics.router import router as analytics_router
# from app.ai.router import router as ai_router
# app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])

@app.get("/health")
def health():
    return {"status": "ok"}
