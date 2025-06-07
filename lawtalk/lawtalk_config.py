from dotenv import load_dotenv
import os
from config import config as base_config

load_dotenv()

BASE_URL = "https://www.lawtalk.co.kr"

class LawtalkConfig:
    """로톡 크롤러 설정 클래스 (기존 config 통합)"""
    
    def __init__(self, base_config):
        # 기존 config의 모든 속성을 복사
        for attr_name in dir(base_config):
            if not attr_name.startswith('_'):
                setattr(self, attr_name, getattr(base_config, attr_name))
        
        # 로톡 관련 설정 추가
        self.REQUEST_INTERVAL = 1
        self.BASE_URL = BASE_URL
        
        # 로톡 관련 헤더
        self.BASE_HEADERS = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        }
        
        # 로톡 API URLs
        self.LOGIN_URL = f"{BASE_URL}/api/session"
        self.LOGIN_REFERER = f"{BASE_URL}/sign-in"
        self.CONSULTATION_URL = f"{BASE_URL}/api/qna/question/search"
        
        # 로그인 정보
        self.LOGIN_PAYLOAD = {
            "username": os.getenv("LAWTALK_ID"),
            "password": os.getenv("LAWTALK_PW"), 
            "remember": False
        }
        
        # 상담 사례 검색 기본 파라미터 예시
        self.CONSULTATION_PAYLOAD_KEYS = {
            "blindFilter": "true",
            "filter": "answers", 
            "limit": "10",
            "offset": "0",  # 나머지 고정하고, 얘만 변경하여 pagination
            "sort": "recentAnswer",
            "withRelated": "answers,lawyer,answerRevisions,keywords"
        }

        # 상담 사례 탐색 페이지 리밋
        self.CONSULTATION_OFFSET_START = 0
        self.CONSULTATION_OFFSET_END = 5

# 통합 config 인스턴스 (기존 config + 로톡 설정)
config = LawtalkConfig(base_config)