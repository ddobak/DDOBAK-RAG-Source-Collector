"""
프로젝트 설정 관리
환경변수와 각종 설정값들을 중앙에서 관리합니다.
"""
import os
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
        
        # 데이터 저장 경로
        self.DATA_DIR = self.ROOT_DIR / "data"
        self.DATA_DIR.mkdir(exist_ok=True)
        
        # 로그 설정
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        # 각 사이트별 설정
        self.lawtalk = self._load_lawtalk_config()
    
    def _load_lawtalk_config(self) -> dict:
        """로톡 관련 설정 로드"""
        return {
            "base_url": os.getenv("LAWTALK_BASE_URL", "https://www.lawtalk.co.kr"),
            "output_dir": self.DATA_DIR / "lawtalk",
        }
    


# 전역 설정 인스턴스
settings = Settings() 