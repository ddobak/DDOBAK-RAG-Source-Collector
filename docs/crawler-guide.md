# 크롤러 개발 가이드

DDOBAK RAG Source Collector에서 새로운 크롤러를 개발하는 방법에 대한 상세한 가이드입니다.

## 🏗️ 크롤러 아키텍처 개요

### BaseCrawler 추상 클래스

모든 크롤러는 `BaseCrawler`를 상속받아 구현합니다:

```python
from abc import ABC, abstractmethod
from common.base_crawler import BaseCrawler

class YourCrawler(BaseCrawler):
    @abstractmethod
    def get_site_name(self) -> str:
        """사이트 이름 반환"""
        pass
    
    @abstractmethod  
    def crawl(self) -> None:
        """크롤링 로직 구현"""
        pass
```

### 공통 기능

BaseCrawler에서 제공하는 공통 기능들:

- **로깅**: 자동 설정된 로거 (`self.logger`)
- **출력 디렉터리**: 자동 생성된 출력 경로 (`self.output_dir`)
- **크롤링 옵션**: 설정 옵션 관리 (`self.crawl_options`)
- **실행 흐름**: 표준화된 실행 흐름 (`run()` 메서드)

## 🔧 새 크롤러 개발 단계

### 1. 프로젝트 구조 설정

```bash
# 새 사이트 모듈 생성
mkdir new_site
cd new_site

# 필수 파일 생성
touch __init__.py
touch crawler.py
touch config.py
```

### 2. 크롤러 클래스 구현

#### 기본 구조

```python
# new_site/crawler.py
from typing import Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

from common.base_crawler import BaseCrawler
from utils.utils import save_json_data_to_local
from .config import NewSiteConfig


class NewSiteCrawler(BaseCrawler):
    """새 사이트 크롤러"""
    
    def __init__(self, crawl_options: Optional[Dict[str, Any]] = None):
        super().__init__(crawl_options)
        self.config = NewSiteConfig()
        self.session = requests.Session()
        
    def get_site_name(self) -> str:
        """사이트 이름 반환"""
        return "new_site"
    
    def crawl(self) -> None:
        """크롤링 메인 로직"""
        self.logger.info("Starting new site crawling")
        
        try:
            # 1. 로그인 (필요한 경우)
            self._login()
            
            # 2. 데이터 수집
            data = self._fetch_data()
            
            # 3. 데이터 저장
            self._save_data(data)
            
            self.logger.info("Crawling completed successfully")
            
        except Exception as e:
            self.logger.error(f"Crawling failed: {e}")
            raise
        finally:
            # 4. 정리 작업
            self._cleanup()
    
    def _login(self) -> None:
        """로그인 처리"""
        # 로그인 로직 구현
        pass
    
    def _fetch_data(self) -> Dict[str, Any]:
        """데이터 수집"""
        # 데이터 수집 로직 구현
        return {}
    
    def _save_data(self, data: Dict[str, Any]) -> None:
        """데이터 저장"""
        # 저장 로직 구현
        pass
    
    def _cleanup(self) -> None:
        """정리 작업"""
        # 세션 정리 등
        if hasattr(self, 'session'):
            self.session.close()
```

### 3. 설정 클래스 구현

```python
# new_site/config.py
import os
from typing import Dict


class NewSiteConfig:
    """새 사이트 설정"""
    
    # 기본 URL
    BASE_URL = "https://example.com"
    API_URL = f"{BASE_URL}/api"
    
    # 인증 정보 (환경변수에서 로드)
    USERNAME = os.getenv("NEW_SITE_USERNAME")
    PASSWORD = os.getenv("NEW_SITE_PASSWORD")
    
    # 크롤링 설정
    REQUEST_INTERVAL = 1  # 요청 간격 (초)
    MAX_RETRIES = 3       # 최대 재시도 횟수
    TIMEOUT = 30          # 요청 타임아웃 (초)
    
    # 데이터 설정
    DEFAULT_LIMIT = 10    # 기본 수집 개수
    MAX_LIMIT = 100       # 최대 수집 개수
    
    # 헤더 설정
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    }
    
    @classmethod
    def validate_config(cls) -> bool:
        """설정 유효성 검사"""
        if not cls.USERNAME or not cls.PASSWORD:
            return False
        return True
```

### 4. Poetry Entry Point 등록

```toml
# pyproject.toml에 추가
[tool.poetry.plugins."ddobak.crawlers"]
new_site = "new_site.crawler:NewSiteCrawler"
```

### 5. 테스트 작성

