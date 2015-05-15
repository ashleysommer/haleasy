from unittest import TestCase
from haleasy import HALEasy, LinkNotFoundError
import json
import responses

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