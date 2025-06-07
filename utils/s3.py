import boto3
import io
import os
import json
from typing import Union, Optional, BinaryIO, Dict, Any
from botocore.exceptions import ClientError
from config import config
from datetime import datetime


class S3Manager:
    """S3 작업을 위한 매니저 클래스"""
    
    def __init__(self):
        """생성자에서 S3 클라이언트를 초기화합니다."""
        # AWS 프로필 기반으로 세션 생성 (최초 한 번만)
        session = boto3.Session(profile_name=config.AWS_PROFILE)
        self.client = session.client('s3', region_name=config.AWS_REGION)
    
    def download_file(self, bucket: str, key: str, local_path: Optional[str] = None) -> Optional[Union[str, BinaryIO]]:
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
        try:
            # 로컬에 저장하는 경우
            if local_path:
                # 디렉토리가 없으면 생성
                os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
                self.client.download_file(bucket, key, local_path)
                return local_path
            # 메모리에 로드하는 경우
            else:
                file_obj = io.BytesIO()
                self.client.download_fileobj(bucket, key, file_obj)
                file_obj.seek(0)  # 파일 포인터를 처음으로 되돌림
                return file_obj
        except ClientError as e:
            print(f"S3 파일 다운로드 중 오류 발생: {e}")
            return None

    def upload_file(self, file_path_or_obj: Union[str, BinaryIO], bucket: str, key: str) -> bool:
        """
        파일을 S3에 업로드합니다.
        
        Args:
            file_path_or_obj: 로컬 파일 경로 또는 파일 객체
            bucket: S3 버킷 이름
            key: S3 객체 키(저장될 경로)
        
        Returns:
            bool: 업로드 성공 여부
        """
        try:
            # 문자열인 경우 파일 경로로 간주
            if isinstance(file_path_or_obj, str):
                self.client.upload_file(file_path_or_obj, bucket, key)
            # 파일 객체인 경우
            else:
                self.client.upload_fileobj(file_path_or_obj, bucket, key)
            return True
        except ClientError as e:
            print(f"S3 파일 업로드 중 오류 발생: {e}")
            return False

    def list_objects(self, bucket: str, prefix: str = "", max_items: int = 1000) -> list:
        """
        S3 버킷 내 객체 목록을 가져옵니다.
        
        Args:
            bucket: S3 버킷 이름
            prefix: 객체 접두사(디렉토리 경로)
            max_items: 최대 항목 수
        
        Returns:
            list: 객체 정보 목록
        """
        try:
            response = self.client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=max_items)
            if 'Contents' in response:
                return response['Contents']
            return []
        except ClientError as e:
            print(f"S3 객체 목록 조회 중 오류 발생: {e}")
            return []

    def object_exists(self, bucket: str, key: str) -> bool:
        """
        S3에 특정 객체가 존재하는지 확인합니다.
        
        Args:
            bucket: S3 버킷 이름
            key: S3 객체 키
        
        Returns:
            bool: 객체 존재 여부
        """
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            return False

    def get_file_content(self, bucket: str, key: str) -> Optional[str]:
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
        try:
            # 파일 객체를 메모리에 로드
            file_obj = io.BytesIO()
            self.client.download_fileobj(bucket, key, file_obj)
            file_obj.seek(0)  # 파일 포인터를 처음으로 되돌림
            
            # 파일 내용을 문자열로 변환
            content = file_obj.read().decode('utf-8')
            
            # 사용 완료 후 메모리 명시적 해제
            file_obj.close()
            
            return content
        except ClientError as e:
            print(f"S3 파일 로드 중 오류 발생: {e}")
            return None

    def generate_unique_key(self, bucket: str, base_key: str) -> str:
        """
        S3에서 중복되지 않는 고유한 키를 생성합니다.
        파일이 이미 존재하면 파일명에 숫자를 붙여서 고유하게 만듭니다.
        
        예: 0.json -> 0_2.json -> 0_3.json
        
        Args:
            bucket: S3 버킷 이름
            base_key: 기본 S3 키 (경로 포함)
            
        Returns:
            str: 고유한 S3 키
        """
        # 기본 키가 존재하지 않으면 그대로 반환
        if not self.object_exists(bucket, base_key):
            return base_key
        
        # 파일명과 확장자 분리
        if '.' in base_key:
            key_parts = base_key.rsplit('.', 1)
            base_name = key_parts[0]
            extension = '.' + key_parts[1]
        else:
            base_name = base_key
            extension = ''
        
        # 중복이 없는 키를 찾을 때까지 반복
        counter = 2
        while True:
            new_key = f"{base_name}_{counter}{extension}"
            if not self.object_exists(bucket, new_key):
                return new_key
            counter += 1

    def save_json_data(self, data: Dict[str, Any], bucket: str, key: str) -> Dict[str, Any]:
        """
        JSON 데이터를 S3에 저장합니다.
        파일명이 이미 존재하면 자동으로 숫자를 붙여서 고유하게 만듭니다.
        
        Args:
            data: 저장할 데이터
            bucket: S3 버킷 이름
            key: S3 객체 키 (저장될 경로)
            
        Returns:
            저장 결과를 담은 딕셔너리
        """
        if not bucket:
            return {'success': False, 'error': 'S3 bucket not configured'}
        
        try:
            # 중복되지 않는 고유한 키 생성
            unique_key = self.generate_unique_key(bucket, key)
            
            # JSON 데이터를 BytesIO 객체로 변환
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            json_bytes = io.BytesIO(json_data.encode('utf-8'))
            
            # S3에 업로드
            upload_success = self.upload_file(
                file_path_or_obj=json_bytes,
                bucket=bucket,
                key=unique_key
            )
            
            if upload_success:
                return {
                    'success': True,
                    'storage_type': 's3',
                    'bucket': bucket,
                    's3_key': unique_key,
                    'original_key': key,
                    'total_questions': data.get('total_fetched', 0)
                }
            else:
                return {'success': False, 'error': 'S3 upload failed'}
        except Exception as e:
            return {'success': False, 'error': f'JSON serialization or upload failed: {str(e)}'}

    def get_last_crawl_start_time(self, bucket: str, s3_dir_name: str) -> Optional[str]:
        """
        S3에서 마지막 크롤링 시작 시간을 가져옵니다.
        
        Args:
            bucket: S3 버킷 이름
            s3_dir_name: S3 디렉터리 이름 (예: consultation_case, solved_cases/재산범죄)
            
        Returns:
            Optional[str]: ISO format 타임스탬프 또는 None (파일이 없는 경우)
        """
        if not bucket:
            return None
            
        # 빠른 탐색을 위해 특별한 파일명 사용: 00_last_crawl_start_time.txt
        key = f"{s3_dir_name}/00_last_crawl_start_time.txt"
        
        try:
            content = self.get_file_content(bucket, key)
            if content:
                return content.strip()
            return None
        except Exception as e:
            print(f"Error getting last crawl start time: {e}")
            return None

    def save_last_crawl_start_time(self, bucket: str, s3_dir_name: str, timestamp: str) -> bool:
        """
        S3에 크롤링 시작 시간을 저장합니다.
        
        Args:
            bucket: S3 버킷 이름
            s3_dir_name: S3 디렉터리 이름 (예: consultation_case, solved_cases/재산범죄)
            timestamp: ISO format 타임스탬프
            
        Returns:
            bool: 저장 성공 여부
        """
        if not bucket:
            return False
            
        # 빠른 탐색을 위해 특별한 파일명 사용: 00_last_crawl_start_time.txt
        key = f"{s3_dir_name}/00_last_crawl_start_time.txt"
        
        try:
            # 타임스탬프를 BytesIO 객체로 변환
            timestamp_bytes = io.BytesIO(timestamp.encode('utf-8'))
            
            # S3에 업로드
            return self.upload_file(
                file_path_or_obj=timestamp_bytes,
                bucket=bucket,
                key=key
            )
        except Exception as e:
            print(f"Error saving last crawl start time: {e}")
            return False

    def should_stop_crawling(self, item_updated_at: str, last_crawl_start_time: str) -> bool:
        """
        아이템의 업데이트 시간이 마지막 크롤링 시작 시간보다 이전인지 확인합니다.
        
        Args:
            item_updated_at: 아이템의 업데이트 시간 (ISO format, UTC 기준, 'Z'로 끝남)
            last_crawl_start_time: 마지막 크롤링 시작 시간 (ISO format, KST 기준)
            
        Returns:
            bool: 크롤링을 멈춰야 하는지 여부 (True면 멈춤)
        """
        try:
            if not item_updated_at or not last_crawl_start_time:
                return False
                
            # item_updated_at은 UTC 형식 ('Z'로 끝남)
            item_time = datetime.fromisoformat(item_updated_at.replace('Z', '+00:00'))
            
            # last_crawl_start_time은 KST 형식
            if '+' not in last_crawl_start_time and 'Z' not in last_crawl_start_time:
                last_crawl_start_time += '+09:00'
            last_crawl_time = datetime.fromisoformat(last_crawl_start_time.replace('Z', '+09:00'))
            
            # 아이템의 업데이트 시간이 마지막 크롤링 시작 시간보다 이전이면 True
            return item_time < last_crawl_time
        except Exception as e:
            print(f"Error comparing timestamps: {e}")
            return False

    def get_current_timestamp(self) -> str:
        """
        현재 시간을 ISO format으로 반환합니다.
        
        Returns:
            str: 현재 시간의 ISO format 문자열 (KST timezone 포함)
        """
        from datetime import timezone, timedelta
        # KST는 UTC+9
        kst = timezone(timedelta(hours=9))
        return datetime.now(kst).isoformat()
    

def get_s3_manager():
    return S3Manager()