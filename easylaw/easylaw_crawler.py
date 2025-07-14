import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from common.base_crawler import BaseCrawler
from .easylaw_config import config
from .utils import extract_url_parameters, build_full_url, clean_text, validate_qa_data, filter_qa_data_by_mode, get_category_name
from utils.s3 import S3Manager


class EasylawDataExtractor:
    """이지로 Q&A 데이터 추출 전담 클래스"""
    
    def __init__(self, config):
        self.config = config
    
    def extract_qa_items(self, soup: BeautifulSoup) -> List[Dict]:
        """HTML에서 Q&A 아이템들을 추출"""
        question_ul = soup.find('ul', class_='question')
        if not question_ul:
            return []
        
        qa_items = question_ul.find_all('li', class_='qa')
        extracted_data = []
        
        for qa_item in qa_items:
            qa_data = self._extract_single_qa(qa_item)
            if qa_data and validate_qa_data(qa_data):
                extracted_data.append(qa_data)
        
        return extracted_data
    
    def _extract_single_qa(self, qa_item) -> Optional[Dict]:
        """개별 Q&A 아이템에서 데이터 추출"""
        question_div = qa_item.find('div', class_='ttl')
        answer_div = qa_item.find('div', class_='ans')
        
        if not (question_div and question_div.find('a') and answer_div):
            return None
        
        question_link = question_div.find('a')
        answer_p = answer_div.find('p', class_='line4-text')
        
        # URL과 텍스트 추출
        question_url = question_link.get('href', '')
        question_text = clean_text(question_link.get_text())
        answer_text = clean_text(answer_p.get_text()) if answer_p else ''
        
        # URL 파라미터 추출
        url_params = extract_url_parameters(question_url)
        
        # 카테고리 이름 조회
        category_id = url_params.get('category_id')
        category_name = get_category_name(category_id, self.config.CATEGORY_MAPPING) if category_id else '기타'
        
        # RAG용 통합 텍스트 내용 생성
        text_parts = []
        
        # 질문 제목 추가
        if question_text:
            text_parts.append(f"질문: {question_text}")
        
        # 답변 내용 추가
        if answer_text:
            text_parts.append(f"답변: {answer_text}")
        
        # 카테고리 정보 추가
        if category_name:
            text_parts.append(f"카테고리: {category_name}")
        
        # 통합 텍스트 생성
        text_content = "\n\n".join(text_parts)
        
        # RAG용 메타데이터 생성
        metadata = {
            "question_id": url_params.get('question_id'),
            "category_id": category_id,
            "category_name": category_name,
            "detail_url": question_url,
            "full_url": build_full_url(self.config.BASE_URL, question_url),
            "document_type": "qa",
            "crawl_date": datetime.now().isoformat()
        }
        
        return {
            'question_id': url_params.get('question_id'),
            'category_id': category_id,
            'category_name': category_name,
            'question': question_text,
            'answer': answer_text,
            'detail_url': question_url,
            'full_url': build_full_url(self.config.BASE_URL, question_url),
            # RAG 최적화 필드 추가
            'text_content': text_content,
            'title': question_text,
            'metadata': metadata
        }


