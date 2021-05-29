import functools
from typing import Any, Dict, Optional, Callable

from urllib.parse import urljoin

import requests

import activesoup
import activesoup.html
from activesoup.response import CsvResponse, JsonResponse


class DriverError(RuntimeError):
    """Errors that occur as part of operating the driver
    
    These errors reflect logic errors (such as accessing the ``last_response``
    before navigating) or that the ``Driver`` is unable to carry out the
    action that was requested (e.g. the server returned a bad redirect)"""
    pass


_Resolver = Callable[[requests.Response], activesoup.Response]


class ContentResolver:
    def __init__(self):
        self._resolvers: Dict[str, _Resolver] = {}

    def register(self, content_type: str, resolver: _Resolver) -> None:
        self._resolvers[content_type] = resolver

    def resolve(self, response: requests.Response) -> activesoup.Response:
        content_type = response.headers.get("Content-Type", None)
        if content_type is not None:
            for k, factory in self._resolvers.items():
                if content_type.startswith(k):
                    return factory(response)

        return activesoup.Response(response, content_type)


class Driver:
    """:py:class:`Driver` is the main entrypoint into ``activesoup``.

    The ``Driver`` provides navigation functions, and keeps track of the
    current page. Note that this class is re-exposed via ``activesoup.Driver``.

    >>> d = Driver()
    >>> page = d.get("https://github.com/jelford/activesoup")
    >>> assert d.url == "https://github.com/jelford/activesoup"

    - Navigation updates the current page
    - Any methods which are not defined directly on ``Driver`` are
      forwarded on to the most recent ``Response`` object

    A single :py:class:`requests.Session` is held open for the
    lifetime of the ``Driver`` - the ``Session`` will accumulate
    cookies and open connections. ``Driver`` may be used as a
    context manager to automatically close all open connections
    when finished:

    .. code-block::

        with Driver() as d:
            d.get("https://github.com/jelford/activesoup")

    See :ref:`getting-started` for a full demo of usage.

    :param kwargs: optional keyword arguments may be passed, which will be set
        as attributes of the :py:class:`requests.Session` which will be used
        for the lifetime of this ``Driver``:

        >>> d = Driver(headers={"User-Agent": "activesoup script"})
        >>> d.session.headers["User-Agent"]
        'activesoup script'
    """

    def __init__(self, **kwargs) -> None:
        self.session = requests.Session()
        for k, v in kwargs.items():
            setattr(self.session, k, v)
        self._last_response: Optional[activesoup.Response] = None
        self._raw_response: Optional[requests.Response] = None
        self.content_resolver = ContentResolver()
        self.content_resolver.register(
            "text/html", functools.partial(activesoup.html.resolve, self)
        )
        self.content_resolver.register("text/csv", CsvResponse)
        self.content_resolver.register(
            "application/json", JsonResponse
        )

    def __enter__(self) -> "Driver":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.session.close()

    def _resolve_url(self, possibly_relative_url) -> str:
        """Converts a relative URL into an absolute one if possible.

        If there is no current page (because the ``Driver`` has not yet received
        a call to :py:meth:`Driver.get`), then the URL is returned unchanged

        >>> d = Driver()
        >>> d._resolve_url("./something")
        './something'
        >>> _ = d.get("https://github.com/jelford/activesoup/")
        >>> d._resolve_url("./something")
        'https://github.com/jelford/activesoup/something'

        :param str possibly_relative_url: A URL which is assumed to be relative
            the current page
        :returns: A URL that has been resolved relative to the current page, if
            there is one.
        """
        current_url_str = self.url
        if not current_url_str:
            return possibly_relative_url

        return urljoin(current_url_str, possibly_relative_url)

    def get(self, url, **kwargs) -> "Driver":
        """Move the Driver to a new page.

        This is the primary means of navigating the ``Driver`` to the page of interest.

        :param str url: the new URL for the Driver to navigate to (e.g. `https://www.example.com`)
        :param kwargs: additional keyword arguments are passed in to the
            constructor of the :py:class:`requests.Request` used to fetch the
            page.
        :returns: the ``Driver`` object itself
        :rtype: Driver

        """
        return self._do(requests.Request(method="GET", url=url, **kwargs))

    def _do(self, request: requests.Request) -> "Driver":
        request.url = self._resolve_url(request.url)
        prepped = self.session.prepare_request(request)
        return self._handle_response(self.session.send(prepped))

    def _handle_response(self, response: requests.Response) -> "Driver":
        if response.status_code in range(300, 304):
            redirected_to = response.headers.get("Location", None)
            if not redirected_to:
                raise DriverError("Found a redirect, but no onward location given")
            return self.get(redirected_to)

        self._last_response = self.content_resolver.resolve(response)
        self._raw_response = response

        return self

    @property
    def url(self) -> Optional[str]:
        """The URL of the current page

        :returns: ``None`` if no page has been loaded, otherwise the URL of the most recently
            loaded page.
        :rtype: str
        """
        return self._last_response.url if self._last_response is not None else None

    @property
    def last_response(self) -> Optional[activesoup.Response]:
        """Get the response object that was the result of the most recent page load

        :returns: ``None`` if no page has been loaded, otherwise the parsed result of the most
            recent page load
        :rtype: activesoup.Response
        """
        return self._last_response

    def __getattr__(self, item) -> Any:
        if not self._last_response:
            raise DriverError("Not on a page")

        return getattr(self._last_response, item)

    def __getitem__(self, item) -> Any:
        if not self._last_response:
            raise DriverError("Not on a page")

        return self._last_response[item]

    def __str__(self) -> str:
        last_resp_str = str(self._last_response) if self._last_response else "unbound"
        return f"<activesoup.driver.Driver[{last_resp_str}]>"
