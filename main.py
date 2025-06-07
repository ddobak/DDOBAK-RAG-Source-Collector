"""
DDOBAK RAG Source Collector 메인 진입점
"""
import click
import sys
from common.crawler_registry import create_crawler, list_available_sites
from utils.validate_args import validate_and_convert_args, exit_with_errors


@click.command()
@click.argument("site")
@click.argument("simple_result", default="simple")
@click.argument("storage_type", default="local")
@click.argument("only_new", default="all")
def main(site: str, simple_result: str, storage_type: str, only_new: str) -> None:
    """사이트 크롤링 실행"""
    # 사이트 유효성 검사
    available_sites = list_available_sites()
    if site not in available_sites:
        print(f"Unknown site: {site}")
        print(f"Available sites: {', '.join(available_sites)}")
        sys.exit(1)
    
    # 인자 검증 및 변환
    validation_result = validate_and_convert_args(simple_result, storage_type, only_new)
    
    if not validation_result['valid']:
        exit_with_errors(validation_result['errors'])
    
    crawl_options = validation_result['options']
    print(f"Crawl options: simple_result={simple_result}, storage_type={storage_type}, only_new={only_new}")
    
    # 크롤러 생성 (옵션과 함께)
    crawler = create_crawler(site, crawl_options)
    if not crawler:
        print(f"Crawler creation failed: {site}")
        sys.exit(1)
    
    # 크롤링 실행
    try:
        print(f"{site} Crawling started...")
        crawler.run()
        print(f"{site} Crawling completed!")
    except Exception as e:
        print(f"Crawling execution error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
