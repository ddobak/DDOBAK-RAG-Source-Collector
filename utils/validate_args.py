"""
CLI 인자 검증 유틸리티
명령행 인자들의 유효성을 검사하는 함수들을 제공합니다.
"""
import sys
from typing import Dict, List, Any


# 유효한 값들 정의
VALID_VALUES = {
    'simple_result': ['simple', 'detail'],
    'storage_type': ['local', 's3'],
    'only_new': ['new', 'all']
}

# 인자 설명
ARG_DESCRIPTIONS = {
    'simple_result': {
        'simple': '간소화된 결과만 수집',
        'detail': '상세한 결과까지 모두 수집'
    },
    'storage_type': {
        'local': '로컬 파일 시스템에 저장',
        's3': 'AWS S3에 저장'
    },
    'only_new': {
        'new': '마지막 크롤링 이후 새로운 데이터만 수집',
        'all': '모든 데이터 수집'
    }
}


def validate_argument(arg_name: str, arg_value: str) -> bool:
    """
    단일 인자의 유효성을 검사합니다.
    
    Args:
        arg_name: 인자 이름
        arg_value: 인자 값
        
    Returns:
        bool: 유효하면 True, 그렇지 않으면 False
    """
    if arg_name not in VALID_VALUES:
        return False
    
    return arg_value in VALID_VALUES[arg_name]


def validate_all_arguments(simple_result: str, storage_type: str, only_new: str) -> Dict[str, Any]:
    """
    모든 CLI 인자의 유효성을 검사합니다.
    
    Args:
        simple_result: 결과 타입 (simple/detail)
        storage_type: 저장 위치 (local/s3)
        only_new: 데이터 범위 (new/all)
        
    Returns:
        dict: 검증 결과와 에러 메시지
    """
    errors = []
    
    # 각 인자 검증
    if not validate_argument('simple_result', simple_result):
        valid_options = ', '.join(VALID_VALUES['simple_result'])
        errors.append(f"잘못된 simple_result 값: '{simple_result}'. 사용 가능한 값: {valid_options}")
    
    if not validate_argument('storage_type', storage_type):
        valid_options = ', '.join(VALID_VALUES['storage_type'])
        errors.append(f"잘못된 storage_type 값: '{storage_type}'. 사용 가능한 값: {valid_options}")
    
    if not validate_argument('only_new', only_new):
        valid_options = ', '.join(VALID_VALUES['only_new'])
        errors.append(f"잘못된 only_new 값: '{only_new}'. 사용 가능한 값: {valid_options}")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def convert_args_to_options(simple_result: str, storage_type: str, only_new: str) -> Dict[str, bool]:
    """
    CLI 인자를 크롤러 옵션 딕셔너리로 변환합니다.
    
    Args:
        simple_result: 결과 타입 (simple/detail)
        storage_type: 저장 위치 (local/s3)
        only_new: 데이터 범위 (new/all)
        
    Returns:
        dict: 크롤러 옵션 딕셔너리
    """
    return {
        'simple_result': simple_result == "simple",
        'storage_type': storage_type == "local",
        'only_new': only_new == "new"
    }


def print_usage_help():
    """사용법 도움말을 출력합니다."""
    print("\n사용법:")
    print("poetry run start <site> [simple_result] [storage_type] [only_new]")
    print("\n인자 설명:")
    
    for arg_name, descriptions in ARG_DESCRIPTIONS.items():
        print(f"\n{arg_name}:")
        for value, desc in descriptions.items():
            print(f"  {value}: {desc}")
    
    print("\n예시:")
    print("poetry run start lawtalk simple s3 all")
    print("poetry run start lawtalk detail local new")


def validate_and_convert_args(simple_result: str, storage_type: str, only_new: str) -> Dict[str, Any]:
    """
    인자 검증과 변환을 한번에 수행합니다.
    
    Args:
        simple_result: 결과 타입 (simple/detail)
        storage_type: 저장 위치 (local/s3)
        only_new: 데이터 범위 (new/all)
        
    Returns:
        dict: 검증 결과와 변환된 옵션
    """
    # 검증 수행
    validation_result = validate_all_arguments(simple_result, storage_type, only_new)
    
    if not validation_result['valid']:
        return {
            'valid': False,
            'errors': validation_result['errors'],
            'options': None
        }
    
    # 변환 수행
    options = convert_args_to_options(simple_result, storage_type, only_new)
    
    return {
        'valid': True,
        'errors': [],
        'options': options
    }


def exit_with_errors(errors: List[str]):
    """
    에러 메시지를 출력하고 프로그램을 종료합니다.
    
    Args:
        errors: 에러 메시지 리스트
    """
    print("❌ 인자 검증 실패:")
    for error in errors:
        print(f"  - {error}")
    
    print_usage_help()
    sys.exit(1) 