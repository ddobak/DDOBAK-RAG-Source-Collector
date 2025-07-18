# DDOBAK RAG Source Collector

RAG를 위한 데이터 수집기입니다.
Poetry 기반의 Python으로 개발되었습니다.
수집한 데이터는 txt 형식의 파일로 AWS S3에 적재됩니다.

## 수집 대상


- [생활법령 100문 100답](https://www.easylaw.go.kr/CSP/OnhunqueansLstRetrieve.laf)
- [국가법령정보 OPEN API](https://open.law.go.kr/LSO/main.do)
  - "근로", "노동", "계약", "임대차", "전세", "월세"와 관련된 판례 데이터 수집
