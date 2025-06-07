# 데이터 구조 설명

DDOBAK RAG Source Collector에서 수집하는 데이터의 구조와 형식에 대한 상세한 설명입니다.

## 📊 데이터 개요

### 로톡 (Lawtalk) 데이터 구조

로톡에서 수집하는 데이터는 크게 3가지 유형으로 구분됩니다:

1. **상담 사례 (Consultation Cases)**: 법률 질문과 변호사 답변
2. **해결된 사례 (Solved Cases)**: 카테고리별 해결 사례  
3. **가이드 포스트 (Guide Posts)**: 법률 가이드 및 정보

## 🗂️ 파일 구조

### 디렉터리 구조

```
data/lawtalk/
├── consultation_case/          # 상담 사례
│   └── MMDD/                  # 날짜별 폴더 (예: 0608)
│       ├── 0.json             # 첫 번째 배치
│       ├── 1.json             # 두 번째 배치
│       └── ...
├── solved_cases/              # 해결 사례
│   └── [카테고리명]/          # 카테고리별 폴더
│       └── MMDD/              # 날짜별 폴더
│           ├── 0.json
│           └── ...
└── guide_posts/               # 법률 가이드 포스트
    └── [카테고리명]/          # 카테고리별 폴더
        └── MMDD/              # 날짜별 폴더
            ├── 0.json
            └── ...
```

### 파일명 규칙

- **날짜 폴더**: `MMDD` 형식 (예: `0608` = 6월 8일)
- **데이터 파일**: `{순번}.json` 형식 (예: `0.json`, `1.json`)
- **중복 방지**: 같은 이름의 파일이 있으면 `{순번}_{카운터}.json` 형식

## 📄 데이터 스키마

### 1. 상담 사례 (Consultation Cases)

#### 파일 구조 예시
```json
{
  "success": true,
  "total_fetched": 10,
  "offset": 0,
  "simple_result": true,
  "data": {
    "questions": [
      {
        "_id": "68445cadefc154ba2a238a0e",
        "user": "658479771c9755a225511cb5",
        "categories": [
          {
            "_id": "62a9f8bb9fcafe948d73e9ee",
            "name": "폭행/협박/상해 일반",
            "description": "폭행, 협박, 상해, 감금, 유기, 학대, 과실치사상, 공무집행방해 등",
            "sort": 1,
            "createdAt": "2022-06-15T15:20:27.526Z",
            "updatedAt": "2022-06-15T15:20:27.526Z",
            "__v": 0
          }
        ],
        "titleOrigin": "이런 경우 특수폭행 재물손괴 가능한가요?",
        "bodyOrigin": "상세한 질문 내용...",
        "title": "특수폭행과 재물손괴 사건 대처 방법",
        "body": "정제된 질문 내용...",
        "slugs": ["523482-이런-경우-특수폭행-재물손괴-가능한가요"],
        "meta": {
          "keywords": ["특수폭행", "재물손괴", "사건 대처"]
        },
        "createdAt": "2025-06-07T15:37:17.876Z",
        "updatedAt": "2025-06-07T17:41:52.631Z",
        "answers": [
          {
            "_id": "68445f91054004aa0ce28a86",
            "lawyer": "6424e5628fa48c59aadd8905",
            "role": "lawyer",
            "body": [
              {
                "_id": "68445f92054004aa0ce28a96",
                "answer": "68445f91054004aa0ce28a86",
                "body": "변호사 답변 내용...",
                "createdAt": "2025-06-07T15:49:38.830Z",
                "updatedAt": "2025-06-07T15:49:38.830Z",
                "number": 2926531
              }
            ]
          }
        ]
      }
    ]
  }
}
```

#### 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `success` | boolean | 크롤링 성공 여부 |
| `total_fetched` | number | 수집된 질문 수 |
| `offset` | number | 페이지네이션 오프셋 |
| `simple_result` | boolean | 간소화된 결과 여부 |
| `data.questions` | array | 질문 목록 |

#### Question 객체

| 필드 | 타입 | 설명 |
|------|------|------|
| `_id` | string | 질문 고유 ID |
| `user` | string | 질문자 ID |
| `categories` | array | 법률 카테고리 목록 |
| `titleOrigin` | string | 원본 제목 |
| `bodyOrigin` | string | 원본 내용 |
| `title` | string | 정제된 제목 |
| `body` | string | 정제된 내용 |
| `slugs` | array | URL 슬러그 목록 |
| `meta.keywords` | array | 키워드 목록 |
| `createdAt` | string | 생성 시간 (ISO 8601) |
| `updatedAt` | string | 수정 시간 (ISO 8601) |
| `answers` | array | 답변 목록 |

#### Answer 객체

| 필드 | 타입 | 설명 |
|------|------|------|
| `_id` | string | 답변 고유 ID |
| `lawyer` | string | 변호사 ID |
| `role` | string | 역할 ("lawyer") |
| `body` | array | 답변 내용 배열 |

