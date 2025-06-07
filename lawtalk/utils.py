"""
로톡 크롤러 공통 유틸리티 함수들
"""
import json
import io
from pathlib import Path
from typing import Dict, Any
from lawtalk.lawtalk_config import config
from utils.s3 import upload_file_to_s3


def save_qna_data_to_local(qna_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
    """
    Q&A 데이터를 로컬에 저장합니다.
    
    Args:
        qna_data: 저장할 Q&A 데이터
        filename: 저장할 파일명
        
    Returns:
        저장 결과를 담은 딕셔너리
    """
    local_dir = config.DATA_DIR / "lawtalk"
    local_dir.mkdir(exist_ok=True)
    local_path = local_dir / filename
    
    json_data = json.dumps(qna_data, ensure_ascii=False, indent=2)
    
    with open(local_path, 'w', encoding='utf-8') as f:
        f.write(json_data)
    
    return {
        'success': True,
        'storage_type': 'local',
        'file_path': str(local_path),
        'total_questions': qna_data.get('total_fetched', 0)
    }


def save_qna_data_to_s3(qna_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
    """
    Q&A 데이터를 S3에 저장합니다.
    
    Args:
        qna_data: 저장할 Q&A 데이터
        filename: 저장할 파일명
        
    Returns:
        저장 결과를 담은 딕셔너리
    """
    if not config.AWS_S3_BUCKET:
        return {'success': False, 'error': 'S3 bucket not configured'}
    
    # S3 키 생성 (lawtalk/{filename})
    s3_key = f"lawtalk/{filename}"
    
    # JSON 데이터를 BytesIO 객체로 변환
    json_data = json.dumps(qna_data, ensure_ascii=False, indent=2)
    json_bytes = io.BytesIO(json_data.encode('utf-8'))
    
    # S3에 업로드
    upload_success = upload_file_to_s3(
        file_path_or_obj=json_bytes,
        bucket=config.AWS_S3_BUCKET,
        key=s3_key
    )
    
    if upload_success:
        return {
            'success': True,
            'storage_type': 's3',
            'bucket': config.AWS_S3_BUCKET,
            's3_key': s3_key,
            'total_questions': qna_data.get('total_fetched', 0)
        }
    else:
        return {'success': False, 'error': 'S3 upload failed'}


def generate_filename(offset: int) -> str:
    """
    offset을 기반으로 파일명을 생성합니다.
    
    Args:
        offset: 데이터 offset
        
    Returns:
        생성된 파일명 (MMDD_{offset}.json)
    """
    return f"{config.DATETIME[:4]}_{offset}.json" 