# 아키텍처 가이드

DDOBAK RAG Source Collector의 아키텍처 설계 원칙과 구조에 대한 상세한 설명입니다.

## 🏛️ 설계 원칙

### 1. 클린 아키텍처 (Clean Architecture)

프로젝트는 로버트 마틴의 클린 아키텍처 원칙을 따릅니다:

- **관심사 분리**: 각 모듈은 단일 책임을 가집니다
- **의존성 역전**: 고수준 모듈이 저수준 모듈에 의존하지 않습니다
- **인터페이스 분리**: 필요한 인터페이스만 노출합니다

### 2. 모듈화 설계

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Main (CLI)    │    │   Config        │    │   Utils         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         v                       v                       v
┌─────────────────────────────────────────────────────────────────┐
│                        Common Layer                             │
│  ┌───────────────┐              ┌─────────────────────────────┐ │
│  │ BaseCrawler   │              │ CrawlerRegistry             │ │
│  │ (Abstract)    │              │ (Plugin System)             │ │
│  └───────────────┘              └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                                   │
         v                                   v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Lawtalk        │    │  LawOpenAPI     │    │  EasyLaw        │
│  Crawler        │    │  Crawler        │    │  Crawler        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🏗️ 계층 구조

### 1. 프레젠테이션 계층 (Presentation Layer)

**위치**: `main.py`

```python
# CLI 인터페이스
@click.command()
def main(site: str, simple_result: str, storage_type: str, only_new: str):
    # 인자 검증
    # 크롤러 생성
    # 실행
```

**책임**:
- CLI 인터페이스 제공
- 사용자 입력 검증
- 크롤링 실행 조율

### 2. 비즈니스 로직 계층 (Business Logic Layer)

**위치**: `common/`, 각 크롤러 모듈

```python
# 크롤러 베이스 클래스
class BaseCrawler(ABC):
    @abstractmethod
    def get_site_name(self) -> str: ...
    
    @abstractmethod
    def crawl(self) -> None: ...
    
    def run(self) -> None:
        # 공통 실행 흐름
```

**책임**:
- 크롤링 비즈니스 로직
- 데이터 처리 및 변환
- 에러 처리 및 로깅

### 3. 데이터 액세스 계층 (Data Access Layer)

**위치**: `utils/`

```python
# 로컬 파일 저장
def save_json_data_to_local(data, base_dir, file_path): ...

# S3 저장
class S3Manager:
    def save_file(self, bucket, key, data): ...
```

**책임**:
- 데이터 저장소 추상화
- 파일 I/O 처리
- 외부 서비스 통신

## 🔌 플러그인 시스템

### Poetry Entry Points 기반 구조

```toml
# pyproject.toml
[tool.poetry.plugins."ddobak.crawlers"]
lawtalk = "lawtalk.lawtalk_crawler:LawtalkCrawler"
law_open_api = "law_open_api.api_crawler:LawOpenAPICrawler"
```

### 동적 로딩 메커니즘

```python
# common/crawler_registry.py
def get_available_crawlers():
    crawlers = {}
    eps = entry_points(group='ddobak.crawlers')
    for ep in eps:
        crawlers[ep.name] = ep
    return crawlers

def create_crawler(site: str, options: dict):
    crawler_class = crawlers[site].load()
    return crawler_class(options)
```

**장점**:
- 새 크롤러 추가시 코드 수정 불필요
- 런타임 크롤러 발견
- 모듈 간 느슨한 결합

## 📊 데이터 흐름

### 1. 설정 데이터 흐름

```
[.env] → [config.py] → [LawtalkConfig] → [Crawler]
  ↑         ↑              ↑              ↑
환경변수   전역설정      사이트별설정    크롤러인스턴스
```

## 🧩 확장성 설계

### 1. 새로운 크롤러 추가

```python
# 1. 크롤러 클래스 구현
class NewSiteCrawler(BaseCrawler):
    def get_site_name(self) -> str:
        return "new_site"
    
    def crawl(self) -> None:
        # 사이트별 크롤링 로직
        pass

# 2. pyproject.toml에 등록
[tool.poetry.plugins."ddobak.crawlers"]
new_site = "new_site.crawler:NewSiteCrawler"

# 3. 즉시 사용 가능
poetry run start new_site
```

### 2. 새로운 저장소 타입 추가

```python
# utils/new_storage.py
class CloudStorageManager:
    def save_data(self, data, path): ...
    def load_data(self, path): ...

# 기존 코드 수정 없이 사용 가능
```

## 🔒 보안 설계

### 1. 환경변수 기반 설정

```python
# 민감한 정보는 환경변수로 관리
LAWTALK_ID = os.getenv("LAWTALK_ID")
LAWTALK_PW = os.getenv("LAWTALK_PW")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
```

### 2. 세션 관리

```python
# 로그인 세션 안전 관리
class LawtalkCrawler:
    def _login(self):
        # 로그인 후 세션 쿠키 저장
        self.session_cookie = response.cookies['connect.sid']
    
    def cleanup(self):
        # 크롤링 후 세션 정리
        self.session = None
```

## 📈 성능 고려사항

### 1. 메모리 효율성

- **스트리밍 처리**: 대용량 데이터를 메모리에 모두 로드하지 않음
- **배치 처리**: 데이터를 청크 단위로 처리
- **지연 로딩**: 필요할 때만 데이터 로드

### 2. 네트워크 최적화

- **요청 간격 조절**: `REQUEST_INTERVAL` 설정으로 서버 부하 방지
- **세션 재사용**: HTTP 연결 풀 활용
- **재시도 로직**: 일시적 네트워크 오류 처리

### 3. 증분 크롤링

```python
# 마지막 크롤링 시간 기준으로 새 데이터만 수집
if only_new and last_crawl_time:
    if item_updated_at < last_crawl_time:
        break  # 크롤링 중단
```

## 🧪 테스트 가능성

### 1. 의존성 주입

```python
class BaseCrawler:
    def __init__(self, crawl_options: dict = None):
        self.crawl_options = crawl_options or {}
        # 옵션을 통해 테스트용 설정 주입 가능
```

### 2. 모의 객체 지원

```python
# 테스트에서 HTTP 요청을 모의할 수 있도록 설계
class LawtalkCrawler:
    def __init__(self, session=None):
        self.session = session or requests.Session()
```

## 📝 로깅 및 모니터링

### 1. 구조화된 로깅

```python
# 각 크롤러별 로거
logger = logging.getLogger(self.__class__.__name__)

# 구조화된 로그 메시지
logger.info(f"Starting crawling for {site_name}")
logger.error(f"Crawling failed for {site_name}: {error}")
```

### 2. 진행 상황 추적

```python
# 크롤링 진행 상황 로그
logger.info(f"Processed {count}/{total} items")
logger.info(f"Saved {files} files, {total_size} bytes")
```

이 아키텍처는 확장성, 유지보수성, 테스트 가능성을 모두 고려하여 설계되었으며, 새로운 요구사항에 유연하게 대응할 수 있습니다. 