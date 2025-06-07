import requests
from typing import Dict, Any, List
from lawtalk.lawtalk_config import config
from lawtalk.utils import save_data_to_local, save_data_to_s3, generate_filename
from utils.s3 import S3Manager
# 로거 설정
logger = config.get_logger(__name__)

S3_DIR_NAME = "lawtalk/guide_posts"


def collect_and_save_single_guide_page(session_cookie: Any, category_name: str, category_id: str, offset: int, file_number: int,
                                      simple_result: bool = False, storage_type: bool = True, 
                                      only_new: bool = False) -> Dict[str, Any]:
    """
    단일 offset(페이지)의 로톡 가이드 포스트를 수집하여 저장합니다.
    
    Args:
        session_cookie: 인증을 위한 세션 쿠키 객체
        category_name: 카테고리 이름 (한국어)
        category_id: 카테고리 ID
        offset: 수집할 페이지 offset
        file_number: 저장할 파일 번호 (0, 1, 2, ...)
        simple_result: True면 간소화된 데이터, False면 상세 데이터
        storage_type: True면 로컬 저장, False면 S3 저장
        only_new: True면 마지막 크롤링 이후 새로운 데이터만 수집
        
    Returns:
        dict: 수집 및 저장 결과
    """
    logger.info(f"Processing guide posts for category {category_name}, offset {offset}")
    
    try:
        # 단일 offset에 대해 데이터 수집
        response = request_guide_posts(session_cookie, category_id, offset)
        
        if not response.get('success'):
            logger.error(f"Failed to request guide posts data for {category_name} at offset {offset}")
            return {'success': False, 'error': 'Request failed', 'category': category_name, 'offset': offset}
        
        # 데이터 처리
        guide_data = process_guide_posts(response, simple_result, only_new, storage_type, category_name)
        
        if not guide_data.get('success'):
            logger.error(f"Failed to process guide posts data for {category_name} at offset {offset}")
            return {'success': False, 'error': 'Processing failed', 'category': category_name, 'offset': offset}
        
        # early_stop_triggered가 True면 크롤링 중단
        if guide_data.get('early_stop_triggered'):
            logger.info(f"Early stop triggered for {category_name} at offset {offset}")
            return {'success': False, 'error': 'Early stop triggered', 'category': category_name, 'offset': offset, 'early_stop': True}
        
        # 단일 offset에 대한 결과 구성
        posts = guide_data.get('data', {}).get('posts', [])
        
        # 데이터가 없으면 종료
        if not posts:
            logger.info(f"No data available for {category_name} at offset {offset}")
            return {'success': False, 'error': 'No data', 'category': category_name, 'offset': offset, 'early_stop': True}
        
        # 최종 데이터 구성
        final_data = {
            'success': True,
            'total_fetched': len(posts),
            'category': category_name,
            'category_id': category_id,
            'offset': offset,
            'simple_result': simple_result,
            'data': {
                'posts': posts
            }
        }
        
        # 파일명 생성
        filename = generate_filename(file_number)
        
        # 카테고리별 디렉토리로 저장
        s3_dir_name = f"guide_posts/{category_name}"
        
        # 개별 파일로 저장
        if storage_type:
            save_result = save_data_to_local(final_data, s3_dir_name, filename)
        else:
            save_result = save_data_to_s3(final_data, s3_dir_name, filename)
        
        if save_result.get('success'):
            logger.info(f"Successfully saved {len(posts)} guide posts from {category_name} offset {offset}")
            return {
                'success': True,
                'category': category_name,
                'offset': offset,
                'filename': filename,
                'posts_count': len(posts),
                'storage_result': save_result
            }
        else:
            logger.error(f"Failed to save data for {category_name} offset {offset}: {save_result.get('error')}")
            return {'success': False, 'error': f"Save failed: {save_result.get('error')}", 'category': category_name, 'offset': offset}
    
    except Exception as e:
        logger.error(f"Error processing {category_name} offset {offset}: {e}")
        return {'success': False, 'error': str(e), 'category': category_name, 'offset': offset}


