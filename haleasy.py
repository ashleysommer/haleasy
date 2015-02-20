import dougrain
import dougrain.link
import requests
import json
import urlparse

class LinkNotFoundError(Exception):
    pass


def listify(item_or_list):
    if isinstance(item_or_list, list):
        return item_or_list
    else:
        return [item_or_list]


def make_full_url(url, host):
    if url.startswith('http://'):
        return url
    else:
        return urlparse.urljoin(host, url)


class HALEasy(object):
    DEFAULT_HEADERS = {'Accept': 'application/json',
                       'Content-Type': 'application/hal+json'}
    DEFAULT_METHOD = 'GET'
    SUPPORTED_METHODS = (None, 'GET', 'POST', 'PUT', 'DELETE')

    def _add_links(self):
        self._link_list = []
        for rel, links in self.doc.links.iteritems():
            for link in listify(links):
                self._link_list.append(HALEasyLink(link.as_object(),
                                                   base_uri=self.host,
                                                   rel=rel,
                                                   hal_class=type(self)))

    def _add_embedded_as_links(self):
        for rel in self.doc.embedded:
            for resource in listify(self.doc.embedded[rel]):
                preview = HALEasy(make_full_url(resource.url(), self.host),
                                  json_str=json.dumps(resource.as_object()),
                                  is_preview=True)

                try:
                    link = self.link(rel=rel, href=preview.link(rel='self').href)
                    link.preview = preview
                except LinkNotFoundError:
                    new_link = HALEasyLink(preview.link(rel='self').as_object(),
                                           base_uri=preview.host,
                                           rel=rel,
                                           hal_class=type(self),
                                           preview=preview)
                    self._link_list.append(new_link)

    def __init__(self, url, data=None, method=None, headers=None, json_str=None, is_preview=False, preview=None, **kwargs):
        """
        If json_str is provided then we don't try to fetch anything over HTTP, we build the doc directly from the str
        """
        if not json_str:
            json_str, url = self.follow(url, data=data, method=method, headers=headers, **kwargs)
        url_parts = urlparse.urlsplit(url)
        self.path = urlparse.urlunsplit(('', '')+(url_parts[2:]))
        self.host = urlparse.urlunsplit(url_parts[:2]+('', '', ''))
        if not self.host:
            raise ValueError('HAL document must have a full url, but you gave me %s' % url)
        self.doc = dougrain.Document.from_object(json.loads(json_str), base_uri=self.host)
        self.is_preview = is_preview
        self.preview = preview
        self._add_links()
        self._add_embedded_as_links()

    def _update(self, other):
        self.path = other.path
        self.host = other.host
        self.doc = other.doc
        self.is_preview = other.is_preview
        self.preview = other.is_preview
        self._link_list = other._link_list

    @classmethod
    def follow(cls, url, method=None, headers=None, data=None, **kwargs):
        """
        The kwargs will are passed in to the requests.Session.send() function after populating with defaults if needed
        for HTTP method (GET), and the Accept and Content-Type headers (both application/json)
        """
        if method not in cls.SUPPORTED_METHODS:
            raise NotImplementedError('HTTP method %s is not implemented by the HALEasy client' % method)
        if data is not None and not isinstance(data, basestring):
            data = json.dumps(data)
        session = requests.Session()
        req = requests.Request(method or cls.DEFAULT_METHOD,
                               url,
                               headers=headers or cls.DEFAULT_HEADERS,
                               data=data).prepare()
        resp = session.send(req, **kwargs)
        if resp.status_code in (200, 203):
            # The server is returning data we should interpret as a HAL document
            return resp.text, url
        elif resp.status_code in (301, 302, 307, 308):
            # We should follow a Location header using the original method to find the document.  The absence of such a
            # header is an error
            return cls.follow(resp.headers['Location'],
                              method=method or cls.DEFAULT_METHOD,
                              headers=headers or cls.DEFAULT_HEADERS,
                              data=data,
                              **kwargs)
        elif resp.status_code in (201, 303):
            # We should follow a Location header with a GET to find the document.  The absence of such a header is an
            # error
            return cls.follow(resp.headers['Location'],
                              method='GET',
                              headers=headers or cls.DEFAULT_HEADERS,
                              **kwargs)
        elif resp.status_code in (202, 204, 205):
            # We should _try_ to follow a Location header with a GET to find the document, but there may not be such a
            # header, and that is OK.
            if resp.headers['Location']:
                return cls.follow(resp.headers['Location'],
                                  method='GET',
                                  headers=headers or cls.DEFAULT_HEADERS,
                                  **kwargs)
            else:
                return
        else:
            resp.raise_for_status()
        # Response wasn't an error, or a non-error we know how to deal with
        raise NotImplementedError('haleasy.follow() does not handle HTTP status code %s.  Response headers were %s',
                                  (resp.status_code, resp.headers))

    def __getitem__(self, item):
        """
        To access any properties of the HAL document use H['attrname'].  To access any other methods or properties of
        the dougrain document object use H.doc
        """
        try:
            return self.doc.properties[item]
        except KeyError:
            if self.is_preview:
                target = self.link(rel='self').follow()
                self._update(target)
                return self[item]
            else:
                raise

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
        if 'rel' in want_params:
            want_params['rel'] = self.doc.expand_curie(want_params['rel'])
        for link in self._link_list:
            if not want_params:
                yield link
            else:
                has_params = link.as_object_with_rel()
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
        one link for a given match, which is quite common for singular rels.  It will raise a LinkNotFoundError if no matching
        link is found, to help avoid subtle bugs if the returned value isn't used immediately
        """
        try:
            return self.links(**want_params).next()
        except StopIteration:
            raise LinkNotFoundError('no link matching %s found, document is %s' % (want_params, self))

    def __repr__(self):
        return str(self.__dict__)


class HALEasyLink(dougrain.link.Link):
    """
    A small wrapper around dougrain.link.Link which tracks base_uris, hal_classes and previews, as
    well as a .follow() method to create the next HAL doc
    """
    def __init__(self, json_object, base_uri=None, rel=None, hal_class=None, preview=None):
        super(HALEasyLink, self).__init__(json_object, base_uri)
        self.base_uri = base_uri
        self.rel = rel
        self.hal_class = hal_class
        self.preview = preview

    def as_object_with_rel(self):
        o = {'rel': self.rel}
        o.update(self.as_object())
        return o

    def follow(self, method=None, headers=None, data=None, **link_params):
        if self.preview:
            return self.preview
        else:
            url = self.url(**link_params)
            return self.hal_class(url, method=method, headers=headers, data=data, preview=self.preview)

    def __getitem__(self, item):
        return self.as_object()[item]

    def __repr__(self):
        return str(self.o)
