import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

def setup_logging(environment: str = "local", log_dir: str = "logs") -> None:
    """환경별 로깅 설정"""
    log_level = logging.DEBUG if environment == "local" else logging.INFO

    #포맷 정의
    log_format = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
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
        root_logger.addHandler(error_handler)

    # AI 지표 로거 (별도)
    metrics_logger = logging.getLogger("metrics")
    metrics_logger.setLevel(logging.INFO)
    metrics_logger.propagate = False  # 루트로 전파 안 함
    
    metrics_console = logging.StreamHandler(sys.stdout)
    metrics_console.setFormatter(formatter)
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
    
    logging.info(f"로깅 설정 완료: environment={environment}, level={logging.getLevelName(log_level)}")

def get_logger(name: str) -> logging.Logger:
    """로거 인스턴스 반환"""
    return logging.getLogger(name)

def get_metrics_logger() -> logging.Logger:
    """AI 지표 로거 반환"""
    return logging.getLogger("metrics")