def request_guide_posts(session_cookie: Any, category_id: str, offset: int = 0) -> Dict[str, Any]:
    """
    로톡 가이드 포스트 목록을 API를 통해 가져옵니다.

    Args:
        session_cookie: 인증을 위한 세션 쿠키 객체
        category_id: 카테고리 ID
        offset: 데이터를 가져올 시작 위치

    Returns:
        API 응답을 담은 딕셔너리. 실패 시 에러 정보 포함.
    """
    url = config.GUIDE_POSTS_URL
    
    # config에서 기본 파라미터 가져와서 동적으로 설정
    params = config.GUIDE_POSTS_PAYLOAD_KEYS.copy()
    params.update({
        "category": category_id,
        "offset": str(offset)
    })
    
    headers = config.BASE_HEADERS
    
    cookies = {
        session_cookie.name: session_cookie.value
    }
    
    logger.debug(f"Requesting guide posts with category: {category_id}, offset: {offset}")
    
    try:
        response = requests.get(url, headers=headers, params=params, cookies=cookies)
        response.raise_for_status()  # 200번대 응답이 아니면 예외 발생
        
        data = response.json()
        posts_count = len(data.get('posts', []))
        
        logger.debug(f"Successfully fetched {posts_count} guide posts from category {category_id}, offset {offset}")
        logger.debug(f"Response data keys: {list(data.keys())}")
        
        return {
            'success': True,
            'data': data
        }
            
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed for category {category_id}, offset {offset}: {e}")
        return {
            'success': False,
            'error': 'RequestException',
            'message': str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error for category {category_id}, offset {offset}: {e}")
        return {
            'success': False,
            'error': 'Exception',
            'message': str(e)
        }


def process_guide_posts(response_data: Dict[str, Any], simple_result: bool = False, 
                       only_new: bool = False, storage_type: bool = True, 
                       category_name: str = "") -> Dict[str, Any]:
    """
    로톡 가이드 포스트 API 응답 데이터를 simpleResult 인자에 따라 정리합니다.
    
    Args:
        response_data: request_guide_posts에서 받은 API 응답 데이터
        simple_result: True면 간소화된 데이터, False면 상세 데이터 반환
        only_new: True면 마지막 크롤링 이후 새로운 데이터만 처리
        storage_type: S3 사용 여부 판단용
        category_name: 카테고리 이름 (S3 경로 구성용)
        
    Returns:
        정리된 가이드 포스트 데이터를 담은 딕셔너리
    """
    if not response_data.get('success') or not response_data.get('data'):
        logger.warning("Invalid response data provided for processing")
        return response_data
    
    posts = response_data['data'].get('posts', [])
    processed_posts = []
    
    logger.debug(f"Processing {len(posts)} guide posts with simple_result={simple_result}, only_new={only_new}")
    
    # only_new가 True이고 S3를 사용하는 경우 마지막 크롤링 시간 확인
    last_crawl_start_time = None
    if only_new and not storage_type:
        bucket = config.AWS_S3_BUCKET
        s3_dir_name = f"{S3_DIR_NAME}/{category_name}"
        last_crawl_start_time = S3Manager().get_last_crawl_start_time(bucket, s3_dir_name)
        
        if last_crawl_start_time:
            logger.info(f"Only processing data updated after: {last_crawl_start_time}")
        else:
            logger.info("No previous crawl timestamp found, processing all data")
    
    for post in posts:
        # only_new 체크: 포스트의 updatedAt이 마지막 크롤링 시간보다 이전이면 중단
        if only_new and last_crawl_start_time:
            post_updated_at = post.get('updatedAt')
            if post_updated_at and S3Manager().should_stop_crawling(post_updated_at, last_crawl_start_time):
                logger.info(f"Stopping crawling: post updated at {post_updated_at} is before last crawl time {last_crawl_start_time}")
                return {
                    'success': True,
                    'early_stop_triggered': True,
                    'data': {'posts': processed_posts}
                }
        
        if simple_result:
            # 간소화된 데이터
            processed_post = {
                '_id': post.get('_id'),
                'title': post.get('title'),
                'titleOrigin': post.get('titleOrigin'),
                'type': post.get('type'),
                'isPublished': post.get('isPublished'),
                'createdAt': post.get('createdAt'),
                'updatedAt': post.get('updatedAt'),
                'htmlContent': post.get('htmlContent', ''),
                'textContent': post.get('textContent', ''),
                'lawyer': {
                    '_id': post.get('lawyer', {}).get('_id'),
                    'name': post.get('lawyer', {}).get('name'),
                    'role': post.get('lawyer', {}).get('role')
                } if post.get('lawyer') else None,
                'categories': post.get('categories', []),
                'keywords': post.get('keywords', [])
            }
        else:
            # 상세 데이터 (전체 post 객체 사용)
            processed_post = post
        
        processed_posts.append(processed_post)
    
    # 원본 구조 유지하면서 posts만 정리된 데이터로 교체
    result = response_data.copy()
    result['data'] = result['data'].copy()
    result['data']['posts'] = processed_posts
    
    logger.debug(f"Successfully processed {len(processed_posts)} guide posts")
    
    return result


def get_all_categories_guide_posts(session_cookie: Any, start_offset: int = 0, end_offset: int = None,
                                  simple_result: bool = False, storage_type: bool = True, 
                                  only_new: bool = False) -> Dict[str, Any]:
    """
    모든 카테고리의 가이드 포스트를 수집합니다.
    
    Args:
        session_cookie: 인증을 위한 세션 쿠키 객체
        start_offset: 시작 offset (기본값: 0)
        end_offset: 종료 offset (None이면 한 번만 요청)
        simple_result: True면 간소화된 데이터, False면 상세 데이터
        storage_type: True면 로컬 저장, False면 S3 저장
        only_new: True면 마지막 크롤링 이후 새로운 데이터만 수집
        
    Returns:
        모든 카테고리의 수집 결과를 담은 딕셔너리
    """
    total_files = 0
    total_posts = 0
    all_results = {}
    
    logger.info(f"Starting guide posts collection for all categories: offset {start_offset} to {end_offset}, simple_result={simple_result}, only_new={only_new}")
    
    # 크롤링 시작 시간을 미리 기록 (모든 카테고리에 대해 동일한 시작 시간 사용)
    crawl_start_time = S3Manager().get_current_timestamp() if not storage_type else None
    
    for category_name, category_id in config.CATEGORY_IDS.items():
        logger.info(f"Processing category: {category_name} ({category_id})")
        
        # 각 카테고리별로 페이지네이션 수행
        category_results = collect_category_guide_posts_with_pagination(
            session_cookie=session_cookie,
            category_name=category_name,
            category_id=category_id,
            start_offset=start_offset,
            end_offset=end_offset,
            simple_result=simple_result,
            storage_type=storage_type,
            only_new=only_new
        )
        
        all_results[category_name] = category_results
        total_files += category_results.get('total_files', 0)
        total_posts += category_results.get('total_posts', 0)
        
        # S3를 사용하고 크롤링이 성공적으로 완료된 경우에만 크롤링 시간 업데이트
        if not storage_type and category_results.get('success') and crawl_start_time:
            bucket = config.AWS_S3_BUCKET
            s3_dir_name = f"{S3_DIR_NAME}/{category_name}"
            S3Manager().save_last_crawl_start_time(bucket, s3_dir_name, crawl_start_time)
            logger.info(f"Updated last crawl time for {category_name}: {crawl_start_time}")
        
        logger.info(f"Completed category {category_name}: {category_results.get('total_posts', 0)} posts in {category_results.get('total_files', 0)} files")
    
    # 최종 결과 구성
    final_result = {
        'success': True,
        'total_categories': len(config.CATEGORY_IDS),
        'total_files': total_files,
        'total_posts': total_posts,
        'offset_range': f"{start_offset} to {end_offset}",
        'storage_type': 'local' if storage_type else 's3',
        'only_new': only_new,
        'category_results': all_results
    }
    
    logger.info(f"Guide posts collection completed: {total_posts} total posts in {total_files} files across {len(config.CATEGORY_IDS)} categories")
    
    return final_result


def collect_category_guide_posts_with_pagination(session_cookie: Any, category_name: str, category_id: str,
                                                 start_offset: int = 0, end_offset: int = None,
                                                 simple_result: bool = False, storage_type: bool = True, 
                                                 only_new: bool = False) -> Dict[str, Any]:
    """
    특정 카테고리의 가이드 포스트를 페이지별로 수집하고 저장합니다.
    
    Args:
        session_cookie: 인증을 위한 세션 쿠키 객체
        category_name: 카테고리 이름 (한국어)
        category_id: 카테고리 ID
        start_offset: 시작 offset (기본값: 0)
        end_offset: 종료 offset (None이면 한 번만 요청)
        simple_result: True면 간소화된 데이터, False면 상세 데이터
        storage_type: True면 로컬 저장, False면 S3 저장
        only_new: True면 마지막 크롤링 이후 새로운 데이터만 수집
        
    Returns:
        해당 카테고리의 수집 결과를 담은 딕셔너리
    """
    current_offset = start_offset
    file_number = 0  # 순차적인 파일 번호 (0, 1, 2, ...)
    total_files = 0
    total_posts = 0
    results = []
    
    # end_offset가 None이면 한 번만 요청
    if end_offset is None:
        end_offset = start_offset + 9  # 가이드 포스트는 기본 limit이 9
    
    logger.info(f"Starting {category_name} guide posts collection: offset {start_offset} to {end_offset}")
    
    while current_offset < end_offset:
        result = collect_and_save_single_guide_page(
            session_cookie=session_cookie,
            category_name=category_name,
            category_id=category_id,
            offset=current_offset,
            file_number=file_number,
            simple_result=simple_result,
            storage_type=storage_type,
            only_new=only_new
        )
        
        if result.get('success'):
            total_files += 1
            total_posts += result.get('posts_count', 0)
            results.append(result)
            logger.info(f"Successfully processed {category_name} offset {current_offset}")
        else:
            # early_stop이 True면 더 이상 진행하지 않음
            if result.get('early_stop'):
                logger.info(f"Early stop triggered for {category_name} at offset {current_offset}, stopping collection")
                break
            # 다른 에러의 경우 로그만 남기고 계속 진행
            logger.warning(f"Failed to process {category_name} offset {current_offset}: {result.get('error')}")
        
        # 다음 offset과 파일 번호로 이동 (가이드 포스트는 limit이 9)
        current_offset += 9
        file_number += 1
        
        # end_offset를 초과하지 않도록 조정
        if current_offset >= end_offset:
            break
    
    # 최종 결과 구성
    category_result = {
        'success': True,
        'category': category_name,
        'category_id': category_id,
        'total_files': total_files,
        'total_posts': total_posts,
        'offset_range': f"{start_offset} to {min(current_offset, end_offset)}",
        'only_new': only_new,
        'results': results
    }
    
    logger.info(f"{category_name} guide posts collection completed: {total_posts} total posts in {total_files} files")
    
    return category_result
