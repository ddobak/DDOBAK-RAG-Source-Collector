import requests
from typing import Dict, Any, List
from lawtalk.lawtalk_config import config
from lawtalk.utils import save_data_to_local, save_data_to_s3, generate_filename
from utils.s3 import S3Manager

# 로거 설정
logger = config.get_logger(__name__)

S3_DIR_NAME = "lawtalk/consultation_case"

def collect_and_save_single_qna_page(session_cookie: Any, offset: int, file_number: int,
                                    simple_result: bool = False, storage_type: bool = True, 
                                    only_new: bool = False) -> Dict[str, Any]:
    """
    단일 offset(페이지)의 로톡 Q&A 상담사례를 수집하여 저장합니다.
    
    Args:
        session_cookie: 인증을 위한 세션 쿠키 객체
        offset: 수집할 페이지 offset
        file_number: 저장할 파일 번호 (0, 1, 2, ...)
        simple_result: True면 간소화된 데이터, False면 상세 데이터
        storage_type: True면 로컬 저장, False면 S3 저장
        only_new: True면 마지막 크롤링 이후 새로운 데이터만 수집
        
    Returns:
        dict: 수집 및 저장 결과
    """
    logger.info(f"Processing offset {offset}")
    
    try:
        # 단일 offset에 대해 데이터 수집
        response = request_qna_cases(session_cookie, offset)
        
        if not response.get('success'):
            logger.error(f"Failed to request Q&A data at offset {offset}")
            return {'success': False, 'error': 'Request failed', 'offset': offset}
        
        # 데이터 처리
        qna_data = process_qna_cases(response, simple_result, only_new, storage_type)
        
        if not qna_data.get('success'):
            logger.error(f"Failed to process Q&A data at offset {offset}")
            return {'success': False, 'error': 'Processing failed', 'offset': offset}
        
        # early_stop_triggered가 True면 크롤링 중단
        if qna_data.get('early_stop_triggered'):
            logger.info(f"Early stop triggered at offset {offset}")
            return {'success': False, 'error': 'Early stop triggered', 'offset': offset, 'early_stop': True}
        
        # 단일 offset에 대한 결과 구성
        questions = qna_data.get('data', {}).get('questions', [])
        
        # 데이터가 없으면 종료
        if not questions:
            logger.info(f"No data available at offset {offset}")
            return {'success': False, 'error': 'No data', 'offset': offset}
        
        # 최종 데이터 구성
        final_data = {
            'success': True,
            'total_fetched': len(questions),
            'offset': offset,  # 단일 offset만 명시
            'simple_result': simple_result,
            'data': {
                'questions': questions
            }
        }
        
        # 파일명 생성
        filename = generate_filename(file_number)
        
        # 개별 파일로 저장
        if storage_type:
            save_result = save_data_to_local(final_data, "consultation_case", filename)
        else:
            save_result = save_data_to_s3(final_data, "consultation_case", filename)
        
        if save_result.get('success'):
            logger.info(f"Successfully saved {len(questions)} questions from offset {offset}")
            return {
                'success': True,
                'offset': offset,
                'filename': filename,
                'questions_count': len(questions),
                'storage_result': save_result
            }
        else:
            logger.error(f"Failed to save data for offset {offset}: {save_result.get('error')}")
            return {'success': False, 'error': f"Save failed: {save_result.get('error')}", 'offset': offset}
    
    except Exception as e:
        logger.error(f"Error processing offset {offset}: {e}")
        return {'success': False, 'error': str(e), 'offset': offset}


