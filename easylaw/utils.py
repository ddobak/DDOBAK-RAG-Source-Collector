import re
import time
from typing import Dict, List, Optional
from pathlib import Path

from bs4 import BeautifulSoup


def extract_url_parameters(url: str) -> Dict[str, str]:
    """URL에서 파라미터 추출"""
    params = {}
    
    # onhunqueSeq 추출
    seq_match = re.search(r'onhunqueSeq=(\d+)', url)
    if seq_match:
        params['question_id'] = seq_match.group(1)
    
    # onhunqnaAstSeq 추출  
    ast_seq_match = re.search(r'onhunqnaAstSeq=(\d+)', url)
    if ast_seq_match:
        params['category_id'] = ast_seq_match.group(1)
    
    return params


def build_full_url(base_url: str, relative_url: str) -> str:
    """상대 URL을 절대 URL로 변환"""
    if relative_url.startswith('http'):
        return relative_url
    
    if relative_url.startswith('/'):
        return f"{base_url}{relative_url}"
    
    return f"{base_url}/CSP/{relative_url}"


def clean_text(text: str) -> str:
    """텍스트 정리 (공백, 개행 등 제거)"""
    if not text:
        return ""
    
    # 연속된 공백을 하나로 변경
    text = re.sub(r'\s+', ' ', text)
    
    # 앞뒤 공백 제거
    return text.strip()


def get_category_name(category_id: str, category_mapping: Dict[str, str]) -> str:
    """
    카테고리 ID로 카테고리 이름 조회
    
    Args:
        category_id: 카테고리 ID
        category_mapping: 카테고리 매핑 딕셔너리
        
    Returns:
        카테고리 이름 (매핑되지 않은 경우 '기타')
    """
    return category_mapping.get(category_id, '기타')


def validate_qa_data(qa_data: Dict) -> bool:
    """Q&A 데이터 유효성 검증"""
    required_fields = ['question_id', 'category_id', 'category_name', 'question', 'answer', 'detail_url', 'full_url']
    
    for field in required_fields:
        if field not in qa_data:
            return False
        
        # question_id와 category_id는 None이어도 허용 (일부 데이터에서 추출 실패 가능)
        if field in ['question_id', 'category_id']:
            continue
            
        # 나머지 필드는 비어있으면 안됨
        if not qa_data[field]:
            return False
    
    return True


def filter_qa_data_by_mode(qa_data_list: List[Dict], simple_result: bool) -> List[Dict]:
    """결과 모드에 따라 Q&A 데이터 필터링
    
    Args:
        qa_data_list: 원본 Q&A 데이터 리스트
        simple_result: True이면 간단한 필드만, False이면 모든 필드
    
    Returns:
        필터링된 Q&A 데이터 리스트
    """
    if not simple_result:
        # detail 모드: 모든 필드 반환
        return qa_data_list
    
    # simple 모드: category_id, category_name, question, answer만 반환
    filtered_data = []
    for item in qa_data_list:
        filtered_item = {
            'category_id': item.get('category_id'),
            'category_name': item.get('category_name'),
            'question': item.get('question'),
            'answer': item.get('answer')
        }
        filtered_data.append(filtered_item)
    
    return filtered_data