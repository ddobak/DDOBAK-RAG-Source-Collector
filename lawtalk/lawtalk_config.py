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
        self.SOLVED_CASES_URL = f"{BASE_URL}/api/posts/search"
        self.GUIDE_POSTS_URL = f"{BASE_URL}/api/posts/search"
        
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

        self.CATEGORY_IDS = {
            "재산범죄": "62a9f91a9fcafe948d73ea0c",
            "부동산_임대차": "62a9f91a9fcafe948d73ea12",
            "형사철자": "62a9f91a9fcafe948d73ea0e",
            "명예훼손_모욕": "62a9f91a9fcafe948d73ea10",
            "금전_계약 문제": "62a9f91a9fcafe948d73ea13",
            "회사": "62a9f91b9fcafe948d73ea17",
            "의료_세금_행정": "62a9f91b9fcafe948d73ea18",
            "IT_지식재산_금융": "62a9f91b9fcafe948d73ea19"
        }

        # 해결된 사례 검색 기본 파라미터
        self.SOLVED_CASES_PAYLOAD_KEYS = {
            "category": "",  # 사용자 제공 카테고리 ID
            "limit": "10",
            "offset": "0",  # 페이지네이션을 위해 변경
            "sort": "createdAt",
            "type": "case"
        }

        # 가이드 포스트 검색 기본 파라미터
        self.GUIDE_POSTS_PAYLOAD_KEYS = {
            "category": "",  # 사용자 제공 카테고리 ID
            "limit": "9",
            "offset": "0",  # 페이지네이션을 위해 변경
            "showScms": "true",
            "sort": "createdAt",
            "type": "essay,guide"
        }

        # 상담 사례 탐색 페이지 리밋
        self.CONSULTATION_OFFSET_START = 0
        self.CONSULTATION_OFFSET_END = 1000
        
        # 해결된 사례 탐색 페이지 리밋
        self.SOLVED_CASES_OFFSET_START = 0
        self.SOLVED_CASES_OFFSET_END = 1000

        # 가이드 포스트 탐색 페이지 리밋
        self.GUIDE_POSTS_OFFSET_START = 0
        self.GUIDE_POSTS_OFFSET_END = 9999

# 통합 config 인스턴스 (기존 config + 로톡 설정)
config = LawtalkConfig(base_config)