from activesoup import driver


def test_can_get_something(localwebserver):
    d = driver.Driver()
    d.get('http://localhost:60123/foo')


def test_can_decodes_html_into_beautiful_soup_document(localwebserver):
    d = driver.Driver()
    page = d.get('http://localhost:60123/html/simple_page.html')
    page_text = page.body.p.get_text()
    assert page_text == 'text-in-body'
