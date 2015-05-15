from unittest import TestCase
from haleasy import HALEasy, LinkNotFoundError, listify, make_preview_url
import json
import responses


class TestListify(TestCase):
    def test_listify(self):
        for example in [None, 1, 'foo']:
            self.assertEqual(listify(example), [example, ])
        for example in [[None], [1], ['foo']]:
            self.assertEqual(listify(example), example)
        for example in [[None, 1, 'foo'], [None, [1, 'foo']]]:
            self.assertEqual(listify(example), example)
        for example in [(1, 2), {1, 2}]:
            self.assertEqual(listify(example), [example, ])


class TestMakePreviewUrl(TestCase):
    def test_untrue_urlstring_returns_empty_string(self):
        for untrue_value in (0, '', None, [], False):
            self.assertEqual(make_preview_url(untrue_value, 'dummyhost.com'), '')

    def test_full_urls_are_unchanged(self):
        for teststring in ('http://',
                           'http://a',
                           'http://a.com',
                           'http://a.com/',
                           'http://a.com/foo',
                           'http://a.com/foo/bar?b&%c=4'):
            self.assertEqual(make_preview_url(teststring, 'http://dummyhost.com'), teststring)

    def test_relative_urls_are_prepended(self):
        for teststring in ('/foo',
                           '/foo/bar?b&%c=4'):
            self.assertEqual(make_preview_url(teststring, 'http://dummyhost.com'),
                             'http://dummyhost.com{}'.format(teststring))
        for teststring in ('foo',
                           'foo/bar?b&%c=4'):
            self.assertEqual(make_preview_url(teststring, 'http://dummyhost.com'),
                             'http://dummyhost.com/{}'.format(teststring))


