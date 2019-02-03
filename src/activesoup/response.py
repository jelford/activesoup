class UnknownResponseType(RuntimeError):
    pass


class Response:
    def __init__(self, raw_response, content_type):
        self._raw_response = raw_response
        self._content_type = content_type

    @property
    def url(self):
        return self._raw_response.url

    @property
    def status_code(self):
        return self._raw_response.status_code

    @property
    def response(self):
        return self._raw_response

    def __getattr__(self, attr):
        raise UnknownResponseType(
            f"Wasn't sure how to parse this response (type: {self._content_type}), can't dive any deeper"
        )
