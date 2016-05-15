from functools import lru_cache
import requests
import bs4
from activesoup import response


class Resolver:

    def __init__(self, driver):
        self._driver = driver

    def resolve(self, response):
        return BoundTag(self._driver, response,
                        bs4.BeautifulSoup(response.text, 'html5lib'))


class BoundTag(response.Response):

    def __init__(self, driver, raw_response, soup):
        response.Response.__init__(self, raw_response)
        self._driver = driver
        self._soup = soup

    @lru_cache(maxsize=1024)
    def __getattr__(self, item):
        soup_element = getattr(self._soup, item)
        if soup_element is not None and isinstance(soup_element, bs4.Tag):
            bound_tag = get_bound_tag_factory(item)(
                self._driver, self._raw_response, soup_element)
            return bound_tag
        else:
            return soup_element

    def __getitem__(self, attr):
        return self._soup[attr]

    def find_one(self, tagname, attrs=None):
        attrs = attrs or {}

        initial_candidates = self._soup.find_all(tagname)
        filtered_candidates = {c for c in initial_candidates if
                               all((c.has_attr(k) and c[k] == v for k, v in attrs.items()))}

        if len(filtered_candidates) > 1:
            raise TagSearchError('More than one element found matching search')
        elif not(filtered_candidates):
            raise TagSearchError('No element found matching search')
        else:
            for c in filtered_candidates:
                return get_bound_tag_factory(tagname)(
                    self._driver, self._raw_response, c)


class BoundForm(BoundTag):

    def submit(self, data: dict, suppress_unspecified=False):
        try:
            action = self._soup['action']
        except KeyError:
            action = self._raw_response.request.url
        try:
            method = self._soup['method']
        except KeyError:
            method = 'POST'

        to_submit = {}
        if not suppress_unspecified:
            for i in self._soup.find_all('input'):
                try:
                    to_submit[i['name']] = i['value']
                except KeyError:
                    pass

        to_submit.update(data)

        req = requests.Request(method=method, url=action, data=to_submit)
        return self._driver.do(req)


class BoundTagFactory:

    def __call__(self, driver, session: requests.Session, soup: bs4.BeautifulSoup):
        pass


def get_bound_tag_factory(tagname: str) -> BoundTagFactory:
    return {
        'form': BoundForm
    }.get(tagname, BoundTag)


class TagSearchError(RuntimeError):
    pass
