.. _getting-started:

Getting Started
===============

What are we going to do?
------------------------

For this section, we'll use a form on `httpbin`_ as an example. You can
start a local copy of ``httpbin`` with:

.. code-block::

    docker run -p 8080:80 kennethreitz/httpbin

.. _httpbin: https://httpbin.org

If you don't have docker, you can follow along all the same - just 
swap ``http://localhost:8080`` for ``https://httpbin.org``.

Once that's started, open up a browser to http://localhost:8080/forms/post. You'll
see a basic HTML form with a few fields relating to a pizza order. Go ahead and fill
some values in, then hit the ``Submit order`` button at the bottom of the screen.
From there, you should see a JSON document returned, with some details about your
order. The JSON document look some thing like this:

.. code-block::

    {
        "args": {}, 
        "data": "", 
        "files": {}, 
        "form": {
            "comments": "Pizza is delicious", 
            "custemail": "pizza-lover@example.com", 
            "custname": "John Doe", 
            "custtel": "111-PIZZA", 
            "delivery": "12:45", 
            "size": "large", 
            "topping": [
                "bacon", 
                "cheese"
            ]
        }, 
        "headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", 
            "Accept-Encoding": "gzip, deflate, br", 
            ...
        }, 
        "json": null, 
        "origin": "84.67.72.8", 
        "url": "https://httpbin.org/post"
    }

What we're going to do in the rest of this Getting Started guide is just the same thing, in code. We'll:

1. Create a :py:class:`activesoup.Driver` object, which will be like our browser
2. Navigate the ``Driver`` to the form
3. Inspect the page to see what fields are available
4. Submit the form with a pizza order

Fetching a page
---------------

The starting point for working with ``activesoup`` is the :py:class:`activesoup.Driver` 
class. You can instantiate a ``Driver`` object as follows:

.. code-block::

    import activesoup
    d = activesoup.Driver()

Now we're ready to fetch a page:

.. code-block::

    page = d.get("http://localhost:8080/forms/post")

We can see all the inputs available on the page using :py:meth:`find_all <activesoup.html.BoundTag.find_all>`:

.. code-block::

    inputs = page.find_all('input')    # 1
    for i in inputs:
        print(i['name'])               # 2

Try it now! You should see output like the following:

.. code-block::

    custname
    custtel
    custemail
    size
    size
    size
    topping
    topping
    topping
    topping
    delivery

What happened here?

1. The ``page`` returned by ``d.get(...)`` represents the ``Driver`` after it has transitioned to the given page. 
In our case, the ``Driver`` is now on a normal HTML webpage. When a ``Driver`` is on an HTML webpage, we can
query it for elements on the page using the :py:meth:`find_all <activesoup.html.BoundTag.find_all>` method.
``find_all`` takes the name of the HTML tag and returns all instances of that tag that it can find. We'll see
later that ``find_all`` can be used to search only parts of the page, and can have filters applied to narrow down
the results further.

2. Having found our inputs, we can access their attributes using Python's dictionary-lookup syntax. In the case
of form inputs, they should all have a name, so that's what we print out.

Extracting data from the page
-----------------------------

You might have noticed in the previous section that some form elements are repeated. Take a look at the original
HTML (right-click and "Inspect" in your browser), and you'll see what's going on: the ``size`` and 
``topping`` elements do have several corresponding ``<input>`` elements. Here's the section for ``size``:

.. code-block::

    <fieldset>
        <legend> Pizza Size </legend>
        <p><label> <input type="radio" name="size" value="small"> Small </label></p>
        <p><label> <input type="radio" name="size" value="medium"> Medium </label></p>
        <p><label> <input type="radio" name="size" value="large"> Large </label></p>
    </fieldset>

In this section we'll see:

- How you can enumerate the different options for ``size`` with ``activesoup``
- How you can get the raw HTML you see above

Enumerating the sizes
^^^^^^^^^^^^^^^^^^^^^

How can we see those options with ``activesoup``? Notice the ``value`` attribute. When you select one of these
options and hit "Submit order" in your browser, it sends only the selected value over to the website. It knows
they go together, because they have the same name. So, let's enumerate all the possible values for inputs with
the name "size":


.. code-block::

    pizza_size_inputs = page.find_all('input[@name="size"]')    # 1
    
    for s in pizza_size_inputs:
        print(s['value'])      # small, medium, large           # 2

1. We're using a more advanced form of :py:meth:`find_all <activesoup.html.BoundTag.find_all>` here. 
``find_all`` is implemented using Python's built-in :py:mod:`xml.etree.ElementTree`:

    - Any HTML page is parsed as an :py:class:`xml.etree.ElementTree.Element`
    - ``find_all`` is a shortcut to the ``Element``'s :py:meth:`xml.etree.ElementTree.Element.findall` method,
      searching against all children of the current element (in this case, the whole page). Any filter syntax that
      would work with ``Element.findall`` will work here.

