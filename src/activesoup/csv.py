from activesoup.response import Response


def resolve(response):
    return CsvResponse(response)


class CsvResponse(Response):

    def __init__(self, raw_response):
        super().__init__(raw_response)
        self.content = raw_response.content

    def save(self, to):
        if isinstance(to, type('')):
            with open(to, 'wb') as f:
                self._write_to_file(f)
        else:
            self._write_to_file(to)

    def _write_to_file(self, file_object):
        file_object.write(self.content)