```python
# tests/test_new_site.py
import pytest
from unittest.mock import Mock, patch

from new_site.crawler import NewSiteCrawler
from new_site.config import NewSiteConfig


class TestNewSiteCrawler:
    """새 사이트 크롤러 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.crawler = NewSiteCrawler()
    
    def test_get_site_name(self):
        """사이트 이름 테스트"""
        assert self.crawler.get_site_name() == "new_site"
    
    def test_config_validation(self):
        """설정 유효성 테스트"""
        # 환경변수 설정 후 테스트
        with patch.dict('os.environ', {
            'NEW_SITE_USERNAME': 'test_user',
            'NEW_SITE_PASSWORD': 'test_pass'
        }):
            config = NewSiteConfig()
            assert config.validate_config() is True
    
    @patch('requests.Session.get')
    def test_fetch_data(self, mock_get):
        """데이터 수집 테스트"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.json.return_value = {"test": "data"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # 테스트 실행
        data = self.crawler._fetch_data()
        
        # 검증
        assert "test" in data
        mock_get.assert_called_once()
    
    def test_crawl_integration(self):
        """통합 크롤링 테스트"""
        # 실제 크롤링 로직 테스트
        # 주의: 실제 네트워크 호출 방지를 위해 Mock 사용
        pass
```

## 📚 구현 예시

### 1. 간단한 웹 크롤러

```python
class SimpleWebCrawler(BaseCrawler):
    """간단한 웹페이지 크롤러"""
    
    def get_site_name(self) -> str:
        return "simple_web"
    
    def crawl(self) -> None:
        url = "https://example.com/data"
        
        # HTTP 요청
        response = requests.get(url)
        response.raise_for_status()
        
        # HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 데이터 추출
        items = []
        for element in soup.find_all('div', class_='data-item'):
            item = {
                'title': element.find('h2').text.strip(),
                'content': element.find('p').text.strip(),
                'url': element.find('a')['href']
            }
            items.append(item)
        
        # 데이터 저장
        data = {
            'success': True,
            'total_fetched': len(items),
            'data': {'items': items}
        }
        
        file_path = f"{self.get_site_name()}/data.json"
        save_json_data_to_local(data, self.output_dir, file_path)
```

### 2. API 기반 크롤러

```python
class APICrawler(BaseCrawler):
    """API 기반 크롤러"""
    
    def get_site_name(self) -> str:
        return "api_site"
    
    def crawl(self) -> None:
        # API 인증
        auth_token = self._authenticate()
        
        # 헤더 설정
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        
        # 페이지네이션을 통한 데이터 수집
        all_data = []
        page = 1
        
        while True:
            # API 요청
            response = requests.get(
                f"https://api.example.com/data?page={page}",
                headers=headers
            )
            
            if response.status_code != 200:
                break
                
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                break
                
            all_data.extend(items)
            page += 1
            
            # 요청 간격 조절
            time.sleep(self.config.REQUEST_INTERVAL)
        
        # 데이터 저장
        result = {
            'success': True,
            'total_fetched': len(all_data),
            'data': {'items': all_data}
        }
        
        file_path = f"{self.get_site_name()}/api_data.json"
        save_json_data_to_local(result, self.output_dir, file_path)
    
    def _authenticate(self) -> str:
        """API 인증"""
        auth_data = {
            'username': self.config.USERNAME,
            'password': self.config.PASSWORD
        }
        
        response = requests.post(
            "https://api.example.com/auth",
            json=auth_data
        )
        
        response.raise_for_status()
        return response.json()['access_token']
```

