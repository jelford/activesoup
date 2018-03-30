activesoup
==========

.. image:: https://travis-ci.org/jelford/activesoup.svg?branch=master
    :target: https://travis-ci.org/jelford/activesoup

.. image:: https://img.shields.io/pypi/v/activesoup.svg?maxAge=2592000
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

* You've already checked out the very talented Kenneth Reitz's `requests-html <https://github.com/kennethreitz/requests-html>`__
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

    from activesoup import driver
    
    d = driver.Driver()
    login_page = d.get('https://my-site.com/login')
    login_form = login_page.form
    member_portal = login_form.submit({'username': secret_store['username'],
                        'password': secret_store['password']})

    if member_portal.response.status_code not in range(200, 300):
        raise RuntimeError("Couldn't log in")

    # Logged in now

    csv_report = d.get('/members_area/file.csv')
    csv_report.save_to('~/interesting_resport.csv')