class EasylawPageFetcher:
    """이지로 페이지 요청 전담 클래스"""
    
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """세션 헤더 설정"""
        self.session.headers.update(self.config.BASE_HEADERS)
    
    def fetch_page(self, page_num: int, search_query: str = '') -> Optional[BeautifulSoup]:
        """특정 페이지의 HTML 가져오기"""
        payload = self.config.QNA_LIST_PAYLOAD_KEYS.copy()
        payload['curPage'] = str(page_num)
        payload['sch'] = search_query
        
        try:
            response = self.session.post(
                self.config.QNA_LIST_URL, 
                data=payload, 
                timeout=self.config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            return BeautifulSoup(response.text, 'html.parser')
            
        except requests.RequestException as e:
            print(f"Page {page_num} 요청 실패: {e}")
            return None


class EasylawPaginationHandler:
    """이지로 페이지네이션 처리 전담 클래스"""
    
    def __init__(self, config):
        self.config = config
    
    def has_data(self, soup: BeautifulSoup) -> bool:
        """페이지에 데이터가 있는지 확인"""
        question_ul = soup.find('ul', class_='question')
        if not question_ul:
            return False
        
        qa_items = question_ul.find_all('li', class_='qa')
        return len(qa_items) > 0
    
    def should_continue_crawling(self, consecutive_empty_pages: int) -> bool:
        """크롤링을 계속할지 결정"""
        return consecutive_empty_pages < self.config.MAX_CONSECUTIVE_EMPTY_PAGES


class EasylawDataSaver:
    """이지로 데이터 저장 전담 클래스"""
    
    def __init__(self, config, output_dir: Path, logger, storage_type: bool = True, simple_result: bool = True):
        self.config = config
        self.output_dir = output_dir
        self.logger = logger
        self.storage_type = storage_type  # True: 로컬, False: S3
        self.simple_result = simple_result  # True: 간단한 필드만, False: 모든 필드
        if not storage_type:  # S3 모드일 때만 S3Manager 초기화
            self.s3_manager = S3Manager()
    
    def save_crawled_data(self, qa_data_list: List[Dict]) -> None:
        """크롤링한 데이터를 파일로 저장"""
        if not qa_data_list:
            self.logger.warning("No data to save")
            return
        
        # 결과 모드에 따라 데이터 필터링
        filtered_data = filter_qa_data_by_mode(qa_data_list, self.simple_result)
        
        if self.storage_type:
            self._save_to_local(filtered_data)
        else:
            self._save_to_s3(filtered_data)
    
    def _save_to_local(self, qa_data_list: List[Dict]) -> None:
        """로컬 파일 시스템에 개별 txt 파일로 저장"""
        # 데이터 디렉토리 생성
        data_dir = self.output_dir / self.config.OUTPUT_SUBDIR
        data_dir.mkdir(exist_ok=True)
        
        # 개별 txt 파일로 저장
        saved_count = 0
        for i, qa_data in enumerate(qa_data_list):
            try:
                # 파일명 생성 (question_id가 있으면 사용, 없으면 인덱스 사용)
                question_id = qa_data.get('question_id', f'{i+1:04d}')
                filename = f"qa_{question_id}.txt"
                filepath = data_dir / filename
                
                # 텍스트 내용 생성 (question과 answer 필드 결합)
                text_content = ""
                if qa_data.get('question'):
                    text_content += qa_data['question']
                if qa_data.get('answer'):
                    if text_content:  # question이 있으면 줄바꿈 추가
                        text_content += "\n\n"
                    text_content += qa_data['answer']
                
                # 개별 txt 파일로 저장
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                
                saved_count += 1
                
            except Exception as e:
                self.logger.error(f"Error saving Q&A {qa_data.get('question_id', i)}: {e}")
        
        self.logger.info(f"Data saved to {saved_count} individual txt files in {data_dir}")
        
        # 호환성을 위해 기존 통합 JSON 파일도 저장
        json_file = data_dir / self.config.JSON_FILENAME
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(qa_data_list, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Legacy combined JSON file also saved: {json_file}")
    
    def _save_to_s3(self, qa_data_list: List[Dict]) -> None:
        """S3에 개별 txt 파일로 저장"""
        try:
            from io import BytesIO
            
            # 개별 txt 파일로 S3에 저장
            saved_count = 0
            for i, qa_data in enumerate(qa_data_list):
                try:
                    # 파일명 생성 (question_id가 있으면 사용, 없으면 인덱스 사용)
                    question_id = qa_data.get('question_id', f'{i+1:04d}')
                    filename = f"qa_{question_id}.txt"
                    
                    # S3 키 생성
                    txt_key = f"{self.config.S3_BASE_PREFIX}/{filename}"
                    
                    # 텍스트 내용 생성 (question과 answer 필드 결합)
                    text_content = ""
                    if qa_data.get('question'):
                        text_content += qa_data['question']
                    if qa_data.get('answer'):
                        if text_content:  # question이 있으면 줄바꿈 추가
                            text_content += "\n\n"
                        text_content += qa_data['answer']
                    
                    # 텍스트 데이터를 BytesIO로 준비
                    text_bytes = text_content.encode('utf-8')
                    text_buffer = BytesIO(text_bytes)
                    
                    # S3에 업로드
                    upload_result = self.s3_manager.upload_file(
                        file_path_or_obj=text_buffer,
                        bucket=self.config.S3_BUCKET_NAME,
                        key=txt_key
                    )
                    
                    if upload_result:
                        saved_count += 1
                    else:
                        self.logger.error(f"Failed to upload Q&A {question_id} to S3")
                        
                except Exception as e:
                    self.logger.error(f"Error uploading Q&A {qa_data.get('question_id', i)} to S3: {e}")
            
            self.logger.info(f"Uploaded {saved_count} individual txt files to S3")
            
            # 호환성을 위해 기존 통합 JSON 파일도 저장
            if self.simple_result:
                filename = self.config.S3_SIMPLE_FILENAME
            else:
                filename = self.config.S3_DETAIL_FILENAME
            
            json_key = f"{self.config.S3_BASE_PREFIX}/{filename}"
            json_content = json.dumps(qa_data_list, ensure_ascii=False, indent=2)
            json_bytes = json_content.encode('utf-8')
            json_buffer = BytesIO(json_bytes)
            
            upload_result = self.s3_manager.upload_file(
                file_path_or_obj=json_buffer,
                bucket=self.config.S3_BUCKET_NAME,
                key=json_key
            )
            
            if upload_result:
                self.logger.info(f"Legacy combined JSON file also uploaded to S3: s3://{self.config.S3_BUCKET_NAME}/{json_key}")
            
        except Exception as e:
            self.logger.error(f"S3 upload failed: {str(e)}")
            # S3 실패시 로컬에 백업 저장
            self.logger.info("Falling back to local storage")
            self._save_to_local(qa_data_list)
    




class EasylawCrawler(BaseCrawler):
    """이지로 크롤러 메인 클래스"""
    
    def __init__(self, crawl_options: Optional[Dict] = None):
        super().__init__(crawl_options)
        self.config = config
        self.page_fetcher = EasylawPageFetcher(self.config)
        self.data_extractor = EasylawDataExtractor(self.config)
        self.pagination_handler = EasylawPaginationHandler(self.config)
        
        # storage_type: True=로컬, False=S3
        storage_type = self.crawl_options.get('storage_type', True)
        simple_result = self.crawl_options.get('simple_result', True)
        self.data_saver = EasylawDataSaver(self.config, self.output_dir, self.logger, storage_type, simple_result)
        self.all_qa_data = []
    
    def get_site_name(self) -> str:
        """사이트 이름 반환"""
        return "easylaw"
    
    def crawl(self) -> None:
        """이지로 Q&A 데이터 크롤링 실행"""
        self.logger.info("Starting Easylaw Q&A crawling...")
        
        try:
            self._crawl_all_pages()
            self.data_saver.save_crawled_data(self.all_qa_data)
            
            self.logger.info(f"Crawling completed successfully. Total items: {len(self.all_qa_data)}")
            
        except Exception as e:
            self.logger.error(f"Crawling failed: {str(e)}")
            raise
    
    def _crawl_all_pages(self) -> None:
        """모든 페이지 크롤링"""
        page_num = self.config.PAGE_START
        consecutive_empty_pages = 0
        
        # 테스트 모드인지 확인 (간단한 결과 모드일 때는 5페이지만)
        max_pages = float('inf')
        
        while (self.pagination_handler.should_continue_crawling(consecutive_empty_pages) and 
               page_num <= max_pages):
            self.logger.info(f"Crawling page {page_num}...")
            
            soup = self.page_fetcher.fetch_page(page_num)
            if not soup:
                consecutive_empty_pages += 1
                page_num += 1
                continue
            
            # 페이지에 데이터가 있는지 확인
            if not self.pagination_handler.has_data(soup):
                consecutive_empty_pages += 1
                self.logger.info(f"Page {page_num} has no data")
            else:
                consecutive_empty_pages = 0  # 데이터가 있으면 카운터 리셋
                qa_items = self.data_extractor.extract_qa_items(soup)
                
                if qa_items:
                    self.all_qa_data.extend(qa_items)
                    self.logger.info(f"Page {page_num}: Extracted {len(qa_items)} Q&A items")
                else:
                    consecutive_empty_pages += 1
            
            page_num += 1
            
            # 요청 간 지연
            time.sleep(self.config.REQUEST_INTERVAL)
        
        self.logger.info(f"Crawling finished. Total pages processed: {page_num - 1}") 