activesoup
==========

.. image:: https://github.com/jelford/activesoup/workflows/Build/badge.svg
    :target: https://github.com/jelford/activesoup/actions?query=workflow%3Abuild

.. image:: https://img.shields.io/pypi/v/activesoup.svg?maxAge=3600
    :target: https://pypi.python.org/pypi?:action=display&name=activesoup

A simple library for interacting with the web from python

Description
-----------

``activesoup`` combines familiar python web capabilities for convenient
headless "browsing" functionality:

* Modern HTTP support with `requests <http://www.python-requests.org/>`__ -
  connection pooling, sessions, ...
* Convenient access to the web page with an interface inspired by
  `beautifulsoup <https://www.crummy.com/software/BeautifulSoup/>`__ -
  convenient HTML navigation.
* Robust HTML parsing with
  `html5lib <https://html5lib.readthedocs.org/en/latest/>`__ - parse the web
  like browsers do.

Use cases
---------

Consider using ``activesoup`` when:

* You've already checked out the `requests-html <https://github.com/kennethreitz/requests-html>`__
* You need to actively interact with some web-page from Python (e.g. submitting
  forms, downloading files)
* You don't control the site you need to interact with (if you do, just make an
  API).
* You don't need javascript support (you'll need
  `selenium <http://www.seleniumhq.org/projects/webdriver/>`__ or
  `phantomjs <http://phantomjs.org/>`__).

Usage examples
--------------

Log into a website, and download a CSV file that's access-protected:

.. code-block:: python

    >>> import activesoup

    >>> # Start a session
    >>> d = activesoup.Driver()

    >>> page = d.get("https://httpbin.org/forms/post")

    >>> # conveniently access elements, inspired by BeautifulSoup
    >>> form = page.form

    >>> # get the power of raw xpath search too
    >>> form.find('.//input[@name="size"]')
    BoundTag<input>
    >>> # any element, searching by attribute
    >>> form.find('.//*', name="size")
    BoundTag<input>
    >>> # or just search by attribute
    >>> form.find(name="size")
    BoundTag<input>

    >>> # inspect element attributes
    >>> print([i['name'] for i in form.find_all('input')])
    ['custname', 'custtel', 'custemail', 'size', 'size', 'size', 'topping', 'topping', 'topping', 'topping', 'delivery']

    >>> # work actively with objects on the page
    >>> r = form.submit({"custname": "john", "size": "small"})

    >>> # responses parsed and ready based on content type
    >>> r.keys()
    dict_keys(['args', 'data', 'files', 'form', 'headers', 'json', 'origin', 'url'])
    >>> r['form']
    {'custname': 'john', 'size': 'small', 'topping': 'mushroom'}

    >>> # access the underlying requests.Session too
    >>> d.session
    <requests.sessions.Session object at 0x7f283dc95700>

    >>> # log in with cookie support
    >>> d.get('https://httpbin.org/cookies/set/foo/bar')
    >>> d.session.cookies['foo']
    'bar'
