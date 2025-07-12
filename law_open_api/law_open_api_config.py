"""
법무부 오픈API 설정 파일
"""

import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 법무부 오픈API 설정
LAW_OPEN_API_CONFIG = {
    # API 기본 정보
    "api_key": os.getenv("LAW_OPEN_API_OC", ""),
    "base_url": "http://www.law.go.kr/DRF",
    
    # 판례 검색 API
    "precedent_search_url": "http://www.law.go.kr/DRF/lawSearch.do",
    "precedent_search_params": {
        "OC": os.getenv("LAW_OPEN_API_OC", ""),
        "target": "prec",
        "type": "HTML",  # HTML로 변경
        "search": "1",  # 1: 판례명, 2: 본문검색
        "display": "20",  # 페이지당 결과 수
        "page": "1",
        "sort": "ddes"  # 선고일자 내림차순
    },
    
    # 판례 본문 조회 API
    "precedent_detail_url": "http://www.law.go.kr/DRF/lawService.do",
    "precedent_detail_params": {
        "OC": os.getenv("LAW_OPEN_API_OC", ""),
        "target": "prec",
        "type": "HTML",  # HTML로 변경
    },
    
    # 검색 키워드 (RAG 최적화를 위한 법률 관련 키워드)
    "search_keywords": [
        "근로", "노동", "계약", "임대차", "전세", "월세"
    ],
    
    # 요청 설정
    "headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    },
    "timeout": 30,
    "request_delay": 0.2,  # 초
    "max_pages": 5,  # 키워드당 최대 페이지 수
    "fetch_detail": True,  # 본문 조회 여부
}

# 데이터 구조 정의
DATA_STRUCTURE = {
    "precedent": {
        "prec_id": "판례일련번호",
        "case_number": "사건번호", 
        "case_name": "사건명",
        "court_name": "법원명",
        "court_type_code": "법원종류코드",
        "judgment_date": "선고일자",
        "case_type_name": "사건종류명",
        "case_type_code": "사건종류코드",
        "judgment_type": "판결유형",
        "judgment": "선고",
        "judgment_summary": "판결요지",
        "judgment_point": "판시사항",
        "reference_law": "참조조문",
        "reference_case": "참조판례",
        "case_content": "판례내용",
        "data_source": "데이터출처명",
        "detail_link": "판례상세링크",
        "keywords": "검색키워드",
        "crawl_date": "크롤링일시"
    }
} 