### 2. 해결된 사례 (Solved Cases)

#### 파일 구조 예시
```json
{
  "success": true,
  "total_fetched": 10,
  "category": "재산범죄",
  "category_id": "62a9f8bb9fcafe948d73e9e9",
  "offset": 0,
  "simple_result": true,
  "data": {
    "posts": [
      {
        "_id": "65f2b4b83e4656f1bdde8ffc",
        "title": "부동산 사기 사건 해결 사례",
        "titleOrigin": "부동산 사기 사건 해결 사례",
        "type": "guide",
        "isPublished": true,
        "createdAt": "2024-03-14T09:30:00.000Z",
        "updatedAt": "2024-03-14T09:30:00.000Z",
        "htmlContent": "<p>해결 사례 HTML 내용...</p>",
        "textContent": "해결 사례 텍스트 내용...",
        "lawyer": {
          "_id": "62cf5914c4a922080dd7655c",
          "name": "김변호사",
          "role": "lawyer"
        },
        "categories": [
          {
            "_id": "62a9f8bb9fcafe948d73e9e9",
            "name": "재산범죄"
          }
        ],
        "keywords": ["부동산", "사기", "해결사례"]
      }
    ]
  }
}
```

#### 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `category` | string | 카테고리 이름 |
| `category_id` | string | 카테고리 ID |
| `data.posts` | array | 포스트 목록 |

#### Post 객체

| 필드 | 타입 | 설명 |
|------|------|------|
| `_id` | string | 포스트 고유 ID |
| `title` | string | 제목 |
| `titleOrigin` | string | 원본 제목 |
| `type` | string | 포스트 타입 |
| `isPublished` | boolean | 게시 여부 |
| `htmlContent` | string | HTML 형식 내용 |
| `textContent` | string | 텍스트 형식 내용 |
| `lawyer` | object | 작성 변호사 정보 |
| `categories` | array | 카테고리 목록 |
| `keywords` | array | 키워드 목록 |

### 3. 가이드 포스트 (Guide Posts)

가이드 포스트는 해결된 사례와 동일한 구조를 가지지만, 내용이 가이드 및 정보성 포스트입니다.

## 🔄 데이터 처리 옵션

### Simple Result vs Detail Result

#### Simple Result (`simple_result: true`)
- 핵심 필드만 포함
- 파일 크기 최소화
- 빠른 처리 속도

#### Detail Result (`simple_result: false`)
- 모든 필드 포함
- 완전한 데이터 보존
- 상세 분석 가능

### 예시 비교

**Simple Result**:
```json
{
  "_id": "68445cadefc154ba2a238a0e",
  "title": "특수폭행과 재물손괴 사건 대처 방법",
  "body": "질문 내용...",
  "categories": [...],
  "createdAt": "2025-06-07T15:37:17.876Z",
  "answers": [...]
}
```

**Detail Result**:
```json
{
  "_id": "68445cadefc154ba2a238a0e",
  "title": "특수폭행과 재물손괴 사건 대처 방법",
  "body": "질문 내용...",
  "categories": [...],
  "createdAt": "2025-06-07T15:37:17.876Z",
  "answers": [...],
  "views": 1250,
  "likes": 15,
  "bookmarks": 8,
  "relatedQuestions": [...],
  "tags": [...],
  "metadata": {...}
}
```

## 📈 데이터 통계

### 메타데이터 필드

각 JSON 파일에는 다음과 같은 메타데이터가 포함됩니다:

```json
{
  "success": true,
  "total_fetched": 10,
  "offset": 0,
  "simple_result": true,
  "storage_type": "local",
  "crawl_timestamp": "2025-06-07T15:37:17.876Z"
}
```

### 카테고리 목록

#### 상담 사례 카테고리
- 폭행/협박/상해 일반
- 성폭력/강제추행 등
- 미성년 대상 성범죄
- 디지털 성범죄
- 사기/공갈
- 재산범죄
- 마약/도박
- 형사일반/기타범죄

#### 해결된 사례 & 가이드 포스트 카테고리
- 재산범죄
- IT/지식재산/금융
- 금전/계약 문제
- 형사/수사/재판
- 가족/상속/이혼
- 부동산/임대차
- 교통사고/보험
- 노동/고용/산재
- 생활법률 일반

## 🔍 데이터 활용 예시

### 1. RAG 시스템 입력 데이터

```python
# 질문-답변 쌍 추출
for question in data['data']['questions']:
    context = {
        'question': question['body'],
        'category': question['categories'][0]['name'],
        'answers': [answer['body'][0]['body'] for answer in question['answers']]
    }
```

### 2. 키워드 기반 검색

```python
# 키워드로 관련 사례 검색
keywords = question['meta']['keywords']
relevant_cases = search_by_keywords(keywords)
```

### 3. 카테고리별 분석

```python
# 카테고리별 통계
category_stats = {}
for question in questions:
    category = question['categories'][0]['name']
    category_stats[category] = category_stats.get(category, 0) + 1
```