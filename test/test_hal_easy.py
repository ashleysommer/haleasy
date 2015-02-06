from unittest import TestCase
from haleasy import HALEasy
import json


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

class test_hal_easy(TestCase):
    def test_properties(self):
        h = HALEasy('', json_str=sample_hal_root_json)
        self.assertEqual(h['p1'], 1)
        self.assertRaises(AttributeError, getattr, h, 'nonexistentproperty')

    def test_links(self):
        h = HALEasy('', json_str=sample_hal_root_json)

        self.assertEqual(len(list(h.links(rel='nonexistentrel'))), 0)  # we get a generator yielding nothing

        for l in h.links(rel='nonexistentrel'):  # we can iterate over the empty generator
            raise Exception('We should not reach this part of the loop')

        l = list(h.links(rel='other:link5'))
        self.assertEqual(len(l), 2)
        for i, d in enumerate([
            {
              "name": "link5name1",
              "href": "/link5path1",
              "rel": "other:link5"
            },
            {
                "name": "link5name2",
                "href": "/link5path2",
                "rel": "other:link5"
            }
            ]):
            self.assertDictEqual(d, l[i].as_object())
        self.assertDictEqual(h.link(rel='other:link5').as_object(), {
              "name": "link5name1",
              "href": "/link5path1",
              "rel": "other:link5"
            })
        self.assertEqual(h.link(rel='other:link3').href, "/link3path")  # we get a single object
        self.assertRaises(ValueError, h.link, rel='nonexistentrel')


