from unittest import TestCase
from haleasy import HALHttpClient
import json
import responses

class TestHalHttpClient(TestCase):
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

    def test_invalid_methods_rejected(self):
        self.assertRaises(NotImplementedError, HALHttpClient.request, 'dummy_test_host1234.local', method='ZZZ')

    def test_if_no_session_passed_in_one_is_created(self):
        class TestHttpClient(HALHttpClient):
            @classmethod
            def _request(cls, url, method, session, data, **kwargs):
                self.assertIsNotNone(session)
                return None, None
        (body, url) = TestHttpClient.request('http://api.test_domain/api_root')

