"""
로톡 크롤러 공통 유틸리티 함수들
"""
from typing import Dict, Any
from lawtalk.lawtalk_config import config
from utils.s3 import get_s3_manager
from utils.utils import save_json_data_to_local



def save_data_to_local(data: Dict[str, Any], path: str, filename: str) -> Dict[str, Any]:
    """
    데이터를 로컬에 저장합니다.
    
    Args:
        data: 저장할 데이터
        filename: 저장할 파일명 (경로 포함)
        
    Returns:
        저장 결과를 담은 딕셔너리
    """
    base_dir = str(config.DATA_DIR / "lawtalk" / path)
    return save_json_data_to_local(data, base_dir, filename)


def save_data_to_s3(data: Dict[str, Any], path: str, filename: str) -> Dict[str, Any]:
    """
    데이터를 S3에 저장합니다.
    
    Args:
        data: 저장할 데이터
        filename: 저장할 파일명 (경로 포함)
        
    Returns:
        저장 결과를 담은 딕셔너리
    """
    if not config.AWS_S3_BUCKET:
        return {'success': False, 'error': 'S3 bucket not configured'}
    
    # S3 키 생성 (lawtalk/{path}/{filename})
    s3_key = f"lawtalk/{path}/{filename}"
    
    # S3Manager 인스턴스를 사용하여 저장
    s3_manager = get_s3_manager()
    return s3_manager.save_json_data(data, config.AWS_S3_BUCKET, s3_key)


def generate_filename(file_number: int) -> str:
    """
    전달받은 번호로 날짜 별로 계층화 된 파일명을 생성합니다.
    
    Args:
        file_number: 파일 번호
        
    Returns:
        생성된 파일명 ({file_number}.json)
    """
    return f"{config.DATETIME[:4]}/{file_number}.json" 