from unittest import TestCase
from haleasy import HALEasy, LinkNotFoundError
import json
import responses


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

    @responses.activate
    def test_link_variable_expansion(self):
        thing4json = json.dumps({
            "_links": {
                "self": {
                    "href": "/link4path/foo"
                }
            },
            "prop1": "val1" })
        responses.add(responses.GET, 'http://api.test_domain/link4path/foo',
                      body=thing4json, status=200,
                      content_type='application/json')
        h = HALEasy('http://api.test_domain/api_root')
        h2 = h.link(rel="link4").follow(var="foo")
        self.assertEqual(h2.fetched_from, 'http://api.test_domain/link4path/foo')


