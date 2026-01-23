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
