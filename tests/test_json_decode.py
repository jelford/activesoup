from activesoup import driver


def test_json_response_decoded_as_json_object(localwebserver):
    d = driver.Driver()
    resp = d.get('http://localhost:60123/json?foo=bar')
    assert resp['foo'] == 'bar'
