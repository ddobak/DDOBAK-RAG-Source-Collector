"""
DDOBAK RAG Source Collector 메인 진입점
"""
import click
from config import settings
from common.base_crawler import CommonCrawler


@click.command()
@click.argument("site")
def main(site: str) -> None:
    """사이트 크롤링 실행"""
    config = {
        "site": site,
        "settings": settings
    }
    
    crawler = CommonCrawler()
    crawler.run(config)


if __name__ == "__main__":
    main()
