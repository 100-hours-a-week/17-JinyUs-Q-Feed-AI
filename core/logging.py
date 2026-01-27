import logging
import sys
import uuid
import time
import asyncio
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from contextvars import ContextVar
from functools import wraps
from typing import Callable, Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Trace ID context variable (요청 추적용)
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="-")

class TraceIdFilter(logging.Filter):
    """로그 레코드에 trace_id 추가"""
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = trace_id_var.get()
        return True
    
class TraceIdMiddleware(BaseHTTPMiddleware):
    """요청별 trace_id 자동 설정 미들웨어"""
    
    async def dispatch(self, request: Request, call_next):
        # 클라이언트가 보낸 trace_id 있으면 사용, 없으면 생성
        trace_id = request.headers.get("X-Trace-ID") or generate_trace_id()
        set_trace_id(trace_id)
        
        logger = get_logger("middleware")
        logger.info(f"요청 시작 | {request.method} {request.url.path}")
        
        start_time = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        logger.info(f"요청 완료 | status={response.status_code} | {elapsed_ms:.2f}ms")
        return response

def setup_logging(environment: str = "local", log_dir: str = "logs") -> None:
    """환경별 로깅 설정"""
    log_level = logging.DEBUG if environment == "local" else logging.INFO

    #포맷 정의
    log_format = "[%(asctime)s] [%(levelname)s] [%(name)s] [%(trace_id)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, datefmt=date_format)

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 기존 핸들러 제거 (중복 방지)
    root_logger.handlers.clear()
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    console_handler.addFilter(TraceIdFilter())
    root_logger.addHandler(console_handler)


    # 프로덕션: 파일 핸들러 추가
    if environment == "production":
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # app.log (INFO 이상)
        app_handler = TimedRotatingFileHandler(
            log_path / "app.log",
            when="midnight",
            backupCount=30,
            encoding="utf-8"
        )
        app_handler.setFormatter(formatter)
        app_handler.setLevel(logging.INFO)
        app_handler.addFilter(TraceIdFilter())
        root_logger.addHandler(app_handler)
        
        # error.log (ERROR 이상)
        error_handler = TimedRotatingFileHandler(
            log_path / "error.log",
            when="midnight",
            backupCount=30,
            encoding="utf-8"
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        error_handler.addFilter(TraceIdFilter())
        root_logger.addHandler(error_handler)

    # AI 지표 로거 (별도)
    metrics_logger = logging.getLogger("metrics")
    metrics_logger.setLevel(logging.INFO)
    metrics_logger.propagate = False  # 루트로 전파 안 함
    
    metrics_console = logging.StreamHandler(sys.stdout)
    metrics_console.setFormatter(formatter)
    metrics_console.addFilter(TraceIdFilter())
    metrics_logger.addHandler(metrics_console)

    if environment == "production":
        metrics_handler = TimedRotatingFileHandler(
            log_path / "metrics.log",
            when="midnight",
            backupCount=30,
            encoding="utf-8"
        )
        metrics_handler.setFormatter(formatter)
        metrics_logger.addHandler(metrics_handler)
        metrics_logger.addFilter(TraceIdFilter())
    
    logging.info(f"로깅 설정 완료: environment={environment}, level={logging.getLevelName(log_level)}")

def get_logger(name: str) -> logging.Logger:
    """로거 인스턴스 반환"""
    return logging.getLogger(name)

def get_metrics_logger() -> logging.Logger:
    """AI 지표 로거 반환"""
    return logging.getLogger("metrics")

def generate_trace_id() -> str:
    """새 trace_id 생성 (8자리)"""
    return uuid.uuid4().hex[:8]


def set_trace_id(trace_id: str) -> None:
    """현재 컨텍스트에 trace_id 설정"""
    trace_id_var.set(trace_id)


def get_trace_id() -> str:
    """현재 trace_id 반환"""
    return trace_id_var.get()


def log_execution_time(logger: logging.Logger):
    """함수 실행 시간 로깅 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.info(f"{func.__name__} 완료 | {elapsed_ms:.2f}ms")
                return result
            except Exception as e:
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.error(f"{func.__name__} 실패 | {elapsed_ms:.2f}ms | {type(e).__name__}: {e}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.info(f"{func.__name__} 완료 | {elapsed_ms:.2f}ms")
                return result
            except Exception as e:
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.error(f"{func.__name__} 실패 | {elapsed_ms:.2f}ms | {type(e).__name__}: {e}")
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
