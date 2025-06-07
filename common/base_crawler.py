"""
크롤러 베이스 클래스
모든 크롤러가 상속받아야 하는 공통 인터페이스와 기본 구현을 제공합니다.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import logging

from config import config


class BaseCrawler(ABC):
    """모든 크롤러가 상속받아야 하는 베이스 클래스"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.output_dir = self._setup_output_dir()
    
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
        output_dir = config.DATA_DIR / self.__class__.__name__
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    
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
        try:
            self.logger.info(f"Starting crawling for {self.get_site_name()}")
            self.setup()
            self.crawl()
            self.logger.info(f"Crawling completed for {self.get_site_name()}")
        except Exception as e:
            self.logger.error(f"Crawling failed for {self.get_site_name()}: {e}")
            raise
        finally:
            self.cleanup() 