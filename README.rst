HALEasy
-------
A very simple and short HAL client designed with the following goals in mind:

-  Uniform access to lists of links regardless of whether there is a single one of a kind or more than one. You can always iterate over even single instances of a rel.
-  Uniform access to links by any property, not just the relation type.
-  Uniform access to embedded and linked resources.  Embedded resources are accessed through the .links() method just like linked resources are, but have a .is_preview property with value True.  If you attempt to access a nonexistent property of an embedded resource, HALEasy will fetch the full representation and try to satisfy the request from that.  If you wish, you can use the .preview property of the full resource to check for inconsistencies between the full and embedded resource representations.
-  Full access to the underlying capabilities of the Python requests library

Installation from PyPi
----------------------
::

    pip install haleasy


Installation from GitHub
------------------------
::

    git clone https://github.com/mattclarkdotnet/haleasy.git
    python setup.py install

Basic Usage
-----------
Create a HALEasy resource by fetching a URL:::

    from haleasy import HALEasy
    >>> h = HALEasy('http://haltalk.herokuapp.com/')

Get a dictionary of the resource properties:::

    >>> h.properties()
    {u'hint_1': u'You need an account to post stuff..',
     u'hint_2': u'Create one by POSTing via the ht:signup link..',
     u'hint_3': u'Click the orange buttons on the right to make POST requests..',
     u'hint_4': u'Click the green button to follow a link with a GET request..',
     u'hint_5': u'Click the book icon to read docs for the link relation.',
     u'welcome': u'Welcome to a haltalk server.'}

Get a list of the resource's links:::

    >>> h.links()
    [{u'href': u'/users', 'rel': u'http://haltalk.herokuapp.com/rels/users'},
     {u'href': u'/', 'rel': u'self'},
     {u'href': u'/users/{name}', 'rel': u'http://haltalk.herokuapp.com/rels/me', u'templated': True},
     {u'href': u'/posts/latest', 'rel': u'http://haltalk.herokuapp.com/rels/latest-posts'},
     {u'href': u'/signup', 'rel': u'http://haltalk.herokuapp.com/rels/signup'}]

Get a list of the relations of those links:::

    >>> h.rels()
    [u'http://haltalk.herokuapp.com/rels/users',
     u'self',
     u'http://haltalk.herokuapp.com/rels/me',
     u'http://haltalk.herokuapp.com/rels/latest-posts',
     u'http://haltalk.herokuapp.com/rels/signup']

List all the links with a given rel:::

    >>> h.links(rel='http://haltalk.herokuapp.com/rels/signup')
    [{u'href': u'/signup', 'rel': u'http://haltalk.herokuapp.com/rels/signup'}]

Find the first link with a given rel:::

    >>> h.link(rel='http://haltalk.herokuapp.com/rels/signup')
    {u'href': u'/signup', 'rel': u'http://haltalk.herokuapp.com/rels/signup'}

You can find links by any combination of properties:::

    >>> h.links(rel='http://haltalk.herokuapp.com/rels/me', templated=True)
    [{u'href': u'/users/{name}', 'rel': u'http://haltalk.herokuapp.com/rels/me', u'templated': True}]

