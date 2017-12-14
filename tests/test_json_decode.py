from activesoup import driver


def test_json_response_decoded_as_json_object(localwebserver):
    d = driver.Driver()
    resp = d.get(f'http://localhost:{localwebserver.port}/json?foo=bar')
    assert resp['foo'] == 'bar'