2. ``s['value']`` is doing exactly the same thing as ``i['name']`` in the previous section: it looks up the ``value``
attribute of the HTML element. 

    - Now we know that `page` is implemeted by passing requests through to an :py:class:`xml.etree.ElementTree.Element`,
      we can guess that ``s['value']`` is implemented in a similar way to ``find_all``: it's just a shortcut to :py:meth:`xml.etree.ElementTree.Element.attrs``.

We've covered an important aspect of how ``activesoup`` works here: the basic idea is to provide a convenient
way to access existing (and well-known) ways of doing things. When we work with HTML pages, ``activesoup`` is
just providing a thin wrapper around Python's built-in ``Element``.

Showing the whole ``<fieldset>``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Armed with the knowledge that our ``page`` is a ``ElementTree.Element``, we can guess that ``ElementTree``'s powerful
query API is available to us. We'd be guessing right! We can use the :py:meth:`find <activesoup.html.BoundTag.find>`
method to perform advanced queries. First, let's see what we're looking for:

.. code-block::

    print(", ".join((f'"{l.text()}"' for l in page.find_all("fieldset/legend")))) 

    # Note surrounding spaces
    # " Pizza Size ", " Pizza Toppings "     

.. code-block::

    sizes_fieldset = page.find('.//fieldset[legend=" Pizza Size "]')   # 1
    html = sizes_fieldset.html()                                       # 2
    print(html.decode())                                               # 3
    
    # <fieldset>
    #     <legend> Pizza Size </legend>
    #     <p><label> <input type="radio" name="size" value="small" /> Small </label></p>
    #     <p><label> <input type="radio" name="size" value="medium" /> Medium </label></p>
    #     <p><label> <input type="radio" name="size" value="large" /> Large </label></p>
    #     </fieldset>

Here, we've extracted the HTML snippet we found by inspecting the element in the browser.

1. ``find`` accepts an `XPath query <https://docs.python.org/3/library/xml.etree.elementtree.html#xpath-support>`_
   ``ElementTree``'s XPath support is a little limited, but still very useful - you can find all the details on the
   official documentation page.
2. We can extract the raw HTML from any element by querying its :py:meth:`.html() <activesoup.html.BoundTag.html>` method. 
   A couple of points to note:

    - Since the top-level page is an element too, we could have used the same method to get the raw HTML of the whole page too.
    - The string here is generated from the *parsed* HTML. ``activesoup`` interprets pages in the same way as the browser would,
      and that might mean making some changes to the structure of the document, if the original HTML contained errors. We will see
      later that it's still possible to get the original data that was received over the network.

3. Finally, we need to decode the data into textual form. This may change (to become automatic) in future releases.


Submitting a form
-----------------

Okay, it's about time we submitted our pizza order. In this section we'll:

#. Use the query methods we saw above to find the form object
#. Use what we learned about the page above to decide what fields to submit
#. See how to submit the form, like a browser would

Finding the form object
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block::

    form = page.find('.//form')

There's only one form on the page, so we can just use `find` to get it directly. Recall that the argument
is passed to :py:meth:`xml.etree.ElementTree.Element.find` and interpreted as an XPath query. Since this
is such a common operation, ``activesoup`` provides a shortcut. The following is equivalent:

.. code-block::

    form = page.form

Preparing our form submission
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Recall the list of fields from the previous section (this time with the duplicates removed):

.. code-block::

    for name in {f["name"] for f in page.find_all("input")}:
        print(name)

    # custname
    # custtel
    # custemail
    # size
    # topping
    # delivery

With that, we can prepare our list of values:

.. code-block::

    order = {
        "custname": "Pete Tsarlouvre",
        "custtel": "111-pizza-please",
        "size": "large",
        "topping": ["cheese", "mushroom"],
    }

And submit our order:

.. code-block::

    form.submit(order)


Reading a JSON response
-----------------------

Now that we've submitted our data, let's take a look at the response. Just like a browser, when you submit a form,
your ``activesoup.Driver`` it navigates to the new page. So, we can ask the ``Driver`` for details about the
page it's on now, having submitted our order.

.. code-block::

    print(d.url) # We've navigated away from the original page
    # http://localhost:8080/post

    print(type(d.last_response))
    # <class 'activesoup.json_response.JsonResponse'>

    print(d.json)
    # {'args': {}, ... }

    print(d.json['form']['custname'])
    # Pete Tsarlouvre

When we have a ``json`` response, we can access it with ``d.json``. This is another example of ``activesoup`` being
a thin wrapper on an underlying more well-known technology; in this case, we are accessing the :py:meth:`requests.Response.json`
method, which parses the ``json`` response directly from the server. Again, for convenience, ``activesoup`` provides
a shortcut:

.. code-block::

    d['form']['custname'] # .json can be freely ommitted. 