### 3. Selenium 기반 크롤러

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class SeleniumCrawler(BaseCrawler):
    """Selenium 기반 동적 페이지 크롤러"""
    
    def __init__(self, crawl_options=None):
        super().__init__(crawl_options)
        self.driver = None
    
    def get_site_name(self) -> str:
        return "dynamic_site"
    
    def crawl(self) -> None:
        try:
            # 웹드라이버 초기화
            self._setup_driver()
            
            # 페이지 로드
            self.driver.get("https://dynamic-example.com")
            
            # 로그인 (필요한 경우)
            self._login()
            
            # 동적 콘텐츠 대기
            wait = WebDriverWait(self.driver, 10)
            
            # 데이터 수집
            items = []
            elements = wait.until(
                EC.presence_of_all_elements_located(
                    (By.CLASS_NAME, "data-item")
                )
            )
            
            for element in elements:
                item = {
                    'title': element.find_element(By.TAG_NAME, 'h2').text,
                    'content': element.find_element(By.TAG_NAME, 'p').text
                }
                items.append(item)
            
            # 데이터 저장
            data = {
                'success': True,
                'total_fetched': len(items),
                'data': {'items': items}
            }
            
            file_path = f"{self.get_site_name()}/dynamic_data.json"
            save_json_data_to_local(data, self.output_dir, file_path)
            
        finally:
            self._cleanup()
    
    def _setup_driver(self) -> None:
        """웹드라이버 설정"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # 헤드리스 모드
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        self.driver = webdriver.Chrome(options=options)
    
    def _login(self) -> None:
        """로그인 처리"""
        username_field = self.driver.find_element(By.NAME, "username")
        password_field = self.driver.find_element(By.NAME, "password")
        
        username_field.send_keys(self.config.USERNAME)
        password_field.send_keys(self.config.PASSWORD)
        
        login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        
        # 로그인 완료 대기
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard"))
        )
    
    def _cleanup(self) -> None:
        """정리 작업"""
        if self.driver:
            self.driver.quit()
```

## 🔧 고급 기능

### 1. 증분 크롤링 구현

```python
class IncrementalCrawler(BaseCrawler):
    """증분 크롤링을 지원하는 크롤러"""
    
    def crawl(self) -> None:
        # 마지막 크롤링 시간 확인
        last_crawl_time = self._get_last_crawl_time()
        only_new = self.crawl_options.get('only_new', False)
        
        if only_new and last_crawl_time:
            self.logger.info(f"Incremental crawling since {last_crawl_time}")
            data = self._fetch_new_data(last_crawl_time)
        else:
            self.logger.info("Full crawling")
            data = self._fetch_all_data()
        
        # 현재 시간을 저장
        self._save_crawl_time()
        
        # 데이터 저장
        self._save_data(data)
    
    def _get_last_crawl_time(self) -> Optional[datetime]:
        """마지막 크롤링 시간 조회"""
        try:
            with open(f"{self.output_dir}/.last_crawl", 'r') as f:
                timestamp = f.read().strip()
                return datetime.fromisoformat(timestamp)
        except FileNotFoundError:
            return None
    
    def _save_crawl_time(self) -> None:
        """크롤링 시간 저장"""
        os.makedirs(self.output_dir, exist_ok=True)
        with open(f"{self.output_dir}/.last_crawl", 'w') as f:
            f.write(datetime.now().isoformat())
```

### 2. 병렬 처리 구현

```python
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor


class ParallelCrawler(BaseCrawler):
    """병렬 처리를 지원하는 크롤러"""
    
    async def crawl_async(self) -> None:
        """비동기 크롤링"""
        urls = self._get_urls_to_crawl()
        
        async with aiohttp.ClientSession() as session:
            tasks = [self._fetch_url(session, url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 처리
        successful_results = [r for r in results if not isinstance(r, Exception)]
        self._save_data(successful_results)
    
    async def _fetch_url(self, session: aiohttp.ClientSession, url: str) -> Dict:
        """개별 URL 크롤링"""
        try:
            async with session.get(url) as response:
                data = await response.json()
                return {'url': url, 'data': data, 'success': True}
        except Exception as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return {'url': url, 'error': str(e), 'success': False}
    
    def crawl(self) -> None:
        """동기 크롤링 (비동기 호출)"""
        asyncio.run(self.crawl_async())
```

## 🧪 테스트 모범 사례

### 1. 단위 테스트

```python
class TestCrawlerMethods:
    """크롤러 메서드별 단위 테스트"""
    
    @patch('requests.get')
    def test_fetch_data_success(self, mock_get):
        """데이터 수집 성공 테스트"""
        # Given
        mock_response = Mock()
        mock_response.json.return_value = {'data': 'test'}
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        crawler = YourCrawler()
        
        # When
        result = crawler._fetch_data()
        
        # Then
        assert result['data'] == 'test'
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_fetch_data_failure(self, mock_get):
        """데이터 수집 실패 테스트"""
        # Given
        mock_get.side_effect = requests.RequestException("Network error")
        crawler = YourCrawler()
        
        # When & Then
        with pytest.raises(requests.RequestException):
            crawler._fetch_data()
```

### 2. 통합 테스트

```python
class TestCrawlerIntegration:
    """크롤러 통합 테스트"""
    
    def test_full_crawl_process(self):
        """전체 크롤링 프로세스 테스트"""
        crawler = YourCrawler({
            'simple_result': True,
            'storage_type': 'local',
            'only_new': False
        })
        
        # 실제 크롤링 실행 (테스트 환경)
        crawler.crawl()
        
        # 결과 검증
        assert os.path.exists(crawler.output_dir)
        # 저장된 파일 확인 등
```

## 📋 체크리스트

새 크롤러 개발 완료 전 확인사항:

- [ ] `BaseCrawler`를 상속받고 필수 메서드 구현
- [ ] 설정 클래스 구현 및 환경변수 설정
- [ ] `pyproject.toml`에 Entry Point 등록
- [ ] 단위 테스트 및 통합 테스트 작성
- [ ] 에러 처리 및 로깅 구현
- [ ] 리소스 정리 (`_cleanup` 메서드)
- [ ] 요청 간격 조절 (서버 부하 방지)
- [ ] 증분 크롤링 지원 (필요한 경우)
- [ ] 문서화 (주석 및 docstring)

## 🚀 배포 및 실행

```bash
# 의존성 재설치
poetry install

# 새 크롤러 실행
poetry run start new_site

# 테스트 실행
poetry run pytest tests/test_new_site.py -v
```

이 가이드를 따라하면 DDOBAK RAG Source Collector의 아키텍처에 맞는 새로운 크롤러를 성공적으로 개발할 수 있습니다. 