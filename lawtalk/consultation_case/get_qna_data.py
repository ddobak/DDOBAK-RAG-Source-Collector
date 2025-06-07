import requests
from typing import Dict, Any, List
from lawtalk.lawtalk_config import config
from lawtalk.utils import save_qna_data_to_local, save_qna_data_to_s3, generate_filename

# 로거 설정
logger = config.get_logger(__name__)


def collect_and_save_qna_cases(session_cookie: Any, start_offset: int = 0, end_offset: int = None,
                              simple_result: bool = False, save_local: bool = True) -> Dict[str, Any]:
    """
    지정된 offset 범위의 로톡 Q&A 상담사례를 offset별로 개별 수집하여 각각 저장합니다.
    
    Args:
        session_cookie: 인증을 위한 세션 쿠키 객체
        start_offset: 시작 offset (기본값: 0)
        end_offset: 종료 offset (None이면 한 번만 요청)
        simple_result: True면 간소화된 데이터, False면 상세 데이터
        save_local: True면 로컬 저장, False면 S3 저장
        
    Returns:
        dict: 전체 수집 및 저장 결과
    """
    # end_offset가 None이면 한 번만 요청
    if end_offset is None:
        end_offset = start_offset + 1  # 한 번만 요청
    
    results = []
    total_questions = 0
    
    logger.info(f"Starting Q&A collection and save: offset {start_offset} to {end_offset}, save_local={save_local}")
    
    # 각 offset(페이지)별로 개별 처리
    for current_offset in range(start_offset, end_offset):
        try:
            logger.info(f"Processing offset {current_offset}")
            
            # 개별 offset에 대해 데이터 수집 (한 번만 요청)
            qna_data = get_qna_cases(
                session_cookie=session_cookie,
                start_offset=current_offset,
                end_offset=None,  # None으로 설정하여 한 번만 요청
                simple_result=simple_result
            )
            
            if not qna_data.get('success'):
                logger.error(f"Failed to collect Q&A data at offset {current_offset}")
                continue
            
            # 데이터가 없으면 종료
            questions = qna_data.get('data', {}).get('questions', [])
            if not questions:
                logger.info(f"No more data available at offset {current_offset}")
                break
            
            # 파일명 생성
            filename = generate_filename(current_offset)
            
            # 개별 파일로 저장
            if save_local:
                save_result = save_qna_data_to_local(qna_data, filename)
            else:
                save_result = save_qna_data_to_s3(qna_data, filename)
            
            if save_result.get('success'):
                results.append({
                    'offset': current_offset,
                    'filename': filename,
                    'questions_count': len(questions),
                    'storage_result': save_result
                })
                total_questions += len(questions)
                logger.info(f"Successfully saved {len(questions)} questions from offset {current_offset}")
            else:
                logger.error(f"Failed to save data for offset {current_offset}: {save_result.get('error')}")
        
        except Exception as e:
            logger.error(f"Error processing offset {current_offset}: {e}")
            continue
    
    # 전체 결과 반환
    return {
        'success': len(results) > 0,
        'total_files': len(results),
        'total_questions': total_questions,
        'offset_range': f"{start_offset} to {end_offset}",
        'storage_type': 'local' if save_local else 's3',
        'results': results
    }


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
        
        logger.info(f"Successfully fetched {questions_count} Q&A cases from offset {offset}")
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


def process_qna_cases(response_data: Dict[str, Any], simple_result: bool = False) -> Dict[str, Any]:
    """
    로톡 Q&A API 응답 데이터를 simpleResult 인자에 따라 정리합니다.
    
    Args:
        response_data: request_qna_cases에서 받은 API 응답 데이터
        simple_result: True면 간소화된 데이터, False면 상세 데이터 반환
        
    Returns:
        정리된 Q&A 데이터를 담은 딕셔너리
    """
    if not response_data.get('success') or not response_data.get('data'):
        logger.warning("Invalid response data provided for processing")
        return response_data
    
    questions = response_data['data'].get('questions', [])
    processed_questions = []
    
    logger.debug(f"Processing {len(questions)} questions with simple_result={simple_result}")
    
    for question in questions:
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


def get_qna_cases(session_cookie: Any, start_offset: int = 0, end_offset: int = None, 
                  simple_result: bool = False, limit_per_request: int = 10) -> Dict[str, Any]:
    """
    지정된 offset 범위의 로톡 Q&A 상담사례를 가져와서 정리합니다.
    
    Args:
        session_cookie: 인증을 위한 세션 쿠키 객체
        start_offset: 시작 offset (기본값: 0)
        end_offset: 종료 offset (None이면 한 번만 요청)
        simple_result: True면 간소화된 데이터, False면 상세 데이터
        limit_per_request: 한 번의 요청당 가져올 데이터 수 (기본값: 10)
        
    Returns:
        모든 페이지의 정리된 Q&A 데이터를 담은 딕셔너리
    """
    all_questions = []
    current_offset = start_offset
    total_fetched = 0
    
    # end_offset가 None이면 한 번만 요청
    if end_offset is None:
        end_offset = start_offset + limit_per_request
    
    logger.info(f"Starting Q&A data collection: offset {start_offset} to {end_offset}, simple_result={simple_result}")
    
    while current_offset < end_offset:
        # API 요청
        response = request_qna_cases(session_cookie, current_offset)
        
        if not response.get('success'):
            logger.error(f"Failed to fetch data at offset {current_offset}: {response.get('message', 'Unknown error')}")
            break
        
        # 데이터 처리
        processed_response = process_qna_cases(response, simple_result)
        
        if not processed_response.get('success'):
            logger.error(f"Failed to process data at offset {current_offset}")
            break
        
        questions = processed_response.get('data', {}).get('questions', [])
        
        # 데이터가 없으면 종료
        if not questions:
            logger.info(f"No more data available at offset {current_offset}")
            break
        
        all_questions.extend(questions)
        total_fetched += len(questions)
        
        logger.info(f"Successfully processed {len(questions)} questions from offset {current_offset}")
        
        # 다음 offset으로 이동
        current_offset += limit_per_request
        
        # end_offset를 초과하지 않도록 조정
        if current_offset >= end_offset:
            break
    
    # 최종 결과 구성
    result = {
        'success': True,
        'total_fetched': total_fetched,
        'start_offset': start_offset,
        'end_offset': min(current_offset, end_offset),
        'simple_result': simple_result,
        'data': {
            'questions': all_questions
        }
    }
    
    logger.info(f"Q&A data collection completed: {total_fetched} total cases fetched")
    
    return result


