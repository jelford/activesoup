from functools import lru_cache
import requests
import html5lib
from xml.etree import ElementTree
from activesoup import response
import logging

log = logging.getLogger(__name__)

_namespaces = [
    'http://www.w3.org/1999/xhtml'
]


def _strip_namespace(etree):
    if type(etree.tag) != type(_strip_namespace):
        # For comments, the tag comes through as a function that, when invoked, returns the element.
        for ns in _namespaces:
            etree.tag = etree.tag.replace(f'{{{ns}}}', '')
    for c in etree:
        _strip_namespace(c)
    return etree


class Resolver:

    def __init__(self, driver):
        self._driver = driver

    def resolve(self, response):
        parsed = html5lib.parse(response.content)
        return BoundTag(self._driver, response, _strip_namespace(parsed))


class BoundTag(response.Response):

    def __init__(self, driver, raw_response, et):
        response.Response.__init__(self, raw_response)
        self._driver = driver
        self._et = et

    @lru_cache(maxsize=1024)
    def __getattr__(self, item):
        e = self._find(f'.//{item}')
        if e is not None:
            return e
        raise AttributeError(f'{type(self)} has no attribute {item}')

    @lru_cache(maxsize=1024)
    def __getitem__(self, attr):
        return self._et.attrib[attr]

    def find_all(self, tagname):
        return [
            get_bound_tag_factory(tagname)(self._driver, self._raw_response, e)
            for e in self._et.findall(f'.//{tagname}')
        ]

    @lru_cache(maxsize=1024)
    def find(self, xpath):
        return self._find(xpath)

    def text(self):
        return self._et.text

    def _find(self, xpath):
        e = self._et.find(xpath)
        if e is None:
            log.debug(f'searched a {type(self)} for:', xpath)
            log.debug('could have found:')
            for c in self._et:
                log.debug(c.tag, c.attrib)
            return None

        bound_tag = get_bound_tag_factory(e.tag)(
            self._driver, self._raw_response, e)
        return bound_tag


class BoundForm(BoundTag):

    def submit(self, data: dict, suppress_unspecified=False):
        try:
            action = self._et.attrib['action']
        except KeyError:
            action = self._raw_response.request.url
        try:
            method = self._et.attrib['method']
        except KeyError:
            method = 'POST'

        to_submit = {}
        if not suppress_unspecified:
            for i in self.find_all('input'):
                log.debug('Found: ', i)
                try:
                    to_submit[i['name']] = i['value']
                except KeyError:
                    pass

        to_submit.update(data)

        req = requests.Request(method=method, url=action, data=to_submit)
        return self._driver.do(req)


class BoundTagFactory:

    def __call__(self, driver, session: requests.Session, element: ElementTree):
        pass


def get_bound_tag_factory(tagname: str) -> BoundTagFactory:
    return {
        'form': BoundForm
    }.get(tagname, BoundTag)


class TagSearchError(RuntimeError):
    pass
