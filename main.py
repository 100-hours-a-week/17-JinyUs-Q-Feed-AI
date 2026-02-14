from fastapi import FastAPI

from exceptions.handlers import app_exception_handler, global_exception_handler
from exceptions.exceptions import AppException
from core.config import get_settings
from core.logging import setup_logging, RequestLoggingMiddleware

settings = get_settings()
settings.configure_langsmith() 
setup_logging(environment=settings.ENVIRONMENT, log_dir=settings.log_directory)

from routers import stt,feedback

app = FastAPI()
app.add_middleware(RequestLoggingMiddleware)

app.include_router(stt.router, prefix="/ai", tags=["stt"])
app.include_router(feedback.router, prefix="/ai", tags=["feedback"])

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

@app.get("/ai")
async def root():
    return {"message": "FastAPI is running"}