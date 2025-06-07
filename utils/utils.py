import json
from pathlib import Path
from typing import Dict, Any


def generate_unique_local_path(base_dir: str, file_path: str) -> Path:
    """
    로컬에서 중복되지 않는 고유한 파일 경로를 생성합니다.
    파일이 이미 존재하면 파일명에 숫자를 붙여서 고유하게 만듭니다.
    
    예: 0.json -> 0_2.json -> 0_3.json
    
    Args:
        base_dir: 기본 디렉토리 경로
        file_path: 파일 경로 (base_dir 기준 상대 경로)
        
    Returns:
        Path: 고유한 파일 경로
    """
    # 기본 경로 구성
    full_path = Path(base_dir) / file_path
    
    # 파일이 존재하지 않으면 그대로 반환
    if not full_path.exists():
        return full_path
    
    # 파일명과 확장자 분리
    if full_path.suffix:
        base_name = full_path.stem
        extension = full_path.suffix
        parent_dir = full_path.parent
    else:
        base_name = full_path.name
        extension = ''
        parent_dir = full_path.parent
    
    # 중복이 없는 경로를 찾을 때까지 반복
    counter = 2
    while True:
        new_name = f"{base_name}_{counter}{extension}"
        new_path = parent_dir / new_name
        if not new_path.exists():
            return new_path
        counter += 1


def save_json_data_to_local(data: Dict[str, Any], base_dir: str, file_path: str) -> Dict[str, Any]:
    """
    JSON 데이터를 로컬에 저장합니다.
    파일명이 이미 존재하면 자동으로 숫자를 붙여서 고유하게 만듭니다.
    
    Args:
        data: 저장할 데이터
        base_dir: 기본 디렉토리 경로
        file_path: 저장할 파일 경로 (base_dir 기준 상대 경로)
        
    Returns:
        저장 결과를 담은 딕셔너리
    """
    try:
        # 중복되지 않는 고유한 경로 생성
        unique_path = generate_unique_local_path(base_dir, file_path)
        
        # 디렉토리 생성 (상위 경로 포함)
        unique_path.parent.mkdir(parents=True, exist_ok=True)
        
        # JSON 데이터 저장
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        
        with open(unique_path, 'w', encoding='utf-8') as f:
            f.write(json_data)
        
        return {
            'success': True,
            'storage_type': 'local',
            'file_path': str(unique_path),
            'original_path': str(Path(base_dir) / file_path),
            'total_questions': data.get('total_fetched', 0)
        }
    except Exception as e:
        return {'success': False, 'error': f'Local file save failed: {str(e)}'}