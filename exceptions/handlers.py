# exceptions/handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse

from exceptions.exceptions import AppException


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.message,
            "data": None
        }
    )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """예상치 못한 에러 - 동일한 포맷 유지"""
    # logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "message": "exc.message",
            "data": None
        }
    )