def request_qna_cases(session_cookie: Any, offset: int = 0) -> Dict[str, Any]:
    """
    로톡 Q&A 상담사례 목록을 API를 통해 가져옵니다.

    Args:
        session_cookie: 인증을 위한 세션 쿠키 객체
        offset: 데이터를 가져올 시작 위치

    Returns:
        API 응답을 담은 딕셔너리. 실패 시 에러 정보 포함.
    """
    url = config.CONSULTATION_URL
    
    # config에서 기본 파라미터 가져와서 동적으로 설정
    params = config.CONSULTATION_PAYLOAD_KEYS.copy()
    params.update({
        "offset": str(offset)
    })
    
    headers = config.BASE_HEADERS
    
    cookies = {
        session_cookie.name: session_cookie.value
    }
    
    logger.debug(f"Requesting Q&A cases with offset: {offset}")
    
    try:
        response = requests.get(url, headers=headers, params=params, cookies=cookies)
        response.raise_for_status()  # 200번대 응답이 아니면 예외 발생
        
        data = response.json()
        questions_count = len(data.get('questions', []))
        
        logger.debug(f"Successfully fetched {questions_count} Q&A cases from offset {offset}")
        logger.debug(f"Response data keys: {list(data.keys())}")
        
        return {
            'success': True,
            'data': data
        }
            
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed at offset {offset}: {e}")
        return {
            'success': False,
            'error': 'RequestException',
            'message': str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error at offset {offset}: {e}")
        return {
            'success': False,
            'error': 'Exception',
            'message': str(e)
        }


def process_qna_cases(response_data: Dict[str, Any], simple_result: bool = False, 
                     only_new: bool = False, storage_type: bool = True) -> Dict[str, Any]:
    """
    로톡 Q&A API 응답 데이터를 simpleResult 인자에 따라 정리합니다.
    
    Args:
        response_data: request_qna_cases에서 받은 API 응답 데이터
        simple_result: True면 간소화된 데이터, False면 상세 데이터 반환
        only_new: True면 마지막 크롤링 이후 새로운 데이터만 처리
        storage_type: S3 사용 여부 판단용
        
    Returns:
        정리된 Q&A 데이터를 담은 딕셔너리
    """
    if not response_data.get('success') or not response_data.get('data'):
        logger.warning("Invalid response data provided for processing")
        return response_data
    
    questions = response_data['data'].get('questions', [])
    processed_questions = []
    
    logger.debug(f"Processing {len(questions)} questions with simple_result={simple_result}, only_new={only_new}")
    
    # only_new가 True이고 S3를 사용하는 경우 마지막 크롤링 시간 확인
    last_crawl_start_time = None
    if only_new and not storage_type:
        bucket = config.AWS_S3_BUCKET
        s3_dir_name = S3_DIR_NAME
        last_crawl_start_time = S3Manager().get_last_crawl_start_time(bucket, s3_dir_name)
        
        if last_crawl_start_time:
            logger.info(f"Only processing data updated after: {last_crawl_start_time}")
        else:
            logger.info("No previous crawl timestamp found, processing all data")
    
    for question in questions:
        # only_new 체크: 질문의 updatedAt이 마지막 크롤링 시간보다 이전이면 중단
        if only_new and last_crawl_start_time:
            question_updated_at = question.get('updatedAt')
            if question_updated_at and S3Manager().should_stop_crawling(question_updated_at, last_crawl_start_time):
                logger.info(f"Stopping crawling: question updated at {question_updated_at} is before last crawl time {last_crawl_start_time}")
                return {
                    'success': True,
                    'early_stop_triggered': True,
                    'data': {'questions': processed_questions}
                }
        
        if simple_result:
            # 간소화된 데이터
            processed_question = {
                '_id': question.get('_id'),
                'user': question.get('user'),
                'categories': question.get('categories', []),
                'titleOrigin': question.get('titleOrigin'),
                'bodyOrigin': question.get('bodyOrigin'),
                'title': question.get('title'),
                'body': question.get('body'),
                'slugs': question.get('slugs'),
                'meta': question.get('meta'),
                'createdAt': question.get('createdAt'),
                'updatedAt': question.get('updatedAt'),
                'answers': []
            }
            
            # 답변 데이터 간소화
            for answer in question.get('answers', []):
                lawyer_info = answer.get('lawyer', {})
                body_list = answer.get('body', [])
                
                # body 배열에서 content 추출
                simplified_body = []
                for body_item in body_list:
                    content = body_item.get('content', {})
                    simplified_body.append({
                        '_id': content.get('_id'),
                        'answer': content.get('answer'),
                        'body': content.get('body'),
                        'createdAt': content.get('createdAt'),
                        'updatedAt': content.get('updatedAt'),
                        'number': content.get('number')
                    })
                
                simplified_answer = {
                    '_id': answer.get('_id'),
                    'lawyer': lawyer_info.get('_id'),
                    'role': lawyer_info.get('role'),
                    'body': simplified_body
                }
                processed_question['answers'].append(simplified_answer)
                
        else:
            # 상세 데이터
            processed_question = {
                '_id': question.get('_id'),
                'user': question.get('user'),
                'categories': question.get('categories', []),
                'titleOrigin': question.get('titleOrigin'),
                'bodyOrigin': question.get('bodyOrigin'),
                'title': question.get('title'),
                'body': question.get('body'),
                'slugs': question.get('slugs'),
                'meta': question.get('meta'),
                'createdAt': question.get('createdAt'),
                'updatedAt': question.get('updatedAt'),
                'focusAdCategories': question.get('focusAdCategories'),
                'modelType': question.get('modelType'),
                'aiResponse': question.get('aiResponse', {}),
                'answers': []
            }
            
            # 답변 데이터 상세 정보 포함
            for answer in question.get('answers', []):
                lawyer_info = answer.get('lawyer', {})
                body_list = answer.get('body', [])
                
                # body 배열에서 모든 버전의 content 추출
                detailed_body = []
                for body_item in body_list:
                    content = body_item.get('content', {})
                    detailed_body.append({
                        '_id': content.get('_id'),
                        'answer': content.get('answer'),
                        'body': content.get('body'),
                        'createdAt': content.get('createdAt'),
                        'updatedAt': content.get('updatedAt'),
                        'number': content.get('number')
                    })
                
                detailed_answer = {
                    '_id': answer.get('_id'),
                    'lawyer': lawyer_info,
                    'slug': answer.get('slug'),
                    'body': {
                        'content': detailed_body
                    }
                }
                processed_question['answers'].append(detailed_answer)
        
        processed_questions.append(processed_question)
    
    # 원본 구조 유지하면서 questions만 정리된 데이터로 교체
    result = response_data.copy()
    result['data'] = result['data'].copy()
    result['data']['questions'] = processed_questions
    
    logger.debug(f"Successfully processed {len(processed_questions)} questions")
    
    return result


def collect_qna_cases_with_pagination(session_cookie: Any, start_offset: int = 0, end_offset: int = None,
                                     simple_result: bool = False, storage_type: bool = True, 
                                     only_new: bool = False) -> Dict[str, Any]:
    """
    지정된 offset 범위의 로톡 Q&A 상담사례를 페이지별로 수집하고 저장합니다.
    
    Args:
        session_cookie: 인증을 위한 세션 쿠키 객체
        start_offset: 시작 offset (기본값: 0)
        end_offset: 종료 offset (None이면 한 번만 요청)
        simple_result: True면 간소화된 데이터, False면 상세 데이터
        storage_type: True면 로컬 저장, False면 S3 저장
        only_new: True면 마지막 크롤링 이후 새로운 데이터만 수집
        
    Returns:
        모든 페이지의 수집 결과를 담은 딕셔너리
    """
    current_offset = start_offset
    file_number = 0  # 순차적인 파일 번호 (0, 1, 2, ...)
    total_files = 0
    total_questions = 0
    results = []
    
    # end_offset가 None이면 한 번만 요청
    if end_offset is None:
        end_offset = start_offset + 10
    
    logger.info(f"Starting Q&A collection: offset {start_offset} to {end_offset}, simple_result={simple_result}, only_new={only_new}")
    
    # only_new가 True이고 S3를 사용하는 경우 크롤링 시작 시간 저장
    if only_new and not storage_type:
        bucket = config.AWS_S3_BUCKET
        s3_dir_name = S3_DIR_NAME
        crawl_start_time = S3Manager().get_current_timestamp()
        S3Manager().save_last_crawl_start_time(bucket, s3_dir_name, crawl_start_time)
        logger.info(f"Saved crawl start time: {crawl_start_time}")
    
    while current_offset < end_offset:
        result = collect_and_save_single_qna_page(
            session_cookie=session_cookie,
            offset=current_offset,
            file_number=file_number,
            simple_result=simple_result,
            storage_type=storage_type,
            only_new=only_new
        )
        
        if result.get('success'):
            total_files += 1
            total_questions += result.get('questions_count', 0)
            results.append(result)
            logger.info(f"Successfully processed offset {current_offset}")
        else:
            # early_stop이 True면 더 이상 진행하지 않음
            if result.get('early_stop'):
                logger.info(f"Early stop triggered at offset {current_offset}, stopping collection")
                break
            # 다른 에러의 경우 로그만 남기고 계속 진행
            logger.warning(f"Failed to process offset {current_offset}: {result.get('error')}")
        
        # 다음 offset과 파일 번호로 이동
        current_offset += 10
        file_number += 1
        
        # end_offset를 초과하지 않도록 조정
        if current_offset >= end_offset:
            break
    
    # 최종 결과 구성
    final_result = {
        'success': True,
        'total_files': total_files,
        'total_questions': total_questions,
        'offset_range': f"{start_offset} to {min(current_offset, end_offset)}",
        'storage_type': 'local' if storage_type else 's3',
        'only_new': only_new,
        'results': results
    }
    
    logger.info(f"Q&A collection completed: {total_questions} total questions in {total_files} files")
    
    return final_result


