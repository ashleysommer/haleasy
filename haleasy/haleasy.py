import dougrain
import dougrain.link
import requests
import json
import urlparse


def iteritems(item_or_list, item_type):
    if type(item_or_list) == item_type:
        yield item_or_list
    else:
        for item_or_list_2 in item_or_list:
            for next_item in iteritems(item_or_list_2, item_type):
                yield next_item


class HALEasy(object):
    DEFAULT_HEADERS = {'Accept': 'application/json',
                       'Content-Type': 'application/hal+json'}
    DEFAULT_METHOD = 'GET'

    def __init__(self, url, data=None, method=None, headers=None, json_str=None, **kwargs):
        """
        If json_str is provided then we don't try to fetch anything over HTTP, we build the doc directly from the str
        """
        if not json_str:
            json_str, url = self.follow(url, data=data, method=method, headers=headers, **kwargs)
        self.url = url
        url_parts = urlparse.urlsplit(url)
        self.path = urlparse.urlunsplit(('', '')+(url_parts[2:]))
        self.host = urlparse.urlunsplit(url_parts[:2]+('', '', ''))
        self.doc = dougrain.Document.from_object(json.loads(json_str))
        my_class = type(self)
        self._link_list = []
        for rel, link_or_list in self.doc.links.iteritems():
            for item in iteritems(link_or_list, dougrain.link.Link):
                self._link_list.append(HALEasyLink(item, rel=rel, host=self.host, hal_class=my_class))

    @classmethod
    def follow(cls, url, method=None, headers=None, data=None, **kwargs):
        """
        The kwargs will are passed in to the requests.Session.send() function after populating with defaults if needed
        for HTTP method (GET), and the Accept and Content-Type headers (both application/json)
        """
        if data is not None and not isinstance(data, basestring):
            data = json.dumps(data)
        session = requests.Session()
        req = requests.Request(method or cls.DEFAULT_METHOD,
                               url,
                               headers=headers or cls.DEFAULT_HEADERS,
                               data=data).prepare()
        resp = session.send(req, **kwargs)
        if resp.status_code == 200:
            return resp.text, url
        elif resp.status_code in {201, 303}:
            # 201 and 303 force the next request to be a GET
            return cls.follow(resp.headers['Location'],
                              method='GET',
                              headers=headers or cls.DEFAULT_HEADERS,
                              **kwargs)
        elif resp.status_code in {301, 302, 307}:
            return cls.follow(resp.headers['Location'],
                              method=method or cls.DEFAULT_METHOD,
                              headers=headers or cls.DEFAULT_HEADERS,
                              data=data,
                              **kwargs)
        else:
            resp.raise_for_status()
        # Response wasn't OK, or a handleable redirect, or an error
        raise NotImplementedError('haleasy.follow() does not handle HTTP status code %s.  Headers were %s',
                                  (resp.status_code, resp.headers))

    def __getitem__(self, item):
        """
        To access any properties of the HAL document use H['attrname'].  To access any other methods or properties of
        the dougrain document object use H.doc
        """
        return self.doc.properties[item]

    def properties(self):
        return self.doc.properties

    def links(self, **want_params):
        """
        Return an iterator over the links that match the given names and values in the want_params dict.  To get all
        links pass nothing - the links you get will have their 'rel' attribute populated.  No exception will be raised
        if the list of links returned is empty, as typical usage is expected to be for l in h.links(rel='somerel'):
        and the loop body will simply not be executed

        H.links()
        H.links(rel='next')
        H.links(rel='next', profile='video')
        """
        for link in self._link_list:
            if not want_params:
                yield link
            else:
                has_params = link.as_object()
                for k, v in want_params.iteritems():
                    try:
                        if has_params[k] != v:
                            break  # the key exists but the values don't match
                    except KeyError:
                        break  # the key doesn't exist
                else:  # this else belongs to the for loop - executed if all param values matched
                    yield link

    def link(self, **want_params):
        """
        Return only the first link matching the want_params dict.  Use this if you are confident there is only
        one link for a given match, which is quite common for singular rels.  It will raise a ValueError if no matching
        link is found, to help avoid subtle bugs if the returned value isn't used immediately
        """
        try:
            return self.links(**want_params).next()
        except StopIteration:
            raise ValueError('no link matching %s found, known links are %s' % (want_params, self._link_list))

    def __repr__(self):
        return str({'url': self.url,
                    'doc': self.doc.as_object()})


class HALEasyLink(dougrain.link.Link):
    """
    A small wrapper around dougrain.link.Link which adds .host and .path properties, along with a .follow method to
    create HALEasy documents
    """
    def __init__(self, link, rel=None, host=None, hal_class=None):
        super(HALEasyLink, self).__init__(link.as_object(), None)
        self.o['rel'] = rel
        self.host = host
        self.hal_class = hal_class
        self.path = self.url()

    def follow(self, method=None, headers=None, data=None):
        return self.hal_class(urlparse.urljoin(self.host, self.href), method=method, headers=headers, data=data)

    def __repr__(self):
        return str(self.o)