class TestHalEasyPropertiesAndLinks(TestCase):
    sample_hal_root = {
        "_links": {
            "self": {
                "href": "/api_root"
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
                "href": "/link3path",
                "name": "thing3"
            },
            "link4": {
                "href": "/link4path/{var}",
                "templated": True
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
        "p1": 1,
        "p2": 2,
        "pTrue": True,
        "pStr": "abc"
    }
    sample_hal_root_json = json.dumps(sample_hal_root)

    def setUp(self):
        responses.reset()
        responses.add(responses.GET, 'http://api.test_domain/api_root',
                      body=self.sample_hal_root_json, status=200,
                      content_type='application/json')

    @responses.activate
    def test_properties(self):
        h = HALEasy('http://api.test_domain/api_root')
        self.assertEqual(h.host, 'http://api.test_domain')
        self.assertEqual(h.fetched_from, 'http://api.test_domain/api_root')
        self.assertEqual(h.doc.url(), 'http://api.test_domain/api_root')
        self.assertFalse(h.is_preview)
        self.assertEqual(h['p1'], 1)
        self.assertRaises(AttributeError, getattr, h, 'nonexistentproperty')

    def test_properties_json_str(self):
        h = HALEasy('http://ex.com/api_root', json_str=self.sample_hal_root_json)
        self.assertEqual(h.host, 'http://ex.com')
        self.assertEqual(h.fetched_from, 'http://ex.com/api_root')
        self.assertEqual(h.doc.url(), 'http://ex.com/api_root')
        self.assertFalse(h.is_preview)
        self.assertEqual(h['p1'], 1)
        self.assertRaises(AttributeError, getattr, h, 'nonexistentproperty')

    @responses.activate
    def test_unfound_links_make_zero_length_list(self):
        h = HALEasy('http://api.test_domain/api_root')
        self.assertEqual(len(list(h.links(rel='nonexistentrel'))), 0)  # we get a generator yielding nothing

    @responses.activate
    def test_can_iterate_unfound_links(self):
        h = HALEasy('http://api.test_domain/api_root')
        for l in h.links(rel='nonexistentrel'):  # we can iterate over the empty generator
            raise Exception('We should not reach this part of the loop')

    @responses.activate
    def test_linknotfoundexception_when_link_not_found_by_unary_method(self):
        h = HALEasy('http://api.test_domain/api_root')
        self.assertRaises(LinkNotFoundError, h.link, rel='nonexistentrel')

    @responses.activate
    def test_can_iterate_found_links(self):
        expected = [{
                        "name": "link5name1",
                        "href": "/link5path1",
                    },
                    {
                        "name": "link5name2",
                        "href": "/link5path2",
                    }]
        h = HALEasy('http://api.test_domain/api_root')
        l = list(h.links(rel='other:link5'))
        self.assertEqual(len(l), 2)
        for i, d in enumerate(expected):
            self.assertDictEqual(d, l[i].as_object())

    @responses.activate
    def test_can_extract_specific_link(self):
        h = HALEasy('http://api.test_domain/api_root')
        self.assertDictEqual(h.link(rel='other:link5').as_object(), {
            "name": "link5name1",
            "href": "/link5path1",
        })

    @responses.activate
    def test_find_named_rel_by_name(self):
        h = HALEasy('http://api.test_domain/api_root')
        l = h.link(name="thing3")


class TestHaleasyEmbedded(TestCase):
    sample_hal_root = {
        "_links": {
            "self": {
                "href": "/api_root"
            },
            "sample_hal_rel4": {
                "href": "/thing4"
            },
        },
        "_embedded": {
            "sample_hal_rel1": {
                "a": "b",
                "c": "d",
                "i": "j",
                "p": "q",
                "_links": {
                    "self": {
                        "href": "/thing1",
                        "name": "thing1"
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
        "a": "b"
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

    def setUp(self):
        responses.reset()
        responses.add(responses.GET, 'http://api.test_domain/api_root',
                      body=self.sample_hal_root_json, status=200,
                      content_type='application/json')
        responses.add(responses.GET, 'http://api.test_domain/thing1',
                      body=self.sample_hal_thing1_json, status=200,
                      content_type='application/json')


    @responses.activate
    def test_embedded_objects_exist(self):
        h = HALEasy('http://api.test_domain/api_root')
        self.assertTrue(h.link(rel='sample_hal_rel1').preview)
        self.assertTrue(h.link(rel='sample_hal_rel4').preview)

    @responses.activate
    def test_embedded_objects_with_same_rel_exist(self):
        h = HALEasy('http://api.test_domain/api_root')
        self.assertEqual(len(list(h.links(rel='sample_hal_rel2'))), 2)

    @responses.activate
    def test_embedded_object_has_preview_true(self):
        h = HALEasy('http://api.test_domain/api_root')
        h1 = h.link(rel="sample_hal_rel1").follow()
        self.assertTrue(h1.is_preview)  # h1 is an embedded resource

    @responses.activate
    def test_full_object_fetched_when_preview_lacks_property(self):
        h = HALEasy('http://api.test_domain/api_root')
        h1 = h.link(rel="sample_hal_rel1").follow()
        self.assertEqual(h1['k'], 'l')  # 'k' not in embedded resource properties, HTTP GET performed
        self.assertFalse(h1.is_preview) # h1 is now not an embedded resource
        self.assertEqual(h1['i'], 'x')  # value of h1['i'] has changed to 'x'
        self.assertEqual(h1.preview['i'], 'j')  # old value of h1['i'] available here

    @responses.activate
    def test_embedded_rel_with_multiple_objects(self):
        h = HALEasy('http://api.test_domain/api_root')
        links = list(h.links(rel="sample_hal_rel2"))
        self.assertEqual(len(links), 2)
        h2 = h.link(rel="sample_hal_rel2").follow()
        self.assertEqual(h2['e'], 'f')

    @responses.activate
    def test_find_embedded_rel_by_name(self):
        h = HALEasy('http://api.test_domain/api_root')
        l = h.link(name="thing1")

    @responses.activate
    def test_find_embedded_rel_by_property_in_self_link_when_no_link_from_resource(self):
        h = HALEasy('http://api.test_domain/api_root')
        h2 = h.link(rel="sample_hal_rel2", name="thing2").follow()
        self.assertEqual(h2['e'], 'f')


class TestHaleasyAnonymousEmbedded(TestCase):
    sample_hal_root = {
        "_links": {
            "self": {
                "href": "/api_root"
            },
        },
        "_embedded": {
            "emptylinks": {  # an anonymous resource with an empty links object
                "p": "q",
                "_links": {
                },
            },
            "nolinks": {  # an anonymous resource with no link object
                "p": "q",
            },
            "blank_href": {  # an anonymous resource with a blank href on its self link
                "p": "q",
                "_links": {
                    "self": {
                        "href": ""
                    }
                },
            },
        },
    }
    sample_hal_root_json = json.dumps(sample_hal_root)
    # TODO: add a failing case where there is a self link but it has no href (doesn't comply with HAL spec)

    def setUp(self):
        responses.reset()
        responses.add(responses.GET, 'http://api.test_domain/api_root',
                      body=self.sample_hal_root_json, status=200,
                      content_type='application/json')

    @responses.activate
    def test_emptylinks(self):
        h = HALEasy('http://api.test_domain/api_root')
        l = h.link(rel="emptylinks")
        h2 = l.follow()
        self.assertEqual(h2['p'], 'q')

    @responses.activate
    def test_nolinks(self):
        h = HALEasy('http://api.test_domain/api_root')
        l = h.link(rel="nolinks")
        h2 = l.follow()
        self.assertEqual(h2['p'], 'q')

    @responses.activate
    def test_blank_href(self):
        h = HALEasy('http://api.test_domain/api_root')
        l = h.link(rel="blank_href")
        h2 = l.follow()
        self.assertEqual(h2['p'], 'q')





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