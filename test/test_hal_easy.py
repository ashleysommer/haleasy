from unittest import TestCase
from haleasy import HALEasy, LinkNotFoundError
import json
import responses

sample_hal_root = {
    "_links": {
        "self": {
            "href": "/"
        },
        "curies": [
            {
                "name": "ex",
                "href": "http://ex/{rel}",
                "templated": True
            }
        ],
        "link1": {
            "href": "/link1path"
        },
        "ex:link2": {
            "href": "/link2path"
        },
        "other:link3": {
            "href": "/link3path"
        },
        "link4": {
            "href": "/link4path/{var}",
            "templated": True
        },
        "sample_hal_rel4": {
            "href": "/thing4"
        },
        "other:link5": [
            {
                "name": "link5name1",
                "href": "/link5path1"
            },
            {
                "name": "link5name2",
                "href": "/link5path2"
            }
        ],
    },
    "_embedded": {
        "sample_hal_rel1": {
            "a": "b",
            "c": "d",
            "i": "j",
            "_links": {
                "self": {
                    "href": "/thing1"
                }
            },
        },
        "sample_hal_rel2": [
            {
                "e": "f",
                "g": "h",
                "_links": {
                    "self": {
                        "href": "/thing2",
                        "name": "thing2"
                    }
                }
            },
            {
                "n": "o",
                "_links": {
                    "self": {
                        "href": "/thing3",
                        "name": "thing3"
                    }
                }
            },
        ],
        "sample_hal_rel4": {
            "p": "q",
            "_links": {
                "self": {
                    "href": "/thing4"
                }
            },
        },

    },
    "p1": 1,
    "p2": 2,
    "pTrue": True,
    "pStr": "abc"
}
sample_hal_root_json = json.dumps(sample_hal_root)

sample_hal_thing1 = {
    "a": "b",
    "c": "d",
    "i": "x",
    "k": "l",
    "_links": {
        "self": {
            "href": "/thing1"
        }
    }
}
sample_hal_thing1_json = json.dumps(sample_hal_thing1)

sample_hal_thing2 = {
    "e": "f",
    "g": "h",
    "_links": {
        "self": {
            "href": "/thing2"
        }
    }
}
sample_hal_thing2_json = json.dumps(sample_hal_thing2)

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


