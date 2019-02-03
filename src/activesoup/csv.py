import requests

from activesoup.protocols import ActiveSoupResult
from activesoup.response import Response


class CsvResponse(Response):
    def __init__(self, raw_response):
        super().__init__(raw_response)
        self.content = raw_response.content

    def save(self, to):
        if isinstance(to, type("")):
            with open(to, "wb") as f:
                self._write_to_file(f)
        else:
            self._write_to_file(to)

    def _write_to_file(self, file_object):
        file_object.write(self.content)

    def __repr__(self) -> str:
        return "CsvResponse"

    def __str__(self) -> str:
        return "<[csv]>"


class Resolver:
    def resolve(self, raw_response: requests.Response) -> ActiveSoupResult:
        return CsvResponse(raw_response)
