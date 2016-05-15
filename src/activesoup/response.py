class Response:

    def __init__(self, raw_response):
        self._raw_response = raw_response

    @property
    def url(self):
        return self._raw_response.url

    @property
    def status_code(self):
        return self._raw_response.status_code

    @property
    def response(self):
        return self._raw_response
