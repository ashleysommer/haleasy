HALEasy
-------

A very simple and short HAL client designed with the following goals in mind:

* Clear from the code what actions are happening.  There are no implicit names or actions so it is always clear to
  someone reading code that uses this class what the class will do.
* Reuse existing mature libraries.  All HAL processing is done by the dougrain library, all HTTP processing by
  requests
* Easy access to full URL, scheme+host and path+query+fragment of the document
* Uniform access to links regardless of whether there is a single one of a kind or more than one.  You can always
  iterate over even single instances of a rel
* No distinction between embedded and linked resources as far as client usage goes.  Although HAL allows embedded
  to have different representations from the actual resource, this is counter o the use as a 'caching' pattern so
  this client assumes embedded resources are identical to the original resources

It is essential to treat HALEasy and HALEasyLink objects as read only.  The constructors set up several attributes which will be
wrong if altered or other parts of the object are altered.

Usage
-----

    from haleasy import HALEasy
    >>> h = HALEasy('http://haltalk.herokuapp.com/')
    
    >>> list(h.links())
    [{u'href': u'/users', 'rel': u'http://haltalk.herokuapp.com/rels/users'},
     {u'href': u'/', 'rel': u'self'},
     {u'href': u'/users/{name}', 'rel': u'http://haltalk.herokuapp.com/rels/me', u'templated': True},
     {u'href': u'/posts/latest', 'rel': u'http://haltalk.herokuapp.com/rels/latest-posts'},
     {u'href': u'/signup', 'rel': u'http://haltalk.herokuapp.com/rels/signup'}]
     
    >>> h.properties()
    {u'hint_1': u'You need an account to post stuff..',
     u'hint_2': u'Create one by POSTing via the ht:signup link..',
     u'hint_3': u'Click the orange buttons on the right to make POST requests..',
     u'hint_4': u'Click the green button to follow a link with a GET request..',
     u'hint_5': u'Click the book icon to read docs for the link relation.',
     u'welcome': u'Welcome to a haltalk server.'}


    >>> list(h.links(rel='http://haltalk.herokuapp.com/rels/signup'))
    [{u'href': u'/signup', 'rel': u'http://haltalk.herokuapp.com/rels/signup'}]
    
    >>> h.link(rel='http://haltalk.herokuapp.com/rels/signup')
    {u'href': u'/signup', 'rel': u'http://haltalk.herokuapp.com/rels/signup'}
    
    >>> u = h.link(rel='http://haltalk.herokuapp.com/rels/users').follow()
    >>> list(u.links(title='Fred Wilson'))
    [{u'href': u'/users/fred', 'rel': u'http://haltalk.herokuapp.com/rels/user', u'title': u'Fred Wilson'},
     {u'href': u'/users/ryan', 'rel': u'http://haltalk.herokuapp.com/rels/user', u'title': u'Fred Wilson'},
     {u'href': u'/users/joe', 'rel': u'http://haltalk.herokuapp.com/rels/user', u'title': u'Fred Wilson'},
     ...
    
    >>> s = h.link(rel='http://haltalk.herokuapp.com/rels/signup').follow(method='POST', data={'username': '7654321', 'password': '1234567'})
    >>> s.properties()
    {u'username': u'7654321', u'bio': None, u'real_name': None}
    >>> s.url
    'http://haltalk.herokuapp.com/users/7654321'
    >>> s.path
    '/users/7654321'
    >>> s.host
    'http://haltalk.herokuapp.com'
    
Defaults
-------------------

Any additional keyword params passed in to the HalEasy constructor are automatically passed through to the
requests.Session.send() method.  Default values are provided for the HTTP method (GET) and the Accept and Content-Type
headers (both application/json).  However in keeping with the design principle of least surprise, the keyword args
provided do not propagate across HALEasy instances.

To override these more generally, you should subclass HALEasy and provide new defaults:

    from haleasy import HALEasy
    class MyHALClass(HALEasy):
        DEFAULT_HEADERS = {'Accept': 'application/json',
                           'Content-Type': 'application/hal+json'}
        DEFAULT_METHOD = 'GET'

    >>> h = MyHALEasy('http://haltalk.herokuapp.com/')
    
    
   
    
