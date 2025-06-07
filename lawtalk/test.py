from lawtalk.common.lawtalk_crawler import LawtalkCrawler
from lawtalk.consultation_case.get_qna_data import request_qna_cases


def test_request_qna_cases():
    response = request_qna_cases()
    print(response)


if __name__ == "__main__":
    crawler = LawtalkCrawler()
    login_response = crawler.run()
    print(login_response)
    print(login_response['session_cookie'])
    qna_response = request_qna_cases(login_response['session_cookie'], offset=0)
    print(qna_response)