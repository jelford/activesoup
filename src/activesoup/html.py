from functools import lru_cache
from typing import Callable, Dict, List, Optional, Any, cast
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import tostring as et_str

import html5lib
import requests

import activesoup


_namespaces = ["http://www.w3.org/1999/xhtml"]


def _strip_namespace(etree: Element) -> Element:
    if type(etree.tag) != type(_strip_namespace):
        # For comments, the tag comes through as a function that, when invoked, returns the element.
        for ns in _namespaces:
            etree.tag = etree.tag.replace(f"{{{ns}}}", "")
    for c in etree:
        _strip_namespace(c)
    return etree


class BoundTag(activesoup.Response):
    """A ``BoundTag`` represents a single node in an HTML document.
    
    When a new HTML page is opened by the :py:class:`activesoup.Driver`,
    the page is parsed, and a new ``BoundTag`` is created, which is a
    handle to the top-level ``<html>`` element. 

    ``BoundTag`` provides convenient access to data in the page:    
    
    Via field-style find operation (inspired by BeautifulSoup):

        >>> page = html_page('<html><body><a id="link">link-text</a></body></html>')
        >>> page.a.text()
        'link-text'

    Via dictionary-stype attribute lookup:

        >>> page.a["id"]
        'link'
    
    A ``BoundTag`` wraps an :py:class:`xml.etree.ElementTree.Element`,
    providing shortcuts for common operations. The underlying ``Element`` can 
    be accessed via :py:meth:`etree <BoundTag.etree>`. When child elements are 
    accessed via those helpers, they are also wrapped in a ``BoundTag`` object.

    Note: a ``BoundTag`` object is created internally by the
    :py:class:`activesoup.Driver` - you will generally not need to
    construct one directly.
    """
    def __init__(
        self,
        driver: "activesoup.Driver",
        raw_response: requests.Response,
        element: Element,
    ) -> None:
        super().__init__(raw_response, "text/html")
        self._driver = driver
        self._et = element

    @lru_cache(maxsize=1024)
    def __getattr__(self, item: str) -> "BoundTag":
        e = self._find(f".//{item}")
        if e is not None:
            return e
        raise AttributeError(f"{type(self)} has no attribute {item}")

    @lru_cache(maxsize=1024)
    def __getitem__(self, attr: str) -> str:
        return self._et.attrib[attr]

    def find_all(self, element_matcher: str) -> List["BoundTag"]:
        """Find all matching elements on the current page

        :param str element_matcher: match expression to be used.
        :rtype: List[BoundTag]

        The match expression is made relative (by prefixing with ``.//``) and
        then forwarded to :py:meth:`etree's findall <python.xml.etree.ElementTree.Element.findall>`
        on the parsed ``Element``.

        Note that the general power of :py:mod:`xml.etree`'s XPath support is available, so
        filter expressions work too:

        >>> page = html_page('<html><body><a class="uncool">first link</a><a class="cool">second link</a></body></html>')
        >>> links = page.find_all('a')
        >>> links[0].text()
        'first link'
        >>> links[1].text()
        'second link'

        >>> cool_links = page.find_all('a[@class="cool"]')
        >>> len(cool_links)
        1
        >>> cool_links[0].text()
        'second link'

        ``find_all`` is a shortcut for ``.etree().findall()`` with a relative path:

        .. code-block::
        
            # The following are equivalent:
            tag.find_all("a")
            tag.etree().findall(".//a")
        
        """
        return [
            _get_bound_tag_factory(element_matcher)(self._driver, self._raw_response, e)
            for e in self._et.findall(f".//{element_matcher}")
        ]

    @lru_cache(maxsize=1024)
    def find(self, xpath: str = None, **kwargs) -> Optional["BoundTag"]:
        """Find a single element matching the provided xpath expression
        
        :param str xpath: xpath expression that will be forwarded to :py:meth:`etree's find <python.xml.etree.ElementTree.Element.find>`
        :param kwargs: Optional dictionary of attribute values. If present, 
            ``activesoup`` will append attribute filters to the XPath expression
        :rtype: Optional[BoundTag]

        Note that unlike :py:meth:`find_all`, the path is not first made relative.

        >>> page = html_page('<html><body><input type="text" name="first" /><input type="checkbox" name="second" /></body></html>')
        >>> page.find(".//input", type="checkbox")["name"]
        'second'

        The simplest use-case, of returning the first matching item for a
        particular tag, can be done via the field-stype find shortcut:

        >>> first_input = page.input
        >>> first_input["name"]
        'first'

        ``find`` is a shortcut for ``.etree().find()``:

        .. code-block:: 

            # The following are equivalent except that the returned value is wrapped in a BoundTag
            page.find('input', type="checkbox")
            page.find('input[@type="checkbox"]')
            page.etree().find('input[@type="checkbox"]')

            # The following are equivalent except that the returned value is wrapped in a BoundTag
            page.find('.//input')
            page.input
        """
        return self._find(xpath, **kwargs)

    def text(self) -> Optional[str]:
        """Access the text content of an HTML node
        
        :rtype: Optional[str]

        >>> page = html_page('<html><body><p>Hello world</p></body></html>')
        >>> p = page.p
        >>> p.text()
        'Hello world'

        ``text`` is a shortcut fro ``.etree().text``:

        .. code-block::

            # The following are equivalent:
            p.text()
            p.etree().text
        """
        return self._et.text

    def html(self) -> bytes:
        """Render this element's HTML as bytes

        :rtype: bytes

        The output is generated from the parsed HTML structure, as interpretted by ``html5lib``. 
        ``html5lib`` is how ``activesoup`` interprets pages in the same way as the browser would, 
        and that might mean making some changes to the structure of the document - for example, 
        if the original HTML contained errors.
        """
        return et_str(self._et)

    def attrs(self) -> Dict[str, str]:
        return self._et.attrib

    def etree(self) -> Element:
        """Access the wrapped :py:class:`etree.Element <xml.etree.ElementTree.Element>` object

        The other methods on this class class are generally shortcuts to
        functionality provided by the underlying ``Element`` - with the
        difference that where applicable they wrap the results in a new
        ``BoundTag``.

        :rtype: Element
        """
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
    """A ``BoundForm`` is a specialisation of the ``BoundTag`` class, returned
    when the tag is a ``<form>`` element.
    
    ``BoundForm`` adds the ability to submit forms to the server.
    
    >>> d = activesoup.Driver()
    >>> page = d.get("https://github.com/jelford/activesoup/issues/new")
    >>> f = page.form
    >>> page = f.submit({"title": "Misleading examples", "body": "Examples appear to show interactions with GitHub.com but don't reflect GitHub's real page structure"})
    >>> page.url
    'https://github.com/jelford/activesoup/issues/1'
    
    
    """
    def submit(
        self, data: Dict, suppress_unspecified: bool = False
    ) -> "activesoup.Driver":
        """Submit the form to the server
        
        :param Dict data: The values that should be provided for the various 
            fields in the submitted form. Keys should correspond to the form
            inputs' ``name`` attribute, and may be simple string values, or
            lists (in the case where a form input can take several values)
        :param bool suppress_unspecified: If False (the default), then
            ``activesoup`` will augment the ``data`` parameter to include the
            values of fields that are:
            
            - not specified in the ``data`` parameter
            - present with default values in the form as it was presented to
              us.

            The most common use-cases for this is to pick up fields with
            ``type="hidden"`` (commonly used for CSRF protection) or fields
            with ``type="checkbox"`` (commonly some default values are ticked).

        If the form has an ``action`` attribute specified, then the form will
        be submitted to that URL. If the form does not specify a ``method``,
        then ``POST`` will be used as a default.
        """
        try:
            action = self._et.attrib["action"]
        except KeyError:
            action = cast(str, self._raw_response.request.url)
        try:
            method = self._et.attrib["method"]
        except KeyError:
            method = "POST"

        to_submit: Dict[str, Any] = {}
        if not suppress_unspecified:
            for i in self.find_all("input"):
                type = i.attrs().get("type", "text")

                if type in {"checkbox", "radio"}:
                    should_take_value = i.attrs().get("checked") is not None
                else:
                    should_take_value = True

                if should_take_value:
                    try:
                        if type != "checkbox":
                            to_submit[i["name"]] = i["value"]
                        else:
                            value = to_submit.get(i["name"])
                            if value is None:
                                value = []

                            value.append(i["value"])
                            to_submit[i["name"]] = value
                    except KeyError:
                        pass

        to_submit.update(data)
        req = requests.Request(method=method, url=action, data=to_submit)
        return self._driver._do(req)


_BoundTagFactory = Callable[["activesoup.Driver", requests.Response, Element], BoundTag]


def resolve(driver: "activesoup.Driver", response: requests.Response) -> BoundTag:
    parsed: Element = html5lib.parse(response.content)
    return BoundTag(driver, response, _strip_namespace(parsed))


def _get_bound_tag_factory(tagname: str) -> _BoundTagFactory:
    return {"form": BoundForm}.get(tagname, BoundTag)

