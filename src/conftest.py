"""
Test context for doctests
"""

import pytest


@pytest.fixture(autouse=True)
def add_html_parsing(doctest_namespace):
    import requests
    import activesoup.html
    def html_page(raw_html):
        response_from_server = requests.Response()
        response_from_server._content = raw_html.encode('utf-8')
        return activesoup.html.resolve(driver=None, response=response_from_server) # typing: ignore
    
    doctest_namespace["html_page"] = html_page


@pytest.fixture(autouse=True)
def add_json_parsing(doctest_namespace):
    import requests
    import activesoup.response
    def json_page(raw_json):
        response_from_server = requests.Response()
        response_from_server._content = raw_json.encode('utf-8')
        return activesoup.response.JsonResponse(raw_response=response_from_server)
    
    doctest_namespace["json_page"] = json_page


@pytest.fixture(autouse=True)
def fake_github(requests_mock):
    for form in ("https://github.com/jelford/activesoup/", "https://github.com/jelford/activesoup"):
        requests_mock.get(form, 
            text="<html><body><h1>Fake activesoup repo</h1></body></html>",
            headers={
                "Content-Type": "text/html"
            })

    requests_mock.get("https://github.com/jelford/activesoup/issues/new",
        text="<html><body><form></form></body></html>",
        headers={
            "Content-Type": "text/html"
        })
    requests_mock.post("https://github.com/jelford/activesoup/issues/new",
        status_code=302,
        headers={"Location": "https://github.com/jelford/activesoup/issues/1"})
    requests_mock.get("https://github.com/jelford/activesoup/issues/1", text="Dummy page")