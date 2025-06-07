"""
크롤러 베이스 클래스
모든 크롤러가 상속받아야 하는 공통 인터페이스와 기본 구현을 제공합니다.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from config import config


class BaseCrawler(ABC):
    """
    모든 크롤러가 상속받아야 하는 베이스 클래스
    
    이 클래스는 크롤러의 공통 기능을 제공하며,
    각 사이트별 크롤러는 get_site_name()과 crawl() 메서드만 구현하면 됩니다.
    """
    
    def __init__(self, crawl_options: Optional[Dict[str, Any]] = None) -> None:
        """
        크롤러를 초기화합니다.
        
        Args:
            crawl_options: 크롤링 옵션 딕셔너리
        """
        self.logger = self._setup_logger()
        self.output_dir = self._setup_output_dir()
        self.crawl_options = self._setup_crawl_options(crawl_options)
        
        self.logger.info(f"Crawler initialized with options: {self.crawl_options}")
    
    def _setup_logger(self) -> logging.Logger:
        """로거를 설정합니다."""
        logger = logging.getLogger(self.__class__.__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(config.LOG_FORMAT)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(getattr(logging, config.LOG_LEVEL))
            logger.propagate = False  # 부모 로거로의 전파 차단
        return logger
    
    def _setup_output_dir(self) -> Path:
        """출력 디렉토리를 설정합니다."""
        output_dir = config.DATA_DIR / self.get_site_name()
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    
    def _setup_crawl_options(self, crawl_options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """크롤링 옵션을 설정합니다."""
        default_options = {
            'simple_result': True,    # 간소화된 결과 여부
            'storage_type': True,     # 로컬 저장 여부 (False면 S3)
            'only_new': False         # 새로운 데이터만 크롤링 여부
        }
        
        if crawl_options:
            default_options.update(crawl_options)
        
        return default_options

    @abstractmethod
    def get_site_name(self) -> str:
        """사이트 이름을 반환하는 추상 메서드"""
        pass
    
    @abstractmethod
    def crawl(self) -> None:
        """실제 크롤링 로직을 구현해야 하는 추상 메서드"""
        pass
    
    def setup(self) -> None:
        """크롤링 전 초기화 작업 (선택적 구현)"""
        pass
    
    def cleanup(self) -> None:
        """크롤링 후 정리 작업 (선택적 구현)"""
        pass
    
    def run(self) -> None:
        """크롤링 실행의 전체 흐름을 관리"""
        site_name = self.get_site_name()
        try:
            self.logger.info(f"Starting crawling for {site_name}")
            self.setup()
            self.crawl()
            self.logger.info(f"Crawling completed for {site_name}")
        except Exception as e:
            self.logger.error(f"Crawling failed for {site_name}: {e}")
            raise
        finally:
            self.cleanup() 