from lawtalk.common.lawtalk_crawler import LawtalkCrawler


def test_request_qna_cases():
    crawler = LawtalkCrawler()
    crawler.run()
    


if __name__ == "__main__":
    test_request_qna_cases()