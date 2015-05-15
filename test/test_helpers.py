from unittest import TestCase
from haleasy import listify, make_preview_url


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
