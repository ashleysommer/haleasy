from unittest import TestCase
from haleasy import HALHttpClient
import json
import responses

class TestHalHttpClient(TestCase):
    def test_invalid_methods_rejected(self):
        self.assertRaises(NotImplementedError, HALHttpClient.request, 'dummy_test_host1234.local', method='ZZZ')

    def test_if_no_session_passed_in_one_is_created(self):
        class TestHttpClient(HALHttpClient):
            @classmethod
            def _request(cls, url, method, session, data, **kwargs):
                self.assertIsNotNone(session)
                return None, None
        (body, url) = TestHttpClient.request('http://api.test_domain/api_root')

