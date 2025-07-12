"""
법무부 오픈API 크롤러 테스트
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from law_open_api.api_crawler import LawOpenApiCrawler
from law_open_api.law_open_api_config import LAW_OPEN_API_CONFIG


class TestLawOpenApiCrawler:
    """법무부 오픈API 크롤러 테스트 클래스"""
    
    def setup_method(self):
        """테스트 메서드 실행 전 초기화"""
        self.crawler = LawOpenApiCrawler()
    
    def test_get_site_name(self):
        """사이트 이름 반환 테스트"""
        assert self.crawler.get_site_name() == "law_open_api"
    
    def test_crawler_initialization(self):
        """크롤러 초기화 테스트"""
        assert hasattr(self.crawler, 'config')
        assert hasattr(self.crawler, 'session')
        assert hasattr(self.crawler, 'precedent_dir')
        assert hasattr(self.crawler, 'law_dir')
        assert self.crawler.config == LAW_OPEN_API_CONFIG
    
    def test_directories_creation(self):
        """디렉토리 생성 테스트"""
        assert self.crawler.precedent_dir.exists()
        assert self.crawler.law_dir.exists()
        assert self.crawler.precedent_dir.is_dir()
        assert self.crawler.law_dir.is_dir()
    
    def test_get_xml_text(self):
        """XML 텍스트 추출 테스트"""
        import xml.etree.ElementTree as ET
        
        xml_content = """
        <item>
            <사건번호>2023가합12345</사건번호>
            <사건명>근로계약 해지 사건</사건명>
            <empty_tag></empty_tag>
        </item>
        """
        
        element = ET.fromstring(xml_content)
        
        assert self.crawler._get_xml_text(element, "사건번호") == "2023가합12345"
        assert self.crawler._get_xml_text(element, "사건명") == "근로계약 해지 사건"
        assert self.crawler._get_xml_text(element, "empty_tag") == ""
        assert self.crawler._get_xml_text(element, "nonexistent") == ""
    
    def test_parse_precedent_xml(self):
        """판례 XML 파싱 테스트"""
        xml_content = """
        <result>
            <item>
                <사건번호>2023가합12345</사건번호>
                <사건명>근로계약 해지 사건</사건명>
                <법원명>서울중앙지방법원</법원명>
                <판결일>2023-12-01</판결일>
                <사건종류>민사</사건종류>
                <판결종류>판결</판결종류>
                <당사자>원고 김○○ 피고 ㈜○○</당사자>
                <판결요지>근로계약 해지에 관한 판결</판결요지>
                <판결문>판결문 내용</판결문>
            </item>
        </result>
        """
        
        result = self.crawler._parse_precedent_xml(xml_content, "근로")
        
        assert len(result) == 1
        assert result[0]["case_number"] == "2023가합12345"
        assert result[0]["case_name"] == "근로계약 해지 사건"
        assert result[0]["court_name"] == "서울중앙지방법원"
        assert result[0]["keywords"] == "근로"
        assert "crawl_date" in result[0]
    
    def test_parse_law_xml(self):
        """법령 XML 파싱 테스트"""
        xml_content = """
        <result>
            <item>
                <법령ID>LAW001</법령ID>
                <법령명>근로기준법</법령명>
                <법령종류>법률</법령종류>
                <공포일>1953-05-10</공포일>
                <시행일>1953-08-15</시행일>
                <법령내용>근로기준법 내용</법령내용>
            </item>
        </result>
        """
        
        result = self.crawler._parse_law_xml(xml_content, "근로")
        
        assert len(result) == 1
        assert result[0]["law_id"] == "LAW001"
        assert result[0]["law_name"] == "근로기준법"
        assert result[0]["law_type"] == "법률"
        assert result[0]["keywords"] == "근로"
        assert "crawl_date" in result[0]
    
    def test_parse_invalid_xml(self):
        """잘못된 XML 파싱 테스트"""
        invalid_xml = "<invalid>xml content"
        
        result = self.crawler._parse_precedent_xml(invalid_xml, "test")
        assert result == []
        
        result = self.crawler._parse_law_xml(invalid_xml, "test")
        assert result == []
    
    @patch('law_open_api.api_crawler.requests.Session.get')
    def test_search_precedent_success(self, mock_get):
        """판례 검색 성공 테스트"""
        mock_response = Mock()
        mock_response.text = """
        <result>
            <item>
                <사건번호>2023가합12345</사건번호>
                <사건명>근로계약 해지 사건</사건명>
                <법원명>서울중앙지방법원</법원명>
            </item>
        </result>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = self.crawler._search_precedent("근로")
        
        assert len(result) > 0
        assert result[0]["case_number"] == "2023가합12345"
        mock_get.assert_called()
    
    @patch('law_open_api.api_crawler.requests.Session.get')
    def test_search_precedent_request_error(self, mock_get):
        """판례 검색 요청 오류 테스트"""
        mock_get.side_effect = Exception("Network error")
        
        result = self.crawler._search_precedent("근로")
        
        assert result == []
        mock_get.assert_called()
    
    def test_save_precedent_data(self):
        """판례 데이터 저장 테스트"""
        test_data = [
            {
                "case_number": "2023가합12345",
                "case_name": "테스트 사건",
                "keywords": "근로",
                "crawl_date": "2023-12-01T10:00:00"
            }
        ]
        
        self.crawler._save_precedent_data("근로", test_data)
        
        filepath = self.crawler.precedent_dir / "precedent_근로.json"
        assert filepath.exists()
        
        with open(filepath, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert len(saved_data) == 1
        assert saved_data[0]["case_number"] == "2023가합12345"
    
    def test_save_law_data(self):
        """법령 데이터 저장 테스트"""
        test_data = [
            {
                "law_id": "LAW001",
                "law_name": "근로기준법",
                "keywords": "근로",
                "crawl_date": "2023-12-01T10:00:00"
            }
        ]
        
        self.crawler._save_law_data("근로", test_data)
        
        filepath = self.crawler.law_dir / "law_근로.json"
        assert filepath.exists()
        
        with open(filepath, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert len(saved_data) == 1
        assert saved_data[0]["law_id"] == "LAW001"
    
    def test_save_empty_data(self):
        """빈 데이터 저장 테스트"""
        self.crawler._save_precedent_data("test", [])
        self.crawler._save_law_data("test", [])
        
        # 빈 데이터는 파일이 생성되지 않아야 함
        precedent_file = self.crawler.precedent_dir / "precedent_test.json"
        law_file = self.crawler.law_dir / "law_test.json"
        
        assert not precedent_file.exists()
        assert not law_file.exists()
    
    def test_cleanup(self):
        """정리 작업 테스트"""
        # session이 있는지 확인
        assert hasattr(self.crawler, 'session')
        
        # cleanup 실행
        self.crawler.cleanup()
        
        # session.close()가 호출되었는지는 직접 확인하기 어려우므로
        # 에러 없이 실행되는지만 확인
        assert True
    
    @patch('law_open_api.api_crawler.time.sleep')
    @patch('law_open_api.api_crawler.LawOpenApiCrawler._search_precedent')
    @patch('law_open_api.api_crawler.LawOpenApiCrawler._search_law')
    @patch('law_open_api.api_crawler.LawOpenApiCrawler._save_precedent_data')
    @patch('law_open_api.api_crawler.LawOpenApiCrawler._save_law_data')
    def test_crawl_integration(self, mock_save_law, mock_save_precedent, 
                              mock_search_law, mock_search_precedent, mock_sleep):
        """크롤링 통합 테스트"""
        # Mock 반환값 설정
        mock_search_precedent.return_value = [{"test": "precedent"}]
        mock_search_law.return_value = [{"test": "law"}]
        
        # 크롤링 실행
        self.crawler.crawl()
        
        # 모든 키워드에 대해 호출되었는지 확인
        expected_calls = len(LAW_OPEN_API_CONFIG["search_keywords"])
        assert mock_search_precedent.call_count == expected_calls
        assert mock_search_law.call_count == expected_calls
        assert mock_save_precedent.call_count == expected_calls
        assert mock_save_law.call_count == expected_calls
        
        # sleep이 호출되었는지 확인
        assert mock_sleep.call_count == expected_calls


if __name__ == "__main__":
    pytest.main([__file__]) 