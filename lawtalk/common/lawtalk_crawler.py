from common.base_crawler import BaseCrawler
import requests
from lawtalk.lawtalk_config import config
from lawtalk.consultation_case.get_qna_data import collect_and_save_qna_cases


class LawtalkCrawler(BaseCrawler):
    """로톡 크롤러 베이스 클래스"""
    
    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session_cookie = None

    def get_site_name(self) -> str:
        """사이트 이름 반환"""
        return "lawtalk"
    
    def _login(self) -> dict:
        """로톡 로그인 수행"""
        if not config.LOGIN_PAYLOAD["username"] or not config.LOGIN_PAYLOAD["password"]:
            self.logger.error("Login credentials not found in environment variables")
            return {'success': False, 'error': 'Missing credentials'}
        try:
            login_headers = config.BASE_HEADERS.copy()
            login_headers["Referer"] = config.LOGIN_REFERER
            response = self.session.post(
                config.LOGIN_URL,
                headers=login_headers,
                json=config.LOGIN_PAYLOAD
            )
            if response.status_code == 200:
                user_info = response.json()
                self.logger.info(f"Login successful: {user_info['username']}")
                
                # 세션 쿠키 확인
                session_cookie = None
                for cookie in response.cookies:
                    if cookie.name == 'connect.sid':
                        session_cookie = cookie
                        break
                
                return {
                    'success': True,
                    'user_info': user_info,
                    'session_cookie': session_cookie
                }
            else:
                self.logger.error(f"Login failed: {response.text}")
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            self.logger.error(f"Login error occurred: {e}")
            return {'success': False, 'error': str(e)}

    def setup(self) -> None:
        """크롤링 전 로그인 수행"""
        login_result = self._login()
        if not login_result.get('success'):
            raise Exception("Login failed, cannot proceed with crawling")
        
        self.session_cookie = login_result.get('session_cookie')
        self.logger.info("Login successful, ready for crawling")

    def crawl(self) -> None:
        """기본 크롤링 메서드 (하위 클래스에서 구현)"""
        self.logger.info("LawtalkCrawler crawl Started")
        offset_start = config.CONSULTATION_OFFSET_START
        offset_end = config.CONSULTATION_OFFSET_END
        self.crawl_consultation_cases(start_offset=offset_start, end_offset=offset_end, simple_result=True, save_local=True)

    def crawl_consultation_cases(self, start_offset: int = 0, end_offset: int = None, 
                               simple_result: bool = False, save_local: bool = False) -> dict:
        """
        로톡 Q&A 상담사례를 offset별로 개별 수집하여 각각 저장합니다.
        
        Args:
            start_offset: 시작 offset
            end_offset: 종료 offset (None이면 한 번만 요청)
            simple_result: True면 간소화된 데이터, False면 상세 데이터
            save_local: True면 로컬 저장, False면 S3 저장
            
        Returns:
            dict: 수집 및 저장 결과
        """
        self.logger.info(f"Starting consultation cases crawling: offset {start_offset} to {end_offset}")
        
        if not self.session_cookie:
            self.logger.error("Session cookie is required for crawling")
            return {'success': False, 'error': 'No session cookie - login first'}
        
        # 데이터 수집 및 저장
        return collect_and_save_qna_cases(
            session_cookie=self.session_cookie,
            start_offset=start_offset,
            end_offset=end_offset,
            simple_result=simple_result,
            save_local=save_local
        )


        