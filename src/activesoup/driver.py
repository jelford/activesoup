import requests
from urllib.parse import urljoin
import activesoup.html
import activesoup.csv
import activesoup.response
import activesoup.json_response


class DriverError(RuntimeError):
    pass


class ContentResolver:

    def __init__(self):
        self._resolvers = {}

    def register(self, content_type, resolver):
        self._resolvers[content_type] = resolver

    def resolve(self, response):
        content_type = response.headers.get('Content-Type', None)
        if content_type is not None:
            for k, v in self._resolvers.items():
                if content_type.startswith(k):
                    return v.resolve(response)

        return activesoup.response.Response(response)


class Driver:

    def __init__(self):
        self.session = requests.Session()
        self.last_response = None
        self.content_resolver = ContentResolver()
        self.content_resolver.register(
            'text/html', activesoup.html.Resolver(self))
        self.content_resolver.register('text/csv', activesoup.csv)
        self.content_resolver.register(
            'application/json', activesoup.json_response)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def resolve_url(self, possibly_relative_url):
        current_url_str = self.url
        if not current_url_str:
            return possibly_relative_url

        return urljoin(current_url_str, possibly_relative_url)

    def get(self, url, **kwargs):
        return self.do(requests.Request(method='GET', url=url))

    def do(self, request: requests.Request):
        request.url = self.resolve_url(request.url)
        prepped = self.session.prepare_request(request)
        return self.handle_response(self.session.send(prepped))

    def handle_response(self, response: requests.Response):
        if response.status_code in range(300, 304):
            redirected_to = response.headers.get('Location', None)
            if not redirected_to:
                raise DriverError(
                    'Found a redirect, but no onward location given')
            return self.get(redirected_to)

        self.last_response = self.content_resolver.resolve(response)
        self._raw_response = response

        return self

    @property
    def url(self):
        return self.last_response.url if self.last_response is not None else None

    def __getattr__(self, item):
        if not self.last_response:
            raise DriverError('Not on a page')

        return getattr(self.last_response, item)

    def __getitem__(self, item):
        if not self.last_response:
            raise DriverError('Not on a page')

        return self.last_response[item]
