from unittest import TestCase
from haleasy import HALHttpClient
from requests import Session
from requests.auth import HTTPDigestAuth


class TestHeaders(TestCase):
    def test_default_headers(self):
        class TestHttpClient(HALHttpClient):
            DEFAULT_HEADERS = {'Content-Type': 'application/json'}
            @classmethod
            def _request(cls, url, method, data, session, **kwargs):
                return session

        session = TestHttpClient.request('any')
        self.assertEqual(session.headers['content-type'], 'application/json')  # note the change of case


class TestHalHttpClientSession(TestCase):
    def test_invalid_methods_rejected(self):
        self.assertRaises(NotImplementedError, HALHttpClient.request, 'dummy_test_host1234.local', method='ZZZ')

    def test_if_no_session_passed_in_one_is_created(self):
        class TestHttpClient(HALHttpClient):
            @classmethod
            def _request(cls, url, method, data, session, **kwargs):
                return session

        default_session = TestHttpClient.request('http://api.test_domain/api_root')
        self.assertEqual(type(default_session), Session)
        default_session_2 = TestHttpClient.request('http://api.test_domain/api_root')
        self.assertEqual(type(default_session_2), Session)
        self.assertNotEqual(default_session, default_session_2)

    def test_session_passed_in_is_used(self):
        class TestHttpClient(HALHttpClient):
            @classmethod
            def _request(cls, url, method, data, session, **kwargs):
                return session

        mysession = Session()
        httpclientsession = TestHttpClient.request('http://api.test_domain/api_root', session=mysession)
        self.assertEqual(mysession, httpclientsession)


class TestHTTPAuth(TestCase):
    def test_basic_auth(self):
        class TestHttpClient(HALHttpClient):
            @classmethod
            def _request(cls, url, method, data, session, **kwargs):
                return session

        httpclientsession = TestHttpClient.request('http://api.test_domain/api_root', auth=('u', 'p'))
        self.assertEqual(httpclientsession.auth, ('u', 'p'))

    def test_basic_auth_with_session(self):
        class TestHttpClient(HALHttpClient):
            @classmethod
            def _request(cls, url, method, data, session, **kwargs):
                return session

        mysession = Session()
        mysession.auth = ('u', 'p')
        httpclientsession = TestHttpClient.request('http://api.test_domain/api_root', session=mysession)
        self.assertEqual(httpclientsession.auth, ('u', 'p'))

    def test_object_auth(self):
        """
        Although it uses HTTPDigestAuth, if this test passes then any custom authentication scheme should work, such
        as OAuth.  It doesn't seem worth creating a dev dependency to prove this though.
        """
        class TestHttpClient(HALHttpClient):
            @classmethod
            def _request(cls, url, method, data, session, **kwargs):
                return session

        mysession = Session()
        mysession.auth = HTTPDigestAuth('u', 'p')
        httpclientsession = TestHttpClient.request('http://api.test_domain/api_root', session=mysession)
        self.assertEqual(httpclientsession.auth, mysession.auth)

