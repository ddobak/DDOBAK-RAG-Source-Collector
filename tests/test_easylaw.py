import json
import pytest
from unittest.mock import MagicMock, patch

from easylaw.easylaw_crawler import EasylawCrawler, EasylawDataExtractor, EasylawPageFetcher, EasylawPaginationHandler, EasylawDataSaver
from easylaw.easylaw_config import config
from easylaw.utils import extract_url_parameters, build_full_url, clean_text, validate_qa_data, filter_qa_data_by_mode, get_category_name
from bs4 import BeautifulSoup


class TestEasylawUtils:
    """이지로 유틸리티 함수 테스트"""

    def test_extract_url_parameters(self):
        """URL 파라미터 추출 테스트"""
        url = "OnhunqueansInfoRetrieve.laf?onhunqnaAstSeq=86&onhunqueSeq=1083&curPage=2"
        params = extract_url_parameters(url)
        
        assert params['question_id'] == '1083'
        assert params['category_id'] == '86'

    def test_build_full_url(self):
        """URL 빌드 테스트"""
        base_url = "https://www.easylaw.go.kr"
        relative_url = "OnhunqueansInfoRetrieve.laf?test=1"
        
        full_url = build_full_url(base_url, relative_url)
        expected = "https://www.easylaw.go.kr/CSP/OnhunqueansInfoRetrieve.laf?test=1"
        
        assert full_url == expected

    def test_clean_text(self):
        """텍스트 정리 테스트"""
        dirty_text = "  여러    공백이   있는    텍스트  \n"
        clean = clean_text(dirty_text)
        
        assert clean == "여러 공백이 있는 텍스트"

    def test_validate_qa_data(self):
        """Q&A 데이터 유효성 검증 테스트"""
        valid_data = {
            'question_id': '1083',
            'category_id': '86',
            'category_name': '사회안전_범죄',
            'question': '테스트 질문',
            'answer': '테스트 답변',
            'detail_url': 'test.laf',
            'full_url': 'https://example.com/test.laf'
        }
        
        assert validate_qa_data(valid_data) is True
        
        # 필수 필드 누락
        invalid_data = valid_data.copy()
        del invalid_data['question']
        assert validate_qa_data(invalid_data) is False

    def test_get_category_name(self):
        """카테고리 이름 조회 테스트"""
        category_mapping = {
            '86': '사회안전_범죄',
            '25': '가정법률'
        }
        
        # 매핑된 카테고리
        assert get_category_name('86', category_mapping) == '사회안전_범죄'
        assert get_category_name('25', category_mapping) == '가정법률'
        
        # 매핑되지 않은 카테고리
        assert get_category_name('999', category_mapping) == '기타'
        assert get_category_name(None, category_mapping) == '기타'

    def test_filter_qa_data_by_mode(self):
        """Q&A 데이터 필터링 테스트"""
        test_data = [
            {
                'question_id': '1083',
                'category_id': '86',
                'category_name': '사회안전_범죄',
                'question': '테스트 질문1',
                'answer': '테스트 답변1',
                'detail_url': 'test1.laf',
                'full_url': 'https://example.com/test1.laf'
            },
            {
                'question_id': '1084',
                'category_id': '87',
                'category_name': '문화_여가생활',
                'question': '테스트 질문2',
                'answer': '테스트 답변2',
                'detail_url': 'test2.laf',
                'full_url': 'https://example.com/test2.laf'
            }
        ]
        
        # detail 모드 (simple_result=False): 모든 필드 유지
        detail_result = filter_qa_data_by_mode(test_data, simple_result=False)
        assert len(detail_result) == 2
        assert 'question_id' in detail_result[0]
        assert 'category_name' in detail_result[0]
        assert 'detail_url' in detail_result[0]
        assert 'full_url' in detail_result[0]
        
        # simple 모드 (simple_result=True): category_id, category_name, question, answer만 유지
        simple_result = filter_qa_data_by_mode(test_data, simple_result=True)
        assert len(simple_result) == 2
        assert set(simple_result[0].keys()) == {'category_id', 'category_name', 'question', 'answer'}
        assert simple_result[0]['category_id'] == '86'
        assert simple_result[0]['category_name'] == '사회안전_범죄'
        assert simple_result[0]['question'] == '테스트 질문1'
        assert simple_result[0]['answer'] == '테스트 답변1'