class test_hal_easy(TestCase):
    @responses.activate
    def test_properties_mocked(self):
        responses.add(responses.GET, 'http://api.test_domain/api_root',
                      body=sample_hal_root_json, status=200,
                      content_type='application/json')

        h = HALEasy('http://api.test_domain/api_root')
        self.assertEqual(h['p1'], 1)
        self.assertRaises(AttributeError, getattr, h, 'nonexistentproperty')

    @responses.activate
    def test_haleasy_object_properties(self):
        responses.add(responses.GET, 'http://api.test_domain/api_root',
                      body=sample_hal_root_json, status=200,
                      content_type='application/json')

        h = HALEasy('http://api.test_domain/api_root')
        self.assertEqual(h.host, 'http://api.test_domain')
        self.assertEqual(h.url, 'http://api.test_domain/api_root')
        self.assertFalse(h.is_preview)

    def test_haleasy_object_properties_from_str(self):
        h = HALEasy('http://api.test_domain/api_root', json_str=sample_hal_root_json)
        self.assertEqual(h.host, 'http://api.test_domain')
        self.assertEqual(h.url, 'http://api.test_domain/api_root')
        self.assertFalse(h.is_preview)

    def test_properties_json_str(self):
        h = HALEasy('http://ex.com/', json_str=sample_hal_root_json)
        self.assertEqual(h['p1'], 1)

    @responses.activate
    def test_links(self):
        responses.add(responses.GET, 'http://api.test_domain/api_root',
                      body=sample_hal_root_json, status=200,
                      content_type='application/json')
        h = HALEasy('http://api.test_domain/api_root')

        self.assertEqual(len(list(h.links(rel='nonexistentrel'))), 0)  # we get a generator yielding nothing

        for l in h.links(rel='nonexistentrel'):  # we can iterate over the empty generator
            raise Exception('We should not reach this part of the loop')

        l = list(h.links(rel='other:link5'))
        self.assertEqual(len(l), 2)
        for i, d in enumerate([
            {
                "name": "link5name1",
                "href": "/link5path1",
            },
            {
                "name": "link5name2",
                "href": "/link5path2",
            }
        ]):
            self.assertDictEqual(d, l[i].as_object())
        self.assertDictEqual(h.link(rel='other:link5').as_object(), {
            "name": "link5name1",
            "href": "/link5path1",
        })
        self.assertEqual(h.link(rel='other:link3').href, "/link3path")  # we get a single object
        self.assertRaises(LinkNotFoundError, h.link, rel='nonexistentrel')

    @responses.activate
    def test_haltalk_root(self):
        responses.add(responses.GET, 'http://haltalk.herokuapp.com.test_domain/',
                      body=haltalk_root, status=200,
                      content_type='application/json')

        h = HALEasy('http://haltalk.herokuapp.com.test_domain')
        self.assertEqual(h.link(rel=u'self')['href'], u'/')
        self.assertEqual(h.link(rel=u'http://haltalk.herokuapp.com/rels/users')['href'], u'/users')
        self.assertEqual(h.link(rel=u'http://haltalk.herokuapp.com/rels/me')['href'], u'/users/{name}')
        self.assertEqual(h.link(rel=u'http://haltalk.herokuapp.com/rels/me')['templated'], True)

    @responses.activate
    def test_haltalk_root_with_curies(self):
        responses.add(responses.GET, 'http://haltalk.herokuapp.com.test_domain/',
                      body=haltalk_root, status=200,
                      content_type='application/json')

        h = HALEasy('http://haltalk.herokuapp.com.test_domain')
        self.assertEqual(h.link(rel=u'self')['href'], u'/')
        self.assertEqual(h.link(rel=u'ht:users')['href'], u'/users')
        self.assertEqual(h.link(rel=u'ht:me')['href'], u'/users/{name}')
        self.assertEqual(h.link(rel=u'ht:me')['templated'], True)

    @responses.activate
    def test_haltalk_create_user(self):
        responses.add(responses.GET, 'http://haltalk.herokuapp.com.test_domain/',
                      body=haltalk_root, status=200,
                      content_type='application/json')

        responses.add(responses.POST, 'http://haltalk.herokuapp.com.test_domain/signup',
                      body='', status=201,
                      adding_headers={'Location': 'http://haltalk.herokuapp.com.test_domain/users/aaa'},
                      content_type='application/json')

        responses.add(responses.GET, 'http://haltalk.herokuapp.com.test_domain/users/aaa',
                      body=haltalk_get_user_aaa, status=200,
                      content_type='application/json')

        h = HALEasy('http://haltalk.herokuapp.com.test_domain')
        user = h.link(rel='ht:signup').follow(method='POST', data={'username': 'aaa', 'password': 'bbb'})
        self.assertEqual(user['username'], 'aaa')

    @responses.activate
    def test_haltalk_get_me_aaa(self):
        responses.add(responses.GET, 'http://haltalk.herokuapp.com.test_domain/',
                      body=haltalk_root, status=200,
                      content_type='application/json')

        responses.add(responses.GET, 'http://haltalk.herokuapp.com.test_domain/users/aaa',
                      body=haltalk_get_user_aaa, status=200,
                      content_type='application/json')

        h = HALEasy('http://haltalk.herokuapp.com.test_domain')
        user = h.link(rel='ht:me').follow(name='aaa')
        self.assertEqual(user['username'], 'aaa')

    @responses.activate
    def test_embedded_rels_in_links(self):
        responses.add(responses.GET, 'http://api.test_domain/api_root',
                      body=sample_hal_root_json, status=200,
                      content_type='application/json')
        responses.add(responses.GET, 'http://api.test_domain/thing1',
                      body=sample_hal_thing1_json, status=200,
                      content_type='application/json')
        h = HALEasy('http://api.test_domain/api_root')
        self.assertEqual(h.host, 'http://api.test_domain')
        for e in ('sample_hal_rel1', 'sample_hal_rel2'):
            found = False
            for l in h._link_list:
                if l.rel == e:
                    found = True
                    self.assertTrue(hasattr(l, 'preview'))
                    self.assertTrue(l.preview.link(rel='self'))
            self.assertTrue(found, msg='could not find rel %s' % e)
        h1 = h.link(rel="sample_hal_rel1").follow()
        self.assertTrue(h1.is_preview)  # h1 is an embedded resource
        self.assertEqual(h1['a'], 'b')
        self.assertEqual(h1['i'], 'j')  # h1['i'] has value 'j'
        self.assertEqual(h1['k'], 'l')  # 'k' not in embedded resource properties, HTTP GET performed
        self.assertFalse(h1.is_preview) # h1 is now not an embedded resource
        self.assertEqual(h1['i'], 'x')  # value of h1['i'] has changed to 'x'
        self.assertEqual(h1.preview['i'], 'j')  # old value of h1['i'] available here
        h1 = h.link(rel="sample_hal_rel1").follow()

        h2 = h.link(rel="sample_hal_rel2", name="thing2").follow()
        self.assertEqual(h2['e'], 'f')

