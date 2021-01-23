from functools import lru_cache
from typing import Dict, List, Optional
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import tostring as et_str

import html5lib
import requests
from typing_extensions import Protocol

from activesoup import response

from .protocols import Driver

_namespaces = ["http://www.w3.org/1999/xhtml"]


def _strip_namespace(etree: Element) -> Element:
    if type(etree.tag) != type(_strip_namespace):
        # For comments, the tag comes through as a function that, when invoked, returns the element.
        for ns in _namespaces:
            etree.tag = etree.tag.replace(f"{{{ns}}}", "")
    for c in etree:
        _strip_namespace(c)
    return etree


class BoundTag(response.Response):
    def __init__(
        self, driver: Driver, raw_response: requests.Response, et: Element
    ) -> None:
        response.Response.__init__(self, raw_response, "text/html")
        self._driver = driver
        self._et = et

    @lru_cache(maxsize=1024)
    def __getattr__(self, item: str) -> "BoundTag":
        e = self._find(f".//{item}")
        if e is not None:
            return e
        raise AttributeError(f"{type(self)} has no attribute {item}")

    @lru_cache(maxsize=1024)
    def __getitem__(self, attr: str) -> str:
        return self._et.attrib[attr]

    def find_all(self, tagname) -> List["BoundTag"]:
        return [
            _get_bound_tag_factory(tagname)(self._driver, self._raw_response, e)
            for e in self._et.findall(f".//{tagname}")
        ]

    @lru_cache(maxsize=1024)
    def find(self, xpath: str = None, **kwargs) -> Optional["BoundTag"]:
        return self._find(xpath, **kwargs)

    def text(self) -> Optional[str]:
        return self._et.text

    def html(self) -> bytes:
        return et_str(self._et)

    def attrs(self) -> Dict[str, str]:
        return self._et.attrib

    def etree(self) -> Element:
        return self._et

    def _find(self, xpath: str = None, **kwargs) -> Optional["BoundTag"]:
        if xpath is None:
            xpath = ".//*"

        if kwargs:
            xpath += "".join(f"[@{k}='{v}']" for k, v in kwargs.items())

        e = self._et.find(xpath)
        if e is None:
            return None

        bound_tag = _get_bound_tag_factory(e.tag)(self._driver, self._raw_response, e)
        return bound_tag

    def __repr__(self) -> str:
        return f"BoundTag[{self._et.tag}]"

    def __str__(self) -> str:
        return f"{self._et.tag}"


class BoundForm(BoundTag):
    def submit(self, data: Dict, suppress_unspecified: bool = False) -> Driver:
        try:
            action = self._et.attrib["action"]
        except KeyError:
            action = self._raw_response.request.url
        try:
            method = self._et.attrib["method"]
        except KeyError:
            method = "POST"

        to_submit = {}
        if not suppress_unspecified:
            for i in self.find_all("input"):
                try:
                    to_submit[i["name"]] = i["value"]
                except KeyError:
                    pass

        to_submit.update(data)

        req = requests.Request(method=method, url=action, data=to_submit)
        return self._driver.do(req)


class _BoundTagFactory(Protocol):
    def __call__(
        self, driver: Driver, session: requests.Session, element: Element
    ) -> BoundTag:
        ...


class Resolver:
    def __init__(self, driver: Driver) -> None:
        self._driver = driver

    def resolve(self, response) -> BoundTag:
        parsed: Element = html5lib.parse(response.content)
        return BoundTag(self._driver, response, _strip_namespace(parsed))


def _get_bound_tag_factory(tagname: str) -> _BoundTagFactory:
    return {"form": BoundForm}.get(tagname, BoundTag)


class TagSearchError(RuntimeError):
    pass