class TestEasylawDataExtractor:
    """EasylawDataExtractor 테스트"""
    
    def test_extract_qa_items_success(self):
        """Q&A 아이템 추출 성공 테스트"""
        html_content = '''
        <ul class="question">
            <li class="qa">
                <div class="q">
                    <div class="ttl">
                        <a href="OnhunqueansInfoRetrieve.laf?onhunqnaAstSeq=86&onhunqueSeq=1083&curPage=2&sch=&pageType=20">
                            고소ㆍ고발하는 방법을 알려주세요.
                        </a>
                    </div>
                    <div class="ans">
                        <p class="line4-text">
                            고소는 가해자를 처벌해달라고 피해자 등이 수사기관에 범죄사실을 신고하는 것을 말합니다.
                        </p>
                    </div>
                </div>
            </li>
        </ul>
        '''
        
        soup = BeautifulSoup(html_content, 'html.parser')
        extractor = EasylawDataExtractor(config)
        
        qa_items = extractor.extract_qa_items(soup)
        
        assert len(qa_items) == 1
        assert qa_items[0]['question_id'] == '1083'
        assert qa_items[0]['category_id'] == '86'
        assert '고소ㆍ고발하는 방법' in qa_items[0]['question']
        assert '고소는 가해자를' in qa_items[0]['answer']
    
    def test_extract_qa_items_no_data(self):
        """데이터가 없는 경우 테스트"""
        html_content = '<div>No question ul found</div>'
        soup = BeautifulSoup(html_content, 'html.parser')
        extractor = EasylawDataExtractor(config)
        
        qa_items = extractor.extract_qa_items(soup)
        
        assert qa_items == []


class TestEasylawPageFetcher:
    """EasylawPageFetcher 테스트"""
    
    def test_session_setup(self):
        """세션 설정 테스트"""
        fetcher = EasylawPageFetcher(config)
        
        assert 'User-Agent' in fetcher.session.headers
        assert 'Content-Type' in fetcher.session.headers
        assert fetcher.session.headers['Content-Type'] == 'application/x-www-form-urlencoded'
    
    @patch('requests.Session.post')
    def test_fetch_page_success(self, mock_post):
        """페이지 가져오기 성공 테스트"""
        mock_response = MagicMock()
        mock_response.text = '<html><body>Test content</body></html>'
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        fetcher = EasylawPageFetcher(config)
        soup = fetcher.fetch_page(1)
        
        assert soup is not None
        assert soup.find('body').text == 'Test content'
        
        # POST 요청이 올바른 데이터로 호출되었는지 확인
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs['data']['curPage'] == '1'
        assert kwargs['data']['pageTpe'] == '20'


class TestEasylawPaginationHandler:
    """EasylawPaginationHandler 테스트"""
    
    def test_has_data_true(self):
        """데이터가 있는 경우 테스트"""
        html_content = '''
        <ul class="question">
            <li class="qa">
                <div>Some content</div>
            </li>
        </ul>
        '''
        soup = BeautifulSoup(html_content, 'html.parser')
        handler = EasylawPaginationHandler(config)
        
        assert handler.has_data(soup) is True
    
    def test_has_data_false(self):
        """데이터가 없는 경우 테스트"""
        html_content = '<div>No question ul found</div>'
        soup = BeautifulSoup(html_content, 'html.parser')
        handler = EasylawPaginationHandler(config)
        
        assert handler.has_data(soup) is False
    
    def test_should_continue_crawling(self):
        """크롤링 계속 여부 테스트"""
        handler = EasylawPaginationHandler(config)
        
        assert handler.should_continue_crawling(0) is True
        assert handler.should_continue_crawling(2) is True
        assert handler.should_continue_crawling(3) is False


