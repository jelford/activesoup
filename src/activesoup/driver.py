from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests

import activesoup.csv
import activesoup.html
import activesoup.json_response
import activesoup.response
from activesoup.protocols import ActiveSoupResult, Resolver


class DriverError(RuntimeError):
    pass


class ContentResolver:
    def __init__(self):
        self._resolvers: Dict[str, Resolver] = {}

    def register(self, content_type: str, resolver: Resolver) -> None:
        self._resolvers[content_type] = resolver

    def resolve(self, response: requests.Response) -> ActiveSoupResult:
        content_type = response.headers.get("Content-Type", None)
        if content_type is not None:
            for k, v in self._resolvers.items():
                if content_type.startswith(k):
                    return v.resolve(response)

        return activesoup.response.Response(response, content_type)


class Driver:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.last_response: Optional[ActiveSoupResult] = None
        self._raw_response: Optional[requests.Response] = None
        self.content_resolver = ContentResolver()
        self.content_resolver.register("text/html", activesoup.html.Resolver(self))
        self.content_resolver.register("text/csv", activesoup.csv.Resolver())
        self.content_resolver.register(
            "application/json", activesoup.json_response.Resolver()
        )

    def __enter__(self) -> "Driver":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.session.close()

    def resolve_url(self, possibly_relative_url) -> str:
        current_url_str = self.url
        if not current_url_str:
            return possibly_relative_url

        return urljoin(current_url_str, possibly_relative_url)

    def get(self, url, **kwargs):
        return self.do(requests.Request(method="GET", url=url))

    def do(self, request: requests.Request) -> "Driver":
        request.url = self.resolve_url(request.url)
        prepped = self.session.prepare_request(request)
        return self.handle_response(self.session.send(prepped))

    def handle_response(self, response: requests.Response) -> "Driver":
        if response.status_code in range(300, 304):
            redirected_to = response.headers.get("Location", None)
            if not redirected_to:
                raise DriverError("Found a redirect, but no onward location given")
            return self.get(redirected_to)

        self.last_response = self.content_resolver.resolve(response)
        self._raw_response = response

        return self

    @property
    def url(self) -> Optional[str]:
        return self.last_response.url if self.last_response is not None else None

    def __getattr__(self, item) -> Any:
        if not self.last_response:
            raise DriverError("Not on a page")

        return getattr(self.last_response, item)

    def __getitem__(self, item) -> Any:
        if not self.last_response:
            raise DriverError("Not on a page")

        return self.last_response[item]

    def __str__(self) -> str:
        last_resp_str = str(self.last_response) if self.last_response else "unbound"
        return f"<activesoup.driver.Driver[{last_resp_str}]>"