Follow links by calling their .follow() method:::

    >>> u = h.link(rel='http://haltalk.herokuapp.com/rels/users').follow()
    >>> u.links(title='Fred Wilson')
    [{u'href': u'/users/fred', 'rel': u'http://haltalk.herokuapp.com/rels/user', u'title': u'Fred Wilson'},
     {u'href': u'/users/ryan', 'rel': u'http://haltalk.herokuapp.com/rels/user', u'title': u'Fred Wilson'},
     {u'href': u'/users/joe', 'rel': u'http://haltalk.herokuapp.com/rels/user', u'title': u'Fred Wilson'},
     ...

Non-GET requests
----------------
Provide method and data parameters to the .follow() method to perform non-GET requests:::

    >>> s = h.link(rel='http://haltalk.herokuapp.com/rels/signup').follow(method='POST', data={'username': '7654321', 'password': '1234567'})
    >>> s.properties()
    {u'username': u'7654321',
     u'bio': None,
     u'real_name': None}
    >>> s.url
    'http://haltalk.herokuapp.com/users/7654321'
    >>> s.path
    '/users/7654321'
    >>> s.host
    'http://haltalk.herokuapp.com'

Loading from a JSON string instead of a url
-------------------------------------------
You can provide a JSON string directly, but you also need to provide a URL::

    >>> haldoc = json.dumps({
        "_links": {
            "self": {
                "href": "/api_root"
            },
            "sample_hal_rel1": {
                "href": "/thing1"
            },
        },
        "p1": "v1"
    }
    >>> h = HALEasy('http://dummy.local/', json_str=haldoc)

Templated link URIs
-------------------
Fill in URI templates by providing additional parameters to the .follow() method:::

    >>> u2 = h.link(rel='ht:me').follow(name='fred')

Embedded resources
-------------------
Embedded resources are accessed in the same way as normal resources, but they have a .is_preview property set to True::

    >>> haldoc = json.dumps({
        "_links": {
            "self": {
                "href": "/api_root"
            },
            "sample_hal_rel1": {
                "href": "/thing1"
            },
        },
        "p1": "v1"
        "_embedded": {
            "sample_hal_rel1": {
                "a": "b",
                "_links": {
                    "self": {
                        "href": "/thing1",
                    }
                },
            }

    >>> h = HALEasy('http://dummy.local/', json_str=haldoc)
    >>> e = h.link(rel="sample_hal_rel1")
    >>> e.is_preview
    True

If you access a property of an embedded resource that is not defined, HALEasy will fetch the actual resource and try to give you the value from there:::

    >>> e.is_preview
    True
    >>> e['a']
    'b'
    >>> e['c']  # HalEasy wil fetch /thing1.  Assuming 'c' is a property of the full resource with value 'd' we will get:
    'd'
    >>> e.is_preview  # e is no longer a preview resource, as we fetched it from the server
    False


If a property has different values between the embedded and real resources, the real resource value overwrites the embedded resource value.

Anonymous embedded resources
----------------------------
If an embedded resource has a self link with no href then you can still find it by other properties of the self link, such as name.  If the embedded resource has no self link at all then it will be given a logical link with just {'href': ''} as its properties so that it is still accessible vie the .lonks() method of its parent document.  This pattern is useful iun HAL for things like transient form submission errors, where there is no persistent resource to link to.

Authentication and HTTP sessions
--------------------------------
HALEasy uses requests, so you can pass any arguments you like to the HALEasy constructor or to the .follow() method and they will be passed in to requests.Session.request():::

    >>> h = HALEasy('http://some.authenticated.server/api', auth=('uuu', 'ppp'))
    >>> from requests.auth import HTTPDigestAuth
    >>> h = HALEasy('http://some.authenticated.server/api', auth=HTTPDigestAuth('uuu', 'ppp'))

You can also create and pas in your own session objects:::

    >>> from requests import Session
    >>> mysession = Session()
    >>> mysession.auth = ('u', 'p')
    >>> h = HALEasy('http://some.authenticated.server/api', session=mysession)

If you do not pass in a session then HALEasy creates and uses one for the suration of any redirections required to manage an individual request

You need to keep passing your own session object in when repeating requests, as HALEasy does not know your true intent and so will not manage your sessions for you:::

    >>> mysession = Session()
    >>> mysession.auth = ('u', 'p')
    >>> h = HALEasy('http://some.authenticated.server/api', session=mysession)
    >>> h2 = h.link(rel='somerel').follow(session=mysession)

Changing Default Behaviour
--------------------------

Any additional keyword params passed in to the HalEasy constructor are automatically passed through to the requests.Session.send() method by the HTTP client.  Default values are provided for the HTTP method (GET) and the Accept and Content-Type headers (both application/json). However in keeping with the design principle of least surprise, the other keyword args provided do not propagate across HALEasy instances.  If you want them to propagate you should subclass HALHttpClient

    >>> from haleasy import HALEasy, HALHttpClient
    >>> class MyHttpClient(HALHttpClient):
    ...     DEFAULT_METHOD = 'POST'
    >>> class MyHALEasy(HALEasy):
    ...     HTTP_CLIENT_CLASS = MyHttpClient
    >>> h = MyHALEasy('http://haltalk.herokuapp.com/')


