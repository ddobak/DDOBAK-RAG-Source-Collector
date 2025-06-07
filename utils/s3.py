import boto3
import io
import os
from typing import Union, Optional, BinaryIO
from botocore.exceptions import ClientError
from lawtalk.lawtalk_config import config


def get_s3_client():
    """
    boto3 s3 클라이언트를 생성하여 반환합니다.
    config에 설정된 프로필과 리전을 사용합니다.
    """
    # AWS 프로필 기반으로 세션 생성
    session = boto3.Session(profile_name=config.AWS_PROFILE)
    s3_client = session.client('s3', region_name=config.AWS_REGION)
    
    return s3_client


def download_file_from_s3(bucket: str, key: str, local_path: Optional[str] = None) -> Optional[Union[str, BinaryIO]]:
    """
    S3에서 파일을 다운로드합니다.
    
    Args:
        bucket: S3 버킷 이름
        key: S3 객체 키(파일 경로)
        local_path: 로컬에 저장할 경로 (None인 경우 메모리에 로드)
    
    Returns:
        local_path가 제공된 경우: 저장된 로컬 파일 경로
        local_path가 None인 경우: 파일 내용을 담은 BytesIO 객체
    
    Raises:
        ClientError: S3 접근 중 오류가 발생한 경우
    """
    s3_client = get_s3_client()
    
    try:
        # 로컬에 저장하는 경우
        if local_path:
            # 디렉토리가 없으면 생성
            os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
            s3_client.download_file(bucket, key, local_path)
            return local_path
        # 메모리에 로드하는 경우
        else:
            file_obj = io.BytesIO()
            s3_client.download_fileobj(bucket, key, file_obj)
            file_obj.seek(0)  # 파일 포인터를 처음으로 되돌림
            return file_obj
    except ClientError as e:
        print(f"S3 파일 다운로드 중 오류 발생: {e}")
        return None


def upload_file_to_s3(file_path_or_obj: Union[str, BinaryIO], bucket: str, key: str) -> bool:
    """
    파일을 S3에 업로드합니다.
    
    Args:
        file_path_or_obj: 로컬 파일 경로 또는 파일 객체
        bucket: S3 버킷 이름
        key: S3 객체 키(저장될 경로)
    
    Returns:
        bool: 업로드 성공 여부
    """
    s3_client = get_s3_client()
    
    try:
        # 문자열인 경우 파일 경로로 간주
        if isinstance(file_path_or_obj, str):
            s3_client.upload_file(file_path_or_obj, bucket, key)
        # 파일 객체인 경우
        else:
            s3_client.upload_fileobj(file_path_or_obj, bucket, key)
        return True
    except ClientError as e:
        print(f"S3 파일 업로드 중 오류 발생: {e}")
        return False


def list_objects_in_bucket(bucket: str, prefix: str = "", max_items: int = 1000) -> list:
    """
    S3 버킷 내 객체 목록을 가져옵니다.
    
    Args:
        bucket: S3 버킷 이름
        prefix: 객체 접두사(디렉토리 경로)
        max_items: 최대 항목 수
    
    Returns:
        list: 객체 정보 목록
    """
    s3_client = get_s3_client()
    
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=max_items)
        if 'Contents' in response:
            return response['Contents']
        return []
    except ClientError as e:
        print(f"S3 객체 목록 조회 중 오류 발생: {e}")
        return []


def check_if_object_exists(bucket: str, key: str) -> bool:
    """
    S3에 특정 객체가 존재하는지 확인합니다.
    
    Args:
        bucket: S3 버킷 이름
        key: S3 객체 키
    
    Returns:
        bool: 객체 존재 여부
    """
    s3_client = get_s3_client()
    
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        return False


def get_file_content_from_s3(bucket: str, key: str) -> Optional[str]:
    """
    S3에서 파일 내용을 로드합니다.
    
    Args:
        bucket: S3 버킷 이름
        key: S3 객체 키(파일 경로)
    
    Returns:
        Optional[str]: 파일 내용 문자열 또는 파일이 존재하지 않는 경우 None
    
    Raises:
        ClientError: S3 접근 중 오류가 발생한 경우
    """
    s3_client = get_s3_client()
    
    try:
        # 파일 객체를 메모리에 로드
        file_obj = io.BytesIO()
        s3_client.download_fileobj(bucket, key, file_obj)
        file_obj.seek(0)  # 파일 포인터를 처음으로 되돌림
        
        # 파일 내용을 문자열로 변환
        content = file_obj.read().decode('utf-8')
        
        # 사용 완료 후 메모리 명시적 해제
        file_obj.close()
        
        return content
    except ClientError as e:
        print(f"S3 파일 로드 중 오류 발생: {e}")
        return None
