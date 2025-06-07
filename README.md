# DDOBAK RAG Source Collector

Python과 Poetry를 기반으로 한 다중 사이트 웹 크롤링 프로젝트입니다. 클린 코드와 클린 아키텍처 원칙을 따라 각 사이트별로 모듈화된 크롤러를 구현합니다.

## 📋 프로젝트 개요

이 프로젝트는 RAG(Retrieval-Augmented Generation) 시스템을 위한 소스 데이터를 수집하는 크롤러입니다. 현재 로톡(Lawtalk) 사이트의 법률 상담 데이터를 수집하며, 확장 가능한 아키텍처로 설계되어 다른 사이트의 크롤러도 쉽게 추가할 수 있습니다.

### 주요 특징

- **모듈화된 아키텍처**: 각 사이트별 독립적인 크롤러 모듈
- **Poetry Entry Points**: 플러그인 시스템으로 크롤러 자동 등록
- **유연한 저장소**: 로컬 파일 시스템 또는 AWS S3 저장 지원
- **증분 크롤링**: 새로운 데이터만 선택적으로 수집 가능
- **클린 아키텍처**: 관심사 분리와 높은 재사용성

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd DDOBAK-RAG-Source-Collector

# Poetry 설치 (없는 경우)
curl -sSL https://install.python-poetry.org | python3 -

# 의존성 설치
poetry install

# 환경변수 설정
cp .env.example .env
# .env 파일을 편집하여 필요한 설정값들을 입력
```

### 2. 기본 실행

```bash
# 로톡 크롤링 (기본 설정)
poetry run start lawtalk

# 상세 옵션 지정
poetry run start lawtalk detail s3 new
```

### 3. 테스트 실행

```bash
# 전체 테스트
poetry run pytest

# 특정 모듈 테스트
poetry run test-lawtalk
```

## 📖 상세 문서

- **[아키텍처 가이드](docs/architecture.md)** - 프로젝트 구조와 설계 원칙
- **[데이터 구조 설명](docs/data-structure.md)** - 수집되는 데이터의 구조와 형식
- **[크롤러 개발 가이드](docs/crawler-guide.md)** - 새로운 크롤러 개발 방법

## 🏗️ 프로젝트 구조

```
DDOBAK-RAG-Source-Collector/
├── main.py                    # CLI 진입점
├── config.py                  # 전역 설정
├── common/                    # 공통 모듈
│   ├── base_crawler.py        # 크롤러 베이스 클래스
│   └── crawler_registry.py    # 크롤러 관리
├── lawtalk/                   # 로톡 크롤러
│   ├── lawtalk_crawler.py     # 메인 크롤러
│   ├── lawtalk_config.py      # 로톡 설정
│   └── cases/                 # 데이터 타입별 크롤링
├── utils/                     # 유틸리티 함수들
├── data/                      # 크롤링된 데이터
├── logs/                      # 로그 파일
└── docs/                      # 프로젝트 문서
```

## 💾 데이터 수집 현황

### 로톡 (Lawtalk) 데이터

- **상담 사례 (Consultation Cases)**: 법률 질문과 변호사 답변
- **해결된 사례 (Solved Cases)**: 카테고리별 해결 사례
- **가이드 포스트 (Guide Posts)**: 법률 가이드 및 정보

각 데이터 타입의 상세 구조는 [데이터 구조 문서](docs/data-structure.md)를 참고하세요.

## ⚙️ 설정 옵션

### CLI 인자

| 인자 | 설명 | 옵션 |
|------|------|------|
| `site` | 크롤링할 사이트 | `lawtalk` |
| `simple_result` | 결과 타입 | `simple`, `detail` |
| `storage_type` | 저장 위치 | `local`, `s3` |
| `only_new` | 데이터 범위 | `new`, `all` |

### 환경변수

주요 환경변수들:

```bash
# 로톡 로그인 정보
LAWTALK_ID=your_email
LAWTALK_PW=your_password

# AWS S3 설정 (S3 사용시)
AWS_PROFILE=your_profile
AWS_REGION=ap-northeast-2
AWS_S3_BUCKET=your_bucket

# 로깅 설정
LOG_LEVEL=INFO
```

## 🔧 개발 환경

### 요구사항

- Python 3.11+
- Poetry
- AWS CLI (S3 사용시)