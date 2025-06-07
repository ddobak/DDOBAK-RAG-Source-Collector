from dotenv import load_dotenv
import os
from config import config as base_config

load_dotenv()

BASE_URL = "https://www.easylaw.go.kr"

class EasylawConfig:
    """이지로 크롤러 설정 클래스 (기존 config 통합)"""
    
    def __init__(self, base_config):
        # 기존 config의 모든 속성을 복사
        for attr_name in dir(base_config):
            if not attr_name.startswith('_'):
                setattr(self, attr_name, getattr(base_config, attr_name))
        
        # 이지로 관련 설정 추가
        self.REQUEST_INTERVAL = 0.5
        self.BASE_URL = BASE_URL
        
        # 이지로 관련 헤더
        self.BASE_HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Origin': BASE_URL,
            'Referer': f'{BASE_URL}/CSP/OnhunqueansLstRetrieve.laf?search_put='
        }
        
        # 이지로 API URLs
        self.QNA_LIST_URL = f"{BASE_URL}/CSP/OnhunqueansLstRetrieve.laf"
        self.QNA_DETAIL_URL = f"{BASE_URL}/CSP/OnhunqueansInfoRetrieve.laf"
        
        # Q&A 목록 검색 기본 파라미터
        self.QNA_LIST_PAYLOAD_KEYS = {
            'curPage': '1',  # 페이지네이션을 위해 변경
            'sch': '',       # 검색어 (선택사항)
            'pageTpe': '20'  # 페이지당 아이템 수
        }
        
        # 페이지네이션 설정
        self.PAGE_START = 1
        self.PAGE_SIZE = 20
        self.MAX_CONSECUTIVE_EMPTY_PAGES = 3  # 연속으로 빈 페이지가 3번 나오면 종료
        
        # 타임아웃 설정
        self.REQUEST_TIMEOUT = 30
        
        # 데이터 저장 설정
        self.OUTPUT_SUBDIR = "qa_data"
        self.JSON_FILENAME = "easylaw_qa_complete.json"
        
        # S3 저장 설정
        self.S3_BUCKET_NAME = "ddobak-rag-source"
        self.S3_BASE_PREFIX = "easylaw"
        self.S3_SIMPLE_FILENAME = "easylaw_data_simple.json"
        self.S3_DETAIL_FILENAME = "easylaw_data_detail.json"
        
        # 카테고리 매핑 정보 (category_id -> category_name)
        self.CATEGORY_MAPPING = {
            '25': '가정법률',
            '89': '아동-청소년_교육',
            '84': '부동산_임대차',
            '92': '금융_보험',
            '83': '사업',
            '91': '창업',
            '100': '무역_출입국',
            '88': '소비자',
            '87': '문화_여가생활',
            '85': '민형사_소송',
            '90': '교통_운전',
            '82': '근로_노동',
            '97': '복지',
            '81': '국방_보훈',
            '94': '정보통신_기술',
            '96': '환경_에너지',
            '86': '사회안전_범죄',
            '95': '국가_및_지자체'
        }

# 통합 config 인스턴스 (기존 config + 이지로 설정)
config = EasylawConfig(base_config) 