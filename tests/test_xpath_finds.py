import pytest

from activesoup import driver


@pytest.fixture
def nested_objects_page(localwebserver):
    d = driver.Driver()
    yield d.get(
        f"http://localhost:{localwebserver.port}/html/page_with_nested_objects.html"
    )


@pytest.fixture
def articles_list_page(localwebserver):
    d = driver.Driver()
    yield d.get(
        f"http://localhost:{localwebserver.port}/html/page_with_article_list.html"
    )


def test_can_get_something(nested_objects_page):
    content_body = nested_objects_page.find('.//div[@class="content-body"]')

    assert content_body is not None
    assert content_body["class"] == "content-body"
    assert "Something in the content-body" in content_body.text()


def test_can_find_by_id(articles_list_page):
    articles_list = articles_list_page.find(id="articles")

    assert articles_list is not None

    article_links = articles_list.find_all('li[@class="article"]/a')
    hrefs = [a["href"] for a in article_links]
    assert len(article_links) == 3
    assert hrefs == [
        "https://example.com/article1",
        "https://example.com/article2",
        "https://example.com/article3",
    ]
