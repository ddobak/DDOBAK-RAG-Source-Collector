"""
프로젝트 설정 관리
환경변수와 각종 설정값들을 중앙에서 관리합니다.
"""
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class ColoredFormatter(logging.Formatter):
    """로그 레벨별로 색상을 적용하는 포매터"""
    
    # ANSI 색상 코드와 스타일
    COLORS = {
        'DEBUG': '\033[96m',    # 밝은 시안색 (Bright Cyan)
        'INFO': '\033[92m',     # 밝은 초록색 (Bright Green)  
        'WARNING': '\033[93m',  # 밝은 노란색 (Bright Yellow)
        'ERROR': '\033[91m',    # 밝은 빨간색 (Bright Red)
        'CRITICAL': '\033[95m', # 밝은 마젠타색 (Bright Magenta)
        'RESET': '\033[0m',     # 색상 리셋
        'BOLD': '\033[1m',      # 볼드
        'DIM': '\033[2m'        # 어둡게
    }
    
    def format(self, record):
        # 원본 포맷 적용
        log_message = super().format(record)
        
        # 로그 레벨에 따른 색상 가져오기
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        bold = self.COLORS['BOLD']
        dim = self.COLORS['DIM']
        
        # 시간 부분을 어둡게 처리
        parts = log_message.split(' - ')
        if len(parts) >= 4:
            timestamp = parts[0]
            logger_name = parts[1] 
            level_name = parts[2]
            message = ' - '.join(parts[3:])
            
            # 색상 적용된 메시지 구성
            colored_message = (
                f"{dim}{timestamp}{reset} - "
                f"{dim}{logger_name}{reset} - "
                f"{color}{bold}{level_name}{reset} - "
                f"{color}{message}{reset}"
            )
        else:
            # 기본 fallback
            colored_message = f"{color}{bold}{log_message}{reset}"
        
        return colored_message


class Settings:
    """애플리케이션 설정 클래스"""
    
    def __init__(self):
        # 프로젝트 루트 경로
        self.ROOT_DIR = Path(__file__).parent

        self.DATETIME = datetime.now().strftime("%m%d%H%M")
        
        # 데이터 저장 경로
        self.DATA_DIR = self.ROOT_DIR / "data"
        self.DATA_DIR.mkdir(exist_ok=True)
        
        # 로그 설정
        self.LOG_DIR = self.ROOT_DIR / "logs"
        self.LOG_DIR.mkdir(exist_ok=True)
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        # 로거 설정
        self._setup_logging()

        # AWS 설정
        self.AWS_PROFILE = os.getenv("AWS_PROFILE")
        self.AWS_REGION = os.getenv("AWS_REGION")
        self.AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
        self.AWS_LOCAL_PATH = self.ROOT_DIR / "s3_test"
        
    
    def _setup_logging(self):
        """로깅 설정을 초기화합니다."""
        # 현재 시간으로 로그 파일명 생성 (MMDDHHMM.log)
        log_filename = f"{self.DATETIME}.log"
        
        # 콘솔 핸들러 (색상 포매터 적용)
        console_handler = logging.StreamHandler()
        console_formatter = ColoredFormatter(self.LOG_FORMAT)
        console_handler.setFormatter(console_formatter)
        
        # 파일 핸들러 (일반 포매터 적용)
        file_handler = logging.FileHandler(
            self.LOG_DIR / log_filename, 
            encoding='utf-8'
        )
        file_formatter = logging.Formatter(self.LOG_FORMAT)
        file_handler.setFormatter(file_formatter)
        
        # 루트 로거 설정
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.LOG_LEVEL.upper()))
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
        # AWS credential 관련 로그 레벨을 WARNING으로 설정하여 INFO 로그 숨김
        logging.getLogger('botocore.credentials').setLevel(logging.WARNING)
        logging.getLogger('boto3.resources').setLevel(logging.WARNING)
    
    def get_logger(self, name: str) -> logging.Logger:
        """모듈별 로거를 반환합니다."""
        return logging.getLogger(name)


# 전역 설정 인스턴스
config = Settings()