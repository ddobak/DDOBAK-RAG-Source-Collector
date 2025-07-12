"""
법무부 오픈API 크롤러 (HTML 기반)
판례 정보를 HTML 형태로 수집하는 크롤러입니다.
"""

import json
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
from bs4 import BeautifulSoup

from common.base_crawler import BaseCrawler
from .law_open_api_config import LAW_OPEN_API_CONFIG, DATA_STRUCTURE


class LawOpenApiCrawler(BaseCrawler):
    """
    법무부 오픈API 크롤러 (HTML 기반)
    
    판례 정보를 HTML 형태로 수집하여 JSON 형태로 저장합니다.
    """
    
    def __init__(self, crawl_options: Optional[Dict[str, Any]] = None) -> None:
        """크롤러 초기화"""
        super().__init__(crawl_options)
        self.config = LAW_OPEN_API_CONFIG
        self.session = requests.Session()
        self.session.headers.update(self.config["headers"])
        
        # 세션 쿠키 미리 설정
        self._setup_session_cookies()
        
        # 데이터 저장 디렉토리 생성
        self.precedent_dir = self.output_dir / "precedent"
        self.precedent_dir.mkdir(exist_ok=True)
        
        # 법령 데이터 저장 디렉토리 생성 (테스트 호환성)
        self.law_dir = self.output_dir / "law"
        self.law_dir.mkdir(exist_ok=True)
        
        self.logger.info("Law Open API crawler (HTML-based) initialized")
    
    def get_site_name(self) -> str:
        """사이트 이름 반환"""
        return "law_open_api"
    
    def crawl(self) -> None:
        """크롤링 실행"""
        self.logger.info("Starting Law Open API crawling (HTML-based)")
        
        # 각 키워드별로 판례 검색
        for keyword in self.config["search_keywords"]:
            self.logger.info(f"Crawling precedent data for keyword: {keyword}")
            
            # 판례 목록 검색
            precedent_list = self._search_precedent_list(keyword)
            if precedent_list:
                # 판례 본문 조회 및 저장
                precedent_data = self._fetch_precedent_details(precedent_list, keyword)
                if precedent_data:
                    self._save_precedent_data_individually(keyword, precedent_data)
            
            # 요청 간격 준수
            time.sleep(self.config["request_delay"])
        
        self.logger.info("Law Open API crawling completed")
    
    def _search_precedent_list(self, keyword: str) -> List[Dict[str, Any]]:
        """판례 목록 검색 (HTML 파싱)"""
        self.logger.info(f"Searching precedent list for keyword: {keyword}")
        
        all_data = []
        
        for page in range(1, self.config["max_pages"] + 1):
            params = self.config["precedent_search_params"].copy()
            params.update({
                "query": keyword,
                "page": str(page)
            })
            
            try:
                response = self.session.get(
                    self.config["precedent_search_url"],
                    params=params,
                    timeout=self.config["timeout"]
                )
                response.raise_for_status()
                
                # HTML 응답 파싱
                data = self._parse_precedent_list_html(response.text, keyword)
                if not data:
                    break
                
                all_data.extend(data)
                self.logger.info(f"Page {page}: Found {len(data)} precedent records")
                
                # 요청 간격 준수
                time.sleep(self.config["request_delay"])
                
            except requests.RequestException as e:
                self.logger.error(f"Error fetching precedent list for {keyword}, page {page}: {e}")
                break
            except Exception as e:
                self.logger.error(f"Error parsing precedent list for {keyword}, page {page}: {e}")
                break
        
        self.logger.info(f"Total precedent records found for '{keyword}': {len(all_data)}")
        return all_data
    
    def _parse_precedent_list_html(self, html_content: str, keyword: str) -> List[Dict[str, Any]]:
        """판례 목록 HTML 파싱"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 테이블에서 데이터 추출
            table = soup.find('table', class_='tbl8')
            if not table:
                self.logger.warning("No table found in HTML response")
                return []
            
            tbody = table.find('tbody')
            if not tbody:
                self.logger.warning("No tbody found in table")
                return []
            
            rows = tbody.find_all('tr')
            parsed_data = []
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) < 6:
                    continue
                
                # 링크에서 판례 ID 추출
                link = cells[1].find('a')
                if not link:
                    continue
                
                href = link.get('href', '')
                prec_id = self._extract_prec_id_from_url(href)
                if not prec_id:
                    continue
                
                # 사건명 추출 (HTML 태그 제거)
                case_name = self._clean_text(cells[1].get_text(strip=True))
                
                # 법원명 추출
                court_name = self._clean_text(cells[2].get_text(strip=True))
                
                # 사건종류명 추출
                case_type_name = self._clean_text(cells[3].get_text(strip=True))
                
                # 판결유형 추출
                judgment_type = self._clean_text(cells[4].get_text(strip=True))
                
                # 선고일자 추출
                judgment_date = self._clean_text(cells[5].get_text(strip=True))
                
                data = {
                    "prec_id": prec_id,
                    "case_name": case_name,
                    "court_name": court_name,
                    "case_type_name": case_type_name,
                    "judgment_type": judgment_type,
                    "judgment_date": judgment_date,
                    "detail_link": href,
                    "keywords": keyword,
                    "crawl_date": datetime.now().isoformat()
                }
                
                parsed_data.append(data)
            
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"Error parsing precedent list HTML: {e}")
            return []
    
    def _extract_prec_id_from_url(self, url: str) -> str:
        """URL에서 판례 ID 추출"""
        try:
            # ID=숫자 패턴 찾기
            match = re.search(r'ID=(\d+)', url)
            if match:
                return match.group(1)
            return ""
        except Exception:
            return ""
    
    def _clean_text(self, text: str) -> str:
        """텍스트 정리 (공백 제거, 특수문자 정리)"""
        if not text:
            return ""
        
        # 여러 공백을 하나로 변환
        text = re.sub(r'\s+', ' ', text)
        # 앞뒤 공백 제거
        text = text.strip()
        # 점 제거 (날짜 끝의 점)
        text = text.rstrip('.')
        
        return text
    
    def _fetch_precedent_details(self, precedent_list: List[Dict[str, Any]], keyword: str) -> List[Dict[str, Any]]:
        """판례 본문 조회 (HTML 파싱)"""
        if not self.config["fetch_detail"]:
            # 본문 조회를 하지 않더라도 RAG 최적화는 적용
            return [self._optimize_for_bedrock_rag(precedent) for precedent in precedent_list]
        
        self.logger.info(f"Fetching details for {len(precedent_list)} precedents")
        detailed_data = []
        
        for i, precedent in enumerate(precedent_list):
            if "prec_id" not in precedent:
                self.logger.warning(f"No prec_id found for precedent {i}")
                detailed_data.append(precedent)
                continue
            
            try:
                params = self.config["precedent_detail_params"].copy()
                params.update({
                    "ID": precedent["prec_id"],
                    "LM": precedent.get("case_name", "")
                })
                
                response = self.session.get(
                    self.config["precedent_detail_url"],
                    params=params,
                    timeout=self.config["timeout"]
                )
                response.raise_for_status()
                
                # HTML 응답이 iframe 방식인 경우 실제 데이터 URL 추출
                detail_data = self._parse_precedent_detail_html(response.text, precedent["prec_id"])
                
                if detail_data and any(detail_data.values()):  # 실제 내용이 있는지 확인
                    # 기존 목록 데이터와 본문 데이터 병합
                    merged_data = {**precedent, **detail_data}
                    # AWS Bedrock RAG 최적화 필드 추가
                    rag_optimized_data = self._optimize_for_bedrock_rag(merged_data)
                    detailed_data.append(rag_optimized_data)
                    self.logger.debug(f"Successfully fetched detail for prec_id {precedent.get('prec_id')}")
                else:
                    # 본문이 없는 경우에도 RAG 최적화 적용
                    rag_optimized_data = self._optimize_for_bedrock_rag(precedent)
                    detailed_data.append(rag_optimized_data)
                    self.logger.warning(f"No detail content available for prec_id {precedent.get('prec_id')}")
                
                # 요청 간격 준수
                time.sleep(self.config["request_delay"])
                
                if (i + 1) % 10 == 0:
                    self.logger.info(f"Fetched details for {i + 1}/{len(precedent_list)} precedents")
                    
            except requests.RequestException as e:
                self.logger.error(f"Error fetching detail for precedent {precedent.get('prec_id')}: {e}")
                rag_optimized_data = self._optimize_for_bedrock_rag(precedent)
                detailed_data.append(rag_optimized_data)
            except Exception as e:
                self.logger.error(f"Error parsing detail for precedent {precedent.get('prec_id')}: {e}")
                rag_optimized_data = self._optimize_for_bedrock_rag(precedent)
                detailed_data.append(rag_optimized_data)
        
        self.logger.info(f"Successfully fetched details for {len(detailed_data)} precedents")
        return detailed_data
    
    def _parse_precedent_detail_html(self, html_content: str, prec_id: str) -> Dict[str, Any]:
        """판례 본문 HTML 파싱"""
        try:
            # 1순위: 직접 precInfoP.do URL로 접근 시도
            direct_result = self._try_direct_prec_info_access(prec_id)
            if direct_result and any(direct_result.values()):
                self.logger.debug(f"Successfully fetched content via direct precInfoP.do for prec_id {prec_id}")
                return direct_result
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # iframe 방식인지 확인
            iframe = soup.find('iframe')
            if iframe:
                # iframe src에서 실제 데이터 URL 추출
                src = iframe.get('src', '')
                if src:
                    # 실제 데이터 URL 호출
                    if src.startswith('/'):
                        src = f"http://www.law.go.kr{src}"
                    
                    try:
                        # 먼저 HTTPS로 직접 접근 시도 (605281 같은 케이스)
                        https_url = src.replace('http://', 'https://')
                        
                        # HTTPS로 직접 접근 시도
                        self.logger.debug(f"Trying HTTPS direct access: {https_url}")
                        https_response = self.session.get(https_url, timeout=self.config["timeout"])
                        
                        # 응답이 유효한지 확인 (내용이 있고 에러가 아닌 경우)
                        if https_response.status_code == 200 and len(https_response.text) > 1000:
                            # 판례 내용이 실제로 포함되어 있는지 확인
                            if any(keyword in https_response.text for keyword in ['판시사항', '판결요지', '주문', '이유']):
                                self.logger.debug(f"Successfully fetched content via HTTPS for prec_id {prec_id}")
                                return self._parse_law_center_html(https_response.text)
                        
                        # HTTPS 직접 접근이 실패한 경우, 기존 리다이렉트 방식 시도
                        self.logger.debug(f"HTTPS direct access failed, trying redirect method for prec_id {prec_id}")
                        
                        # 1단계: HTTP 리다이렉트 URL 얻기 (allow_redirects=False)
                        response = self.session.get(src, timeout=self.config["timeout"], allow_redirects=False)
                        
                        # 리다이렉트 응답인지 확인
                        if response.status_code in [301, 302, 303, 307, 308]:
                            redirect_url = response.headers.get('Location')
                            if redirect_url:
                                self.logger.debug(f"First redirect to: {redirect_url}")
                                
                                # 2단계: HTTPS 리다이렉트 URL 얻기 (allow_redirects=False)
                                https_response = self.session.get(redirect_url, timeout=self.config["timeout"], allow_redirects=False)
                                
                                if https_response.status_code in [301, 302, 303, 307, 308]:
                                    final_redirect_url = https_response.headers.get('Location')
                                    if final_redirect_url:
                                        self.logger.debug(f"Final redirect to: {final_redirect_url}")
                                        
                                        # 3단계: 최종 리다이렉트 URL에서 ntstDcmId 추출
                                        ntstDcmId = self._extract_ntstdcmid_from_url(final_redirect_url)
                                        if ntstDcmId:
                                            # 4단계: AJAX 요청으로 실제 판례 데이터 가져오기
                                            return self._fetch_precedent_data_via_ajax(ntstDcmId)
                                        else:
                                            self.logger.warning(f"Could not extract ntstDcmId from final redirect URL: {final_redirect_url}")
                                            return {}
                                elif https_response.status_code == 404:
                                    # 404 에러인 경우 빈 데이터 반환
                                    self.logger.warning(f"404 Not Found for prec_id {prec_id}")
                                    return {}
                                elif https_response.status_code == 200:
                                    # 200 OK인 경우 직접 HTML 파싱 (법령정보센터 페이지)
                                    return self._parse_law_center_html(https_response.text)
                                else:
                                    # HTTPS 리다이렉트가 없으면 첫 번째 리다이렉트 URL에서 ntstDcmId 추출 시도
                                    ntstDcmId = self._extract_ntstdcmid_from_url(redirect_url)
                                    if ntstDcmId:
                                        return self._fetch_precedent_data_via_ajax(ntstDcmId)
                                    else:
                                        # 리다이렉트된 페이지에서 직접 HTML 파싱 (법령정보센터 페이지)
                                        return self._parse_law_center_html(https_response.text)
                        else:
                            # 리다이렉트가 없으면 원본 응답 사용
                            return self._parse_actual_precedent_content(response.text)
                            
                    except Exception as e:
                        self.logger.error(f"Error fetching iframe content for prec_id {prec_id}: {e}")
                        return {}
            
            # 직접 HTML에서 데이터 추출 시도
            return self._parse_actual_precedent_content(html_content)
            
        except Exception as e:
            self.logger.error(f"Error parsing precedent detail HTML for prec_id {prec_id}: {e}")
            return {}
    
    def _try_direct_prec_info_access(self, prec_id: str) -> Dict[str, Any]:
        """직접 precInfoP.do URL로 접근 시도"""
        try:
            # precInfoP.do URL로 직접 접근
            direct_url = f"https://www.law.go.kr/LSW/precInfoP.do?mode=0&precSeq={prec_id}"
            
            # 적절한 헤더 설정 (브라우저와 유사하게)
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'max-age=0',
                'Connection': 'keep-alive',
                'Host': 'www.law.go.kr',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"'
            }
            
            self.logger.debug(f"Trying direct precInfoP.do access: {direct_url}")
            response = self.session.get(direct_url, headers=headers, timeout=self.config["timeout"], allow_redirects=True)
            
            # 리다이렉트된 경우 taxlaw.nts.go.kr로 이동했는지 확인
            if response.url and 'taxlaw.nts.go.kr' in response.url:
                self.logger.debug(f"Redirected to taxlaw.nts.go.kr: {response.url}")
                # ntstDcmId 추출
                import re
                match = re.search(r'ntstDcmId=([^&]+)', response.url)
                if match:
                    ntstDcmId = match.group(1)
                    self.logger.debug(f"Extracted ntstDcmId: {ntstDcmId}")
                    # AJAX 요청으로 실제 데이터 가져오기
                    return self._fetch_precedent_data_via_ajax(ntstDcmId)
            
            if response.status_code == 200 and len(response.text) > 1000:
                # 판례 내용이 실제로 포함되어 있는지 확인
                if any(keyword in response.text for keyword in ['판시사항', '판결요지', '주문', '이유', '사건명', '법원명']):
                    self.logger.debug(f"Direct precInfoP.do access successful for prec_id {prec_id}")
                    return self._parse_prec_info_html(response.text)
                else:
                    self.logger.debug(f"Direct precInfoP.do access returned page without judgment content for prec_id {prec_id}")
            elif response.status_code == 404:
                self.logger.warning(f"Precedent not found (404) for prec_id {prec_id} - may be deleted or private")
            else:
                self.logger.debug(f"Direct precInfoP.do access failed: status={response.status_code}, length={len(response.text) if response.text else 0}")
            
            return {}
            
        except Exception as e:
            self.logger.debug(f"Error in direct precInfoP.do access for prec_id {prec_id}: {e}")
            return {}
    
    def _parse_prec_info_html(self, html_content: str) -> Dict[str, Any]:
        """precInfoP.do 페이지에서 판례 내용 파싱"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            data = {}
            
            # 사건명 추출 (h2 태그 또는 title에서)
            h2_tags = soup.find_all('h2')
            for h2 in h2_tags:
                h2_text = h2.get_text(strip=True)
                if h2_text and ('·' in h2_text or len(h2_text) > 10):
                    data['case_name'] = h2_text
                    break
            
            # title에서 사건명 추출 (h2가 없는 경우)
            if not data.get('case_name'):
                title = soup.find('title')
                if title:
                    title_text = title.get_text()
                    if '|' in title_text:
                        case_name = title_text.split('|')[0].strip()
                        data['case_name'] = case_name
            
            # 기본 정보 추출 (테이블 또는 div에서)
            # 사건번호, 법원명, 선고일자 등을 추출
            text_content = soup.get_text()
            
            # 사건번호 패턴 찾기 (여러 패턴 시도)
            case_number_patterns = [
                r'(\d{4}[가-힣]+\d+(?:,\s*\d+)*)',  # 2021다245528, 245535
                r'([가-힣]+법원[^-]*-\d{4}-[가-힣]+-\d+)',  # 서울중앙지방법원-2021-가합-12345
                r'사건번호[:\s]*([^\n\r]+)',  # 사건번호: 내용
            ]
            
            for pattern in case_number_patterns:
                match = re.search(pattern, text_content)
                if match:
                    data['case_number'] = match.group(1).strip()
                    break
            
            # 법원명 패턴 찾기
            court_patterns = [
                r'([가-힣]+법원)',  # 대법원, 서울중앙지방법원 등
                r'법원명[:\s]*([^\n\r]+)',  # 법원명: 내용
            ]
            
            for pattern in court_patterns:
                match = re.search(pattern, text_content)
                if match:
                    court_name = match.group(1).strip()
                    if '법원' in court_name:
                        data['court_name'] = court_name
                        break
            
            # 선고일자 패턴 찾기
            date_patterns = [
                r'(\d{4}\.\s*\d{1,2}\.\s*\d{1,2})',  # 2023. 12. 01
                r'선고일[:\s]*([^\n\r]+)',  # 선고일: 내용
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text_content)
                if match:
                    date_text = match.group(1).strip()
                    if re.match(r'\d{4}\.\s*\d{1,2}\.\s*\d{1,2}', date_text):
                        data['judgment_date'] = date_text.replace(' ', '')
                        break
            
            # 전체 텍스트 내용 저장
            cleaned_text = self._clean_text(text_content)
            if len(cleaned_text) > 500:  # 충분히 긴 텍스트만
                data['case_content'] = cleaned_text
                data['full_judgment_text'] = cleaned_text
                
                # 판결문 섹션 추출
                sections = self._extract_judgment_sections(cleaned_text)
                if sections:
                    data.update(sections)
            
            # 데이터가 비어있는 경우 로그 출력
            if not data or not any(data.values()):
                self.logger.warning("No meaningful content extracted from precInfoP.do HTML")
                return {}
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error parsing precInfoP.do HTML: {e}")
            return {}

    def _setup_session_cookies(self) -> None:
        """세션 쿠키 설정 (필요시)"""
        try:
            # 메인 페이지에 접근해서 세션 쿠키 생성
            main_page_response = self.session.get("https://www.law.go.kr/", timeout=self.config["timeout"])
            if main_page_response.status_code == 200:
                self.logger.debug("Session cookies set up successfully")
            else:
                self.logger.warning(f"Failed to set up session cookies: {main_page_response.status_code}")
        except Exception as e:
            self.logger.warning(f"Error setting up session cookies: {e}")
    
    def _extract_ntstdcmid_from_url(self, url: str) -> str:
        """리다이렉트 URL에서 ntstDcmId 추출"""
        try:
            # ntstDcmId=값 패턴 찾기
            match = re.search(r'ntstDcmId=([^&]+)', url)
            if match:
                return match.group(1)
            return ""
        except Exception:
            return ""
    
    def _fetch_precedent_data_via_ajax(self, ntstDcmId: str) -> Dict[str, Any]:
        """AJAX 요청을 통해 실제 판례 데이터 가져오기"""
        try:
            # 국세법령정보시스템 AJAX 요청
            ajax_url = "https://taxlaw.nts.go.kr/action.do"
            
            # 요청 데이터 준비
            form_data = {
                'actionId': 'ASIQTB002PR01',
                'paramData': f'{{"dcmDVO":{{"ntstDcmId":"{ntstDcmId}"}}}}'
            }
            
            # 요청 헤더 설정
            headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f'https://taxlaw.nts.go.kr/qt/USEQTA002P.do?ntstDcmId={ntstDcmId}'
            }
            
            # AJAX 요청 실행
            response = self.session.post(
                ajax_url,
                data=form_data,
                headers=headers,
                timeout=self.config["timeout"]
            )
            response.raise_for_status()
            
            # JSON 응답 파싱
            json_data = response.json()
            
            if json_data.get('status') == 'SUCCESS':
                return self._parse_ajax_response(json_data)
            else:
                self.logger.warning(f"AJAX request failed for ntstDcmId {ntstDcmId}: {json_data}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error fetching precedent data via AJAX for ntstDcmId {ntstDcmId}: {e}")
            return {}
    
    def _parse_ajax_response(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """AJAX 응답 JSON 파싱"""
        try:
            data = {}
            
            # 메인 데이터 추출
            main_data = json_data.get('data', {}).get('ASIQTB002PR01', {})
            dcm_data = main_data.get('dcmDVO', {})
            
            if dcm_data:
                # 기본 정보
                data['case_number'] = dcm_data.get('ntstDcmDscmCntn', '')
                data['case_name'] = dcm_data.get('ntstDcmTtl', '')
                data['judgment_date'] = dcm_data.get('ntstDcmRgtDt', '')
                data['judgment_summary'] = dcm_data.get('ntstDcmGistCntn', '')
                data['case_content'] = dcm_data.get('ntstDcmCntn', '')
                data['reply_content'] = dcm_data.get('ntstDcmRplyCntn', '')
                
                # 추가 정보
                data['document_class'] = dcm_data.get('ntstDcmClCd', '')
                data['source_org'] = dcm_data.get('ntstDcmSrcsOrgnClCd', '')
                data['year'] = dcm_data.get('attrYr', '')
            
            # HTML 내용 추출 (실제 판결문) - dcmFleByte 필드에서 추출
            hwp_editor_list = main_data.get('dcmHwpEditorDVOList', [])
            for hwp_data in hwp_editor_list:
                if hwp_data.get('dcmFleTy') == 'html':
                    html_content = hwp_data.get('dcmFleByte', '')
                    if html_content:
                        # HTML에서 실제 판결문 내용 추출
                        parsed_html = self._parse_html_judgment_content(html_content)
                        data.update(parsed_html)
                        
                        # dcmFleByte의 HTML 내용을 주요 판례 내용으로 사용
                        if parsed_html.get('full_judgment_text'):
                            data['case_content'] = parsed_html['full_judgment_text']
                        break
            
            # 판례 내용이 없는 경우 기본 내용 사용
            if not data.get('case_content') and dcm_data.get('ntstDcmCntn'):
                data['case_content'] = dcm_data.get('ntstDcmCntn', '')
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error parsing AJAX response: {e}")
            return {}
    
    def _parse_html_judgment_content(self, html_content: str) -> Dict[str, Any]:
        """HTML 판결문 내용 파싱"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            data = {}
            
            # HTML에서 전체 텍스트 추출
            full_text = soup.get_text()
            if full_text:
                cleaned_text = self._clean_text(full_text)
                data['full_judgment_text'] = cleaned_text
                
                # 판결문에서 주요 섹션 추출
                sections = self._extract_judgment_sections(cleaned_text)
                if sections:
                    data.update(sections)
            
            # 특정 섹션 추출 시도 (p 태그 기반)
            paragraphs = soup.find_all('p')
            sections = []
            for p in paragraphs:
                text = self._clean_text(p.get_text())
                if text and len(text) > 10:
                    sections.append(text)
            
            if sections:
                data['judgment_sections'] = sections
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error parsing HTML judgment content: {e}")
            return {}
    
    def _extract_judgment_sections(self, text: str) -> Dict[str, Any]:
        """판결문 텍스트에서 주요 섹션 추출"""
        try:
            sections = {}
            
            # 주문 섹션 추출
            if '주 문' in text or '주문' in text:
                match = re.search(r'주\s*문\s*(.+?)(?=청구취지|이\s*유|$)', text, re.DOTALL)
                if match:
                    sections['judgment_order'] = self._clean_text(match.group(1))
            
            # 청구취지 섹션 추출
            if '청구취지' in text:
                match = re.search(r'청구취지\s*(.+?)(?=이\s*유|항소취지|$)', text, re.DOTALL)
                if match:
                    sections['claim_purpose'] = self._clean_text(match.group(1))
            
            # 이유 섹션 추출
            if '이 유' in text or '이유' in text:
                match = re.search(r'이\s*유\s*(.+?)$', text, re.DOTALL)
                if match:
                    sections['reasoning'] = self._clean_text(match.group(1))
            
            # 판결요지나 판시사항이 있는 경우 추출
            if '판결요지' in text:
                match = re.search(r'판결요지\s*(.+?)(?=판시사항|참조조문|$)', text, re.DOTALL)
                if match:
                    sections['judgment_summary'] = self._clean_text(match.group(1))
            
            if '판시사항' in text:
                match = re.search(r'판시사항\s*(.+?)(?=판결요지|참조조문|$)', text, re.DOTALL)
                if match:
                    sections['judgment_point'] = self._clean_text(match.group(1))
            
            # 참조조문 추출
            if '참조조문' in text:
                match = re.search(r'참조조문\s*(.+?)(?=참조판례|$)', text, re.DOTALL)
                if match:
                    sections['reference_law'] = self._clean_text(match.group(1))
            
            # 참조판례 추출
            if '참조판례' in text:
                match = re.search(r'참조판례\s*(.+?)$', text, re.DOTALL)
                if match:
                    sections['reference_case'] = self._clean_text(match.group(1))
            
            return sections
            
        except Exception as e:
            self.logger.error(f"Error extracting judgment sections: {e}")
            return {}

    def _parse_law_center_html(self, html_content: str) -> Dict[str, Any]:
        """법령정보센터 페이지에서 직접 판례 내용 파싱"""
        try:
            # 빈 응답이나 너무 짧은 응답 체크
            if not html_content or len(html_content.strip()) < 100:
                self.logger.warning("Empty or too short HTML content received")
                return {}
            
            soup = BeautifulSoup(html_content, 'html.parser')
            data = {}
            
            # 제목에서 사건명 추출
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                if '|' in title_text:
                    case_name = title_text.split('|')[0].strip()
                    data['case_name'] = case_name
            
            # h2 태그에서 사건명 추출 (더 정확한 방법)
            h2_tags = soup.find_all('h2')
            for h2 in h2_tags:
                h2_text = h2.get_text(strip=True)
                if h2_text and '·' in h2_text:  # 사건명 패턴 (예: 근로자지위확인등·근로자지위확인등)
                    data['case_name'] = h2_text
                    break
            
            # 사건번호와 법원명 추출 (대괄호 안의 내용)
            bracket_pattern = re.search(r'\[([^\]]+)\]', html_content)
            if bracket_pattern:
                bracket_content = bracket_pattern.group(1)
                # 예: 대법원 2025. 3. 27. 선고 2021다245528, 245535 판결
                if '선고' in bracket_content:
                    parts = bracket_content.split('선고')
                    if len(parts) >= 2:
                        court_and_date = parts[0].strip()
                        case_number = parts[1].strip().replace('판결', '').strip()
                        
                        # 법원명과 선고일자 분리
                        court_date_match = re.search(r'([가-힣]+법원)\s+(\d{4}\.\s*\d{1,2}\.\s*\d{1,2})', court_and_date)
                        if court_date_match:
                            data['court_name'] = court_date_match.group(1)
                            data['judgment_date'] = court_date_match.group(2).replace(' ', '')
                        
                        data['case_number'] = case_number
            
            # 전체 텍스트 추출 - 간단하게 모든 내용을 case_content에 저장
            full_text = soup.get_text()
            if full_text:
                cleaned_text = self._clean_text(full_text)
                if len(cleaned_text) > 500:  # 충분히 긴 텍스트만
                    data['case_content'] = cleaned_text
                    data['full_judgment_text'] = cleaned_text
            
            # 데이터가 비어있는 경우 로그 출력
            if not data or not any(data.values()):
                self.logger.warning("No meaningful content extracted from law center HTML")
                return {}
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error parsing law center HTML: {e}")
            return {}

    def _parse_actual_precedent_content(self, html_content: str) -> Dict[str, Any]:
        """실제 판례 내용 파싱 (레거시 방식)"""
        try:
            # 빈 응답이나 너무 짧은 응답 체크
            if not html_content or len(html_content.strip()) < 100:
                self.logger.warning("Empty or too short HTML content received")
                return {}
            
            soup = BeautifulSoup(html_content, 'html.parser')
            data = {}
            
            # 제목에서 사건명 추출
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                if '|' in title_text:
                    case_name = title_text.split('|')[0].strip()
                    data['case_name'] = case_name
            
            # 전체 텍스트 추출 - 간단하게 모든 내용을 case_content에 저장
            full_text = soup.get_text()
            if full_text:
                cleaned_text = self._clean_text(full_text)
                if len(cleaned_text) > 500:  # 충분히 긴 텍스트만
                    data['case_content'] = cleaned_text
                    data['full_judgment_text'] = cleaned_text
                    
                    # 기본 정보 추출 (사건번호, 법원명, 선고일자)
                    # 사건번호 패턴 찾기
                    case_number_match = re.search(r'([가-힣]+법원[^-]*-\d{4}-[가-힣]+-\d+|\d{4}[가-힣]+\d+)', cleaned_text)
                    if case_number_match:
                        data['case_number'] = case_number_match.group(1)
                    
                    # 선고일자 패턴 찾기
                    date_match = re.search(r'(\d{4}\.\s*\d{1,2}\.\s*\d{1,2})', cleaned_text)
                    if date_match:
                        data['judgment_date'] = date_match.group(1).replace(' ', '')
                    
                    # 법원명 패턴 찾기
                    court_match = re.search(r'([가-힣]+법원)', cleaned_text)
                    if court_match:
                        data['court_name'] = court_match.group(1)
            
            # 데이터가 비어있는 경우 로그 출력
            if not data or not any(data.values()):
                self.logger.warning("No meaningful content extracted from HTML")
                return {}
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error parsing actual precedent content: {e}")
            return {}
    
    def _optimize_for_bedrock_rag(self, precedent_data: Dict[str, Any]) -> Dict[str, Any]:
        """AWS Bedrock RAG에 최적화된 형태로 데이터 변환"""
        
        # RAG용 통합 텍스트 내용 생성
        text_parts = []
        
        # 사건명 추가 (항상 포함)
        if precedent_data.get("case_name"):
            text_parts.append(f"사건명: {precedent_data['case_name']}")
        
        # 기본 정보 추가
        basic_info_parts = []
        if precedent_data.get("case_number"):
            basic_info_parts.append(f"사건번호: {precedent_data['case_number']}")
        if precedent_data.get("court_name"):
            basic_info_parts.append(f"법원명: {precedent_data['court_name']}")
        if precedent_data.get("judgment_date"):
            basic_info_parts.append(f"선고일자: {precedent_data['judgment_date']}")
        if precedent_data.get("case_type_name"):
            basic_info_parts.append(f"사건종류: {precedent_data['case_type_name']}")
        
        if basic_info_parts:
            text_parts.append("기본정보: " + ", ".join(basic_info_parts))
        
        # 판례 전체 내용 추가 (가장 중요한 부분)
        if precedent_data.get("full_judgment_text"):
            text_parts.append(f"판례내용: {precedent_data['full_judgment_text']}")
        elif precedent_data.get("case_content"):
            text_parts.append(f"판례내용: {precedent_data['case_content']}")
        
        # 통합 텍스트 생성
        text_content = "\n\n".join(text_parts)
        
        # RAG용 메타데이터 생성
        metadata = {
            "case_number": precedent_data.get("case_number", ""),
            "court_name": precedent_data.get("court_name", ""),
            "judgment_date": precedent_data.get("judgment_date", ""),
            "case_type_name": precedent_data.get("case_type_name", ""),
            "keywords": precedent_data.get("keywords", ""),
            "crawl_date": precedent_data.get("crawl_date", ""),
            "document_type": "precedent",
            "prec_id": precedent_data.get("prec_id", ""),
            "document_class": precedent_data.get("document_class", ""),
            "year": precedent_data.get("year", "")
        }
        
        # 중복 필드 제거 (text_content에 통합됨)
        fields_to_remove = [
            "case_content", 
            "full_judgment_text", 
            "judgment_order", 
            "reasoning", 
            "judgment_sections",
            "reply_content",  # 일반적으로 비어있는 필드
            "reference_law",  # 참조조문 제거
            "reference_case"  # 참조판례 제거
        ]
        
        for field in fields_to_remove:
            precedent_data.pop(field, None)
        
        # RAG 최적화 필드 추가
        precedent_data.update({
            "text_content": text_content,
            "title": precedent_data.get("case_name", ""),
            "summary": precedent_data.get("judgment_summary", ""),
            "metadata": metadata
        })
        
        return precedent_data
    
    def _save_precedent_data_individually(self, keyword: str, data: List[Dict[str, Any]]) -> None:
        """판례 데이터를 개별 파일로 저장"""
        if not data:
            return
        
        # 키워드별 디렉토리 생성
        keyword_dir = self.precedent_dir / keyword
        keyword_dir.mkdir(exist_ok=True)
        
        saved_count = 0
        for i, precedent in enumerate(data):
            try:
                # 파일명 생성 (prec_id가 있으면 사용, 없으면 인덱스 사용)
                prec_id = precedent.get('prec_id', f'{i+1:04d}')
                filename = f"precedent_{prec_id}.json"
                filepath = keyword_dir / filename
                
                # 개별 파일로 저장
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(precedent, f, ensure_ascii=False, indent=2)
                
                saved_count += 1
                
            except Exception as e:
                self.logger.error(f"Error saving precedent {precedent.get('prec_id', i)}: {e}")
        
        self.logger.info(f"Saved {saved_count} precedent records individually to {keyword_dir}")
    
    def _save_precedent_data(self, keyword: str, data: List[Dict[str, Any]]) -> None:
        """판례 데이터 저장 (레거시 메서드 - 호환성 유지)"""
        if not data:
            return
        
        filename = f"precedent_{keyword}.json"
        filepath = self.precedent_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Saved {len(data)} precedent records to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error saving precedent data for {keyword}: {e}")
    
    def cleanup(self) -> None:
        """정리 작업"""
        if hasattr(self, 'session'):
            self.session.close()
        self.logger.info("Law Open API crawler cleanup completed") 