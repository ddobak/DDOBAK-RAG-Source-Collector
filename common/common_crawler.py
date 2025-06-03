"""
공통 크롤러 관리 클래스
"""
from typing import Dict, Any


class CommonCrawler:
    """사이트별 크롤러를 관리하는 공통 크롤러"""
    
    def __init__(self):
        # 크롤러 팩토리 - 새로운 사이트 추가시 여기만 수정하면 됨
        self.crawler_factory = {
            "lawtalk": ("lawtalk.lawtalk_crawler", "LawtalkCrawler"),
            "law_open_api": ("law_open_api.api_crawler", "ApiCrawler"),
            "easylaw": ("easylaw.crawler", "EasylawCrawler"),
        }
    
    def run(self, config: Dict[str, Any]) -> None:
        """설정에 따라 적절한 크롤러를 실행합니다."""
        site = config.get("site")
        
        if site not in self.crawler_factory:
            print(f"Unknown site: {site}")
            return
        
        # 팩토리에서 크롤러 생성
        crawler = self._create_crawler(site)
        if crawler:
            crawler.run()
    
    def _create_crawler(self, site: str):
        """팩토리 패턴으로 크롤러 생성"""
        try:
            module_path, class_name = self.crawler_factory[site]
            
            # 동적 import
            module = __import__(module_path, fromlist=[class_name])
            crawler_class = getattr(module, class_name)
            
            return crawler_class()
            
        except Exception as e:
            print(f"Failed to create crawler for {site}: {e}")
            return None 