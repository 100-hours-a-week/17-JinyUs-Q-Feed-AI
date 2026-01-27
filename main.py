from fastapi import FastAPI
from routers import stt,feedback
from exceptions.handlers import app_exception_handler, global_exception_handler
from exceptions.exceptions import AppException
from core.config import get_settings
from core.logging import setup_logging
from core.logging import setup_logging, TraceIdMiddleware


#로깅 설정
settings = get_settings()
setup_logging(environment=settings.environment)

app = FastAPI()
app.add_middleware(TraceIdMiddleware) 

app.include_router(stt.router, prefix="/ai", tags=["stt"])
app.include_router(feedback.router, prefix="/ai", tags=["feedback"])

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

@app.get("/ai")
async def root():
    return {"message": "FastAPI is running"}