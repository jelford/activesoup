"""
The module contains the various types of response object, used to access after
navigating to a page with :py:meth:`activesoup.Driver.get`. All responses
are instances of :py:class:`activesoup.response.Response`. When ``activesoup``
recognises the type of data, the response is specialized for convenient access.
This detection is driven by the ``Content-Type`` header in the server's response
(so, if a web server labels a CSV file as HTML, ``activesoup`` will just assume
it's ``HTML`` and try to parse it as such)

The following specialisations are applied:

``text/html``
    :py:class:`activesoup.html.BoundTag`. The HTML page is parsed, and a handle
    to the top-level ``<html>`` element is provided.

``text/csv``
    :py:class:`activesoup.response.CsvResponse`

``application/json``
    :py:class:`activesoup.response.JsonResponse`. The JSON data is parsed into
    python objects via ``json.loads``, and made available via dictionary-like 
    access.

"""

import requests

from typing import Union, Dict, Any, List, Optional
from pathlib import Path
from typing import Union, IO


class UnknownResponseType(RuntimeError):
    pass


class Response:
    """The result of a page load by :py:class:`activesoup.Driver`.

    :param requests.Response raw_response: The raw data returned from the server.
    :param str content_type: The datatype used for interpretting this response object.

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
        """Which URL was requested that resulted in this response?
        
        :rtype: str"""
        return self._raw_response.url

    @property
    def status_code(self):
        """Status code from the HTTP response

        e.g. 200
        
        :rtype: int"""
        return self._raw_response.status_code

    @property
    def response(self):
        """The raw :py:class:`requests.Response` object returned by the server.
        
        You can use this object to inspect information not directly available
        through the ``activesoup`` API.
        
        :rtype: requests.Response"""
        return self._raw_response

    @property
    def content_type(self):
        """The type of content contained in this response

        e.g. application/csv
        
        :rtype: str"""

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

    :param requests.Response raw_response: The raw data returned from the server.

    ``JSON`` data returned by the page will be parsed into a Python object:

    >>> raw_content = '{"key": "value"}'
    >>> resp = json_page(raw_content)
    >>> resp["key"]
    'value'

    
    """

    def __init__(self, raw_response: requests.Response) -> None:
        """
        """
        super().__init__(raw_response, "application/json")
        self.json = raw_response.json()

    def __getitem__(
        self, name: Union[str, int]
    ) -> Union[str, int, Dict[str, Any], List[Any]]:
        """Look up an item in the parsed JSON object. 
        
        ``__getitem__`` allows you to treat this object like a JSON array or 
        object directly, without any further unwrapping.
        """
        return self.json[name]

    def __getattr__(self, attr: str) -> Any:
        return getattr(self.json, attr)

    def __repr__(self) -> str:
        return "JsonResponse"

    def __str__(self) -> str:
        return "<[json]>"


class CsvResponse(Response):
    """A response object representing a ``CSV`` page

    :param requests.Response raw_response: The raw data returned from the server.
    
    """

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