class TestEasylawDataSaver:
    """EasylawDataSaver 테스트"""
    
    def test_save_crawled_data_local_simple(self, tmp_path):
        """로컬 저장 Simple 모드 테스트"""
        mock_logger = MagicMock()
        saver = EasylawDataSaver(config, tmp_path, mock_logger, storage_type=True, simple_result=True)
        
        test_data = [
            {
                'question_id': '1083',
                'category_id': '86',
                'category_name': '사회안전_범죄',
                'question': '테스트 질문',
                'answer': '테스트 답변',
                'detail_url': 'test.laf',
                'full_url': 'https://example.com/test.laf'
            }
        ]
        
        saver.save_crawled_data(test_data)
        
        # 파일이 생성되었는지 확인
        json_file = tmp_path / config.OUTPUT_SUBDIR / config.JSON_FILENAME
        
        assert json_file.exists()
        
        # 저장된 데이터 확인 (simple 모드에서는 4개 필드만)
        with open(json_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert len(saved_data) == 1
        assert set(saved_data[0].keys()) == {'category_id', 'category_name', 'question', 'answer'}
        assert saved_data[0]['question'] == '테스트 질문'

    def test_save_crawled_data_local_detail(self, tmp_path):
        """로컬 저장 Detail 모드 테스트"""
        mock_logger = MagicMock()
        saver = EasylawDataSaver(config, tmp_path, mock_logger, storage_type=True, simple_result=False)
        
        test_data = [
            {
                'question_id': '1083',
                'category_id': '86',
                'category_name': '사회안전_범죄',
                'question': '테스트 질문',
                'answer': '테스트 답변',
                'detail_url': 'test.laf',
                'full_url': 'https://example.com/test.laf'
            }
        ]
        
        saver.save_crawled_data(test_data)
        
        # 파일이 생성되었는지 확인
        json_file = tmp_path / config.OUTPUT_SUBDIR / config.JSON_FILENAME
        
        # 저장된 데이터 확인 (detail 모드에서는 모든 필드)
        with open(json_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert len(saved_data) == 1
        assert 'question_id' in saved_data[0]
        assert 'detail_url' in saved_data[0]
        assert 'full_url' in saved_data[0]
    
    @patch('easylaw.easylaw_crawler.S3Manager')
    def test_save_crawled_data_s3_simple(self, mock_s3_manager_class, tmp_path):
        """S3 저장 Simple 모드 테스트"""
        mock_logger = MagicMock()
        mock_s3_manager = MagicMock()
        mock_s3_manager.upload_file.return_value = True
        mock_s3_manager_class.return_value = mock_s3_manager
        
        saver = EasylawDataSaver(config, tmp_path, mock_logger, storage_type=False, simple_result=True)
        
        test_data = [
            {
                'question_id': '1083',
                'category_id': '86',
                'category_name': '사회안전_범죄',
                'question': '테스트 질문',
                'answer': '테스트 답변',
                'detail_url': 'test.laf',
                'full_url': 'https://example.com/test.laf'
            }
        ]
        
        saver.save_crawled_data(test_data)
        
        # S3 업로드가 1번만 호출되었는지 확인 (JSON만)
        assert mock_s3_manager.upload_file.call_count == 1
        
        # 호출 확인 (Simple 파일명)
        call_args = mock_s3_manager.upload_file.call_args_list[0]
        assert config.S3_BUCKET_NAME in str(call_args)
        assert config.S3_SIMPLE_FILENAME in str(call_args)
    
    @patch('easylaw.easylaw_crawler.S3Manager')
    def test_save_crawled_data_s3_detail(self, mock_s3_manager_class, tmp_path):
        """S3 저장 Detail 모드 테스트"""
        mock_logger = MagicMock()
        mock_s3_manager = MagicMock()
        mock_s3_manager.upload_file.return_value = True
        mock_s3_manager_class.return_value = mock_s3_manager
        
        saver = EasylawDataSaver(config, tmp_path, mock_logger, storage_type=False, simple_result=False)
        
        test_data = [
            {
                'question_id': '1083',
                'category_id': '86',
                'category_name': '사회안전_범죄',
                'question': '테스트 질문',
                'answer': '테스트 답변',
                'detail_url': 'test.laf',
                'full_url': 'https://example.com/test.laf'
            }
        ]
        
        saver.save_crawled_data(test_data)
        
        # S3 업로드가 1번만 호출되었는지 확인 (JSON만)
        assert mock_s3_manager.upload_file.call_count == 1
        
        # 호출 확인 (Detail 파일명)
        call_args = mock_s3_manager.upload_file.call_args_list[0]
        assert config.S3_BUCKET_NAME in str(call_args)
        assert config.S3_DETAIL_FILENAME in str(call_args)


class TestEasylawCrawler:
    """EasylawCrawler 통합 테스트"""
    
    def test_get_site_name(self):
        """사이트 이름 테스트"""
        crawler = EasylawCrawler()
        assert crawler.get_site_name() == "easylaw"
    
    @patch('easylaw.easylaw_crawler.EasylawPageFetcher.fetch_page')
    def test_crawl_single_page(self, mock_fetch_page):
        """단일 페이지 크롤링 테스트"""
        html_content = '''
        <ul class="question">
            <li class="qa">
                <div class="q">
                    <div class="ttl">
                        <a href="OnhunqueansInfoRetrieve.laf?onhunqnaAstSeq=86&onhunqueSeq=1083">테스트 질문</a>
                    </div>
                    <div class="ans">
                        <p class="line4-text">테스트 답변</p>
                    </div>
                </div>
            </li>
        </ul>
        '''
        
        def side_effect(page_num):
            if page_num == 1:
                return BeautifulSoup(html_content, 'html.parser')
            else:
                return BeautifulSoup('<div>No data</div>', 'html.parser')
        
        mock_fetch_page.side_effect = side_effect
        
        # 테스트 옵션으로 크롤러 생성
        crawler = EasylawCrawler(crawl_options={'simple_result': True, 'storage_type': True})
        crawler.crawl()
        
        # 데이터가 수집되었는지 확인
        assert len(crawler.all_qa_data) == 1
        assert crawler.all_qa_data[0]['question'] == '테스트 질문'


@patch('easylaw.easylaw_crawler.EasylawPageFetcher.fetch_page')
def test_easylaw_crawler_integration(mock_fetch_page):
    """이지로 크롤러 통합 테스트"""
    # 첫 번째 페이지 응답
    html_content = '''
    <ul class="question">
        <li class="qa">
            <div class="q">
                <div class="ttl">
                    <a href="OnhunqueansInfoRetrieve.laf?onhunqnaAstSeq=86&onhunqueSeq=1083">첫 번째 질문</a>
                </div>
                <div class="ans">
                    <p class="line4-text">첫 번째 답변</p>
                </div>
            </div>
        </li>
    </ul>
    '''
    
    def side_effect(page_num):
        if page_num == 1:
            return BeautifulSoup(html_content, 'html.parser')
        else:
            return BeautifulSoup('<div>No data</div>', 'html.parser')
    
    mock_fetch_page.side_effect = side_effect
    
    # 크롤러 실행
    crawler = EasylawCrawler(crawl_options={'simple_result': True, 'storage_type': True})
    
    # 사이트 이름 확인
    assert crawler.get_site_name() == "easylaw"
    
    # 크롤링 실행 테스트
    crawler.crawl()
    
    # 결과 확인
    assert len(crawler.all_qa_data) == 1
    assert "첫 번째 질문" in crawler.all_qa_data[0]['question'] 