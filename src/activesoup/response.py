import requests

from typing import Union, Dict, Any, List, Optional
from pathlib import Path
from typing import Union, IO


class UnknownResponseType(RuntimeError):
    pass


class Response:
    """The result of a page load by :py:class:`activesoup.Driver`.

    This top-level class contains attributes common to all responses. Child
    classes contain response-type-specific helpers. Check the :py:attr:`content_type`
    of this object to determine what data you have (and therefore which
    methods are available).

    Generally, fields of a ``Response`` can be accessed directly through the
    ``Driver``:

    >>> import activesoup
    >>> d = activesoup.Driver()
    >>> page = d.get("https://github.com/jelford/activesoup")
    >>> d.content_type
    'text/html'
    >>> links = d.find_all("a") # ... etc
    """

    def __init__(self, raw_response: requests.Response, content_type: Optional[str]):
        self._raw_response = raw_response
        self._content_type = content_type

    @property
    def url(self) -> str:
        """Which URL was requested that resulted in this response?"""
        return self._raw_response.url

    @property
    def status_code(self):
        """Status code from the HTTP response

        e.g. 200"""
        return self._raw_response.status_code

    @property
    def response(self):
        return self._raw_response

    @property
    def content_type(self):
        """The type of content contained in this response

        e.g. application/csv"""

        return self._content_type

    def __getattr__(self, attr):
        raise UnknownResponseType(
            f"Wasn't sure how to parse this response (type: {self._content_type}), can't look up attribute \"{attr}\""
        )

    def __getitem__(self, lookup: str):
        raise UnknownResponseType(
            f"Wasn't sure how to parse this response (type: {self._content_type}), can't look up item \"{lookup}\""
        )


class JsonResponse(Response):
    """A response object representing a ``JSON`` page

    ``JSON`` data returned by the page will be parsed into a Python object:

    >>> import requests
    >>> canned_response = requests.Response()
    >>> canned_response._content = b'{"key": "value"}'
    >>> resp = JsonResponse(canned_response)
    >>> resp["key"]
    'value'
    """

    def __init__(self, raw_response: requests.Response) -> None:
        super().__init__(raw_response, "application/json")
        self.json = raw_response.json()

    def __getitem__(
        self, name: Union[str, int]
    ) -> Union[str, int, Dict[str, Any], List[Any]]:
        return self.json[name]

    def __getattr__(self, attr: str) -> Any:
        return getattr(self.json, attr)

    def __repr__(self) -> str:
        return "JsonResponse"

    def __str__(self) -> str:
        return "<[json]>"


class CsvResponse(Response):
    """A response object representing a ``CSV`` page"""

    def __init__(self, raw_response):
        super().__init__(raw_response, "text/csv")
        self.content = raw_response.content

    def save(self, to: Union[Path, str, IO]):
        """Saves the current page to ``to``

        :param to: Where to save the file. ``to`` may be a path (in which case
            that path will be opened in binary mode, and truncated if it
            already exists) or a file-like object (in which case that object
            will be written to directly)"""

        if isinstance(to, type("")) or isinstance(to, Path):
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
