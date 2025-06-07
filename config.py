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
        
        # 루트 로거 설정
        logging.basicConfig(
            level=getattr(logging, self.LOG_LEVEL.upper()),
            format=self.LOG_FORMAT,
            handlers=[
                logging.StreamHandler(),  # 콘솔 출력
                logging.FileHandler(
                    self.LOG_DIR / log_filename, 
                    encoding='utf-8'
                )  # 파일 출력
            ]
        )
    
    def get_logger(self, name: str) -> logging.Logger:
        """모듈별 로거를 반환합니다."""
        return logging.getLogger(name)


# 전역 설정 인스턴스
config = Settings()