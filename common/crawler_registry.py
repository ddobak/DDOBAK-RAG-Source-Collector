"""
크롤러 레지스트리
Poetry entry points를 통한 크롤러 관리를 담당합니다.
"""
from importlib.metadata import entry_points
from typing import Dict, Any, Optional


def get_available_crawlers() -> Dict[str, Any]:
    """Poetry entry points에서 등록된 크롤러들을 조회합니다."""
    crawlers = {}
    try:
        # Poetry plugins에서 크롤러 엔트리 포인트 로드
        eps = entry_points(group='ddobak.crawlers')
        for ep in eps:
            crawlers[ep.name] = ep
    except Exception as e:
        print(f"크롤러 목록 로드 실패: {e}")
    
    return crawlers


def create_crawler(site: str) -> Optional[Any]:
    """사이트별 크롤러 인스턴스를 생성합니다."""
    crawlers = get_available_crawlers()
    
    if site not in crawlers:
        return None
    
    try:
        # Entry point에서 크롤러 클래스 로드
        crawler_class = crawlers[site].load()
        return crawler_class()
    except Exception as e:
        print(f"크롤러 생성 실패 ({site}): {e}")
        return None


def list_available_sites() -> list[str]:
    """사용 가능한 사이트 목록을 반환합니다."""
    return list(get_available_crawlers().keys()) 