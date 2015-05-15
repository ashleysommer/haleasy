from unittest import TestCase
from haleasy import HALEasy
import responses


class TestHaleasyHaltalk(TestCase):
    haltalk_root = '''{
        "_links": {
            "self": {
                "href":"/"
            },
            "curies": [
                {
                    "name": "ht",
                    "href": "http://haltalk.herokuapp.com/rels/{rel}",
                    "templated": true
                }
            ],
            "ht:users": {
                "href":"/users"
            },
            "ht:signup": {
                "href":"/signup"
            },
            "ht:me": {
                "href": "/users/{name}",
                "templated":true
            },
            "ht:latest-posts": {
                "href":"/posts/latest"
            }
        },
        "welcome": "Welcome to a haltalk server.",
        "hint_1": "You need an account to post stuff..",
        "hint_2": "Create one by POSTing via the ht:signup link..",
        "hint_3": "Click the orange buttons on the right to make POST requests..",
        "hint_4": "Click the green button to follow a link with a GET request..",
        "hint_5": "Click the book icon to read docs for the link relation."
    }'''

    haltalk_get_user_aaa = '''{
        "_links": {
            "self": {
                "href": "/users/aaa"
            },
            "curies": [
                {
                    "name": "ht",
                    "href": "http://haltalk.herokuapp.com/rels/{rel}",
                    "templated": true
                },
                {
                    "name": "bla",
                    "href": "http://haltalk.herokuapp.com/rels/{rel}",
                    "templated": true
                }
            ],
            "ht:posts": {
                "href": "/users/aaa/posts"
            }
        },
        "username": "aaa",
        "bio": null,
        "real_name": null
    }'''

    def setUp(self):
        responses.reset()
        responses.add(responses.GET, 'http://haltalk.herokuapp.com.test_domain/',
                      body=self.haltalk_root, status=200,
                      content_type='application/json')
        responses.add(responses.POST, 'http://haltalk.herokuapp.com.test_domain/signup',
                      body='', status=201,
                      adding_headers={'Location': 'http://haltalk.herokuapp.com.test_domain/users/aaa'},
                      content_type='application/json')
        responses.add(responses.GET, 'http://haltalk.herokuapp.com.test_domain/users/aaa',
                      body=self.haltalk_get_user_aaa, status=200,
                      content_type='application/json')


    @responses.activate
    def test_haltalk_root(self):
        h = HALEasy('http://haltalk.herokuapp.com.test_domain')
        self.assertEqual(h.link(rel=u'self')['href'], u'/')
        self.assertEqual(h.link(rel=u'http://haltalk.herokuapp.com/rels/users')['href'], u'/users')
        self.assertEqual(h.link(rel=u'http://haltalk.herokuapp.com/rels/me')['href'], u'/users/{name}')
        self.assertEqual(h.link(rel=u'http://haltalk.herokuapp.com/rels/me')['templated'], True)

    @responses.activate
    def test_haltalk_root_with_curies(self):
        h = HALEasy('http://haltalk.herokuapp.com.test_domain')
        self.assertEqual(h.link(rel=u'self')['href'], u'/')
        self.assertEqual(h.link(rel=u'ht:users')['href'], u'/users')
        self.assertEqual(h.link(rel=u'ht:me')['href'], u'/users/{name}')
        self.assertEqual(h.link(rel=u'ht:me')['templated'], True)

    @responses.activate
    def test_haltalk_create_user(self):
        h = HALEasy('http://haltalk.herokuapp.com.test_domain')
        user = h.link(rel='ht:signup').follow(method='POST', data={'username': 'aaa', 'password': 'bbb'})
        self.assertEqual(user['username'], 'aaa')

    @responses.activate
    def test_haltalk_get_me_aaa(self):
        h = HALEasy('http://haltalk.herokuapp.com.test_domain')
        user = h.link(rel='ht:me').follow(name='aaa')
        self.assertEqual(user['username'], 'aaa')