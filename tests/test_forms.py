
from activesoup import driver


def test_form_submission_includes_form_fields_which_arent_specified(
        localwebserver):
    d = driver.Driver()
    page = d.get(f'http://localhost:{localwebserver.port}/html/page_with_form.html')
    result = page.form.submit({'visible_field': 'my-value'})

    assert result._raw_response.json() == {
        'visible_field': 'my-value',
        'visible-field-with-value': 'preset-value',
        'some-hidden-field': '5'
    }


def test_unspecified_fields_can_be_suppressed_on_form_submission(
        localwebserver):
    d = driver.Driver()
    page = d.get(f'http://localhost:{localwebserver.port}/html/page_with_form.html')
    result = page.form.submit(
        {'visible_field': 'my-value'}, suppress_unspecified=True)

    assert result._raw_response.json() == {
        'visible_field': 'my-value'
    }


def test_can_submit_form_without_explicit_method(localwebserver):
    d = driver.Driver()
    page = d.get(f'http://localhost:{localwebserver.port}/html/page_with_form_no_method.html')

    result = page.find('.//form[@id="no-method"]').submit({'fieldname': 'value'},
                                                          suppress_unspecified=True)

    assert result._raw_response.json() == {
        'fieldname': 'value'
    }


def test_can_submit_form_without_explicit_action(localwebserver):
    d = driver.Driver()
    page = d.get(f'http://localhost:{localwebserver.port}/form/page_with_form_no_method.html')
    result = page.find('.//form[@id="no-action"]').submit({'fieldname': 'value'},
                                                          suppress_unspecified=True)

    assert result._raw_response.json() == {
        'fieldname': 'value'
    }
