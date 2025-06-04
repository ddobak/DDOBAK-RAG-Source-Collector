"""
DDOBAK RAG Source Collector 메인 진입점
"""
import click
import sys
from common.crawler_registry import create_crawler, list_available_sites


@click.command()
@click.argument("site")
def main(site: str) -> None:
    """사이트 크롤링 실행"""
    # 사이트 유효성 검사
    available_sites = list_available_sites()
    if site not in available_sites:
        print(f"알 수 없는 사이트: {site}")
        print(f"사용 가능한 사이트: {', '.join(available_sites)}")
        sys.exit(1)
    
    # 크롤러 생성
    crawler = create_crawler(site)
    if not crawler:
        print(f"크롤러 생성에 실패했습니다: {site}")
        sys.exit(1)
    
    # 크롤링 실행
    try:
        print(f"{site} 크롤링을 시작합니다...")
        crawler.run()
        print(f"{site} 크롤링이 완료되었습니다!")
    except Exception as e:
        print(f"크롤링 실행 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
