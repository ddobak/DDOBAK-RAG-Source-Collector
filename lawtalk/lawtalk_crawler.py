from common.base_crawler import BaseCrawler
import requests
from typing import Optional
from lawtalk.lawtalk_config import config
from lawtalk.cases.get_qna_data import collect_qna_cases_with_pagination
from lawtalk.cases.get_solved_data import get_all_categories_solved_cases
from lawtalk.cases.get_guide_data import get_all_categories_guide_posts

class LawtalkCrawler(BaseCrawler):
    """로톡 크롤러 베이스 클래스"""
    
    def __init__(self, crawl_options: Optional[dict] = None):
        super().__init__(crawl_options)
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
            # 로그인 요청
            response = self.session.post(
                config.LOGIN_URL,
                json=config.LOGIN_PAYLOAD,
                headers={
                    **config.BASE_HEADERS,
                    "Referer": config.LOGIN_REFERER
                }
            )
            response.raise_for_status()
            
            # 세션 쿠키 추출
            session_cookie = None
            for cookie in response.cookies:
                if cookie.name == "connect.sid":
                    session_cookie = cookie
                    break
            
            if session_cookie:
                self.session_cookie = session_cookie
                self.logger.info("Successfully logged in to Lawtalk")
                return {'success': True, 'session_cookie': session_cookie}
            else:
                self.logger.error("Session cookie not found in login response")
                return {'success': False, 'error': 'Session cookie not found'}
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Login request failed: {e}")
            return {'success': False, 'error': f'Login failed: {str(e)}'}
        except Exception as e:
            self.logger.error(f"Unexpected error during login: {e}")
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}

    def setup(self) -> bool:
        """크롤러 초기 설정"""
        login_result = self._login()
        return login_result.get('success', False)

    def crawl_consultation_cases(self, start_offset: int = 0, end_offset: int = None, 
                               simple_result: bool = False, storage_type: bool = True,
                               only_new: bool = False) -> dict:
        """상담사례 크롤링"""
        if not self.session_cookie:
            self.logger.error("Not logged in. Please run setup() first.")
            return {'success': False, 'error': 'Not logged in'}
        
        self.logger.info(f"Starting consultation cases crawling: offset {start_offset} to {end_offset}, only_new={only_new}")
        
        result = collect_qna_cases_with_pagination(
            session_cookie=self.session_cookie,
            start_offset=start_offset,
            end_offset=end_offset,
            simple_result=simple_result,
            storage_type=storage_type,
            only_new=only_new
        )
        
        return result

    def crawl_solved_cases(self, start_offset: int = 0, end_offset: int = None, 
                         simple_result: bool = False, storage_type: bool = True,
                         only_new: bool = False) -> dict:
        """해결된 사례 크롤링"""
        if not self.session_cookie:
            self.logger.error("Not logged in. Please run setup() first.")
            return {'success': False, 'error': 'Not logged in'}
        
        self.logger.info(f"Starting solved cases crawling: offset {start_offset} to {end_offset}, only_new={only_new}")
        
        result = get_all_categories_solved_cases(
            session_cookie=self.session_cookie,
            start_offset=start_offset,
            end_offset=end_offset,
            simple_result=simple_result,
            storage_type=storage_type,
            only_new=only_new
        )
        
        return result

    def crawl_guide_posts(self, start_offset: int = 0, end_offset: int = None, 
                         simple_result: bool = False, storage_type: bool = True,
                         only_new: bool = False) -> dict:
        """가이드 포스트 크롤링"""
        if not self.session_cookie:
            self.logger.error("Not logged in. Please run setup() first.")
            return {'success': False, 'error': 'Not logged in'}
        
        self.logger.info(f"Starting guide posts crawling: offset {start_offset} to {end_offset}, only_new={only_new}")
        
        result = get_all_categories_guide_posts(
            session_cookie=self.session_cookie,
            start_offset=start_offset,
            end_offset=end_offset,
            simple_result=simple_result,
            storage_type=storage_type,
            only_new=only_new
        )
        
        return result

    def crawl(self) -> None:
        """기본 크롤링 수행"""
        if not self.setup():
            self.logger.error("Failed to setup crawler")
            return
        
        # 기본적으로 상담사례와 해결된 사례 모두 크롤링
        self.logger.info("Starting default crawl (consultation + solved cases)")
        
        consultation_start_offset = config.CONSULTATION_OFFSET_START
        consultation_end_offset = config.CONSULTATION_OFFSET_END

        # 상담사례 크롤링
        consultation_result = self.crawl_consultation_cases(
            start_offset=consultation_start_offset, 
            end_offset=consultation_end_offset, 
            simple_result=self.crawl_options['simple_result'],
            storage_type=self.crawl_options['storage_type'],
            only_new=self.crawl_options['only_new']
        )
        
        if consultation_result.get('success'):
            self.logger.info(f"Consultation cases completed: {consultation_result.get('total_questions', 0)} questions")
        else:
            self.logger.error("Consultation cases crawling failed")

        solved_start_offset = config.SOLVED_CASES_OFFSET_START
        solved_end_offset = config.SOLVED_CASES_OFFSET_END
        
        # 해결된 사례 크롤링
        solved_result = self.crawl_solved_cases(
            start_offset=solved_start_offset, 
            end_offset=solved_end_offset, 
            simple_result=self.crawl_options['simple_result'],
            storage_type=self.crawl_options['storage_type'],
            only_new=self.crawl_options['only_new']
        )
        
        if solved_result.get('success'):
            self.logger.info(f"Solved cases completed: {solved_result.get('total_posts', 0)} posts")
        else:
            self.logger.error("Solved cases crawling failed")

        guide_start_offset = config.GUIDE_POSTS_OFFSET_START
        guide_end_offset = config.GUIDE_POSTS_OFFSET_END
        
        # 가이드 포스트 크롤링
        guide_result = self.crawl_guide_posts(
            start_offset=guide_start_offset,
            end_offset=guide_end_offset,
            simple_result=self.crawl_options['simple_result'],
            storage_type=self.crawl_options['storage_type'],
            only_new=self.crawl_options['only_new']
        )
        
        if guide_result.get('success'):
            self.logger.info(f"Guide posts completed: {guide_result.get('total_posts', 0)} posts")
        else:
            self.logger.error("Guide posts crawling failed")

    def run(self) -> None:
        """기본 크롤링 수행"""
        self.crawl()


        