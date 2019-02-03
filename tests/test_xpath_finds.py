import pytest

from activesoup import driver


@pytest.fixture
def nested_objects_page(localwebserver):
    d = driver.Driver()
    yield d.get(
        f"http://localhost:{localwebserver.port}/html/page_with_nested_objects.html"
    )


def test_can_get_something(nested_objects_page):
    content_body = nested_objects_page.find('.//div[@class="content-body"]')

    assert content_body is not None
    assert content_body["class"] == "content-body"
    assert "Something in the content-body" in content_body.text()
