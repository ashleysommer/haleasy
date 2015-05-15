import dougrain
import dougrain.link
import requests
import json
import six
if six.PY2:
    import urlparse
else:
    import urllib.parse as urlparse
import copy

import logging
logging.basicConfig(level='DEBUG')

class LinkNotFoundError(Exception):
    pass


def listify(item_or_list):
    if isinstance(item_or_list, list):
        return item_or_list
    else:
        return [item_or_list]


def make_preview_url(urlstring, host):
    '''
    If the given URL has a base (scheme + host) then do nothing, otherwise use the host param to create a full url
    :param urlstring:
    :param host:
    :return:
    '''
    if not urlstring:
        # this is here to support anonymous resources - the full url for an anonymous resource is ''
        return ''
    if urlstring.startswith('http://'):
        return urlstring
    else:
        return urlparse.urljoin(host, urlstring)


class HttpDefaults(object):
    DEFAULT_HEADERS = {'Accept': 'application/json',
                       'Content-Type': 'application/hal+json'}
    DEFAULT_METHOD = 'GET'
    SUPPORTED_METHODS = (None, 'GET', 'POST', 'PUT', 'DELETE')


class HALEasy(object):
    def _add_links(self):
        self._link_list = []
        for rel, links in six.iteritems(self.doc.links):
            for link in listify(links):
                self._link_list.append(HALEasyLink(link.as_object(),
                                                   self.httpdefaults,
                                                   base_uri=self.host,
                                                   rel=rel,
                                                   hal_class=type(self)))

    def _add_embedded_as_links(self):
        for rel in self.doc.embedded:
            logging.debug('in rel %s' % rel)
            for embedded_resource in listify(self.doc.embedded[rel]):
                logging.debug('embedded resource is %s' % embedded_resource.as_object())
                if 'self' in embedded_resource.links:
                    has_self_link = True
                    preview_url = make_preview_url(embedded_resource.url(), self.host)
                    self_link_properties = embedded_resource.links['self'].as_object()
                else:
                    has_self_link = False
                    self_link_properties = {'href': ''}
                    preview_url = ''
                logging.debug('SLP: %s' % self_link_properties)
                preview = HALEasy(preview_url,
                                  json_str=json.dumps(embedded_resource.as_object()),
                                  is_preview=True)
                logging.debug('PREVIEW' % preview)
                direct_link_found = False
                if has_self_link:
                    for link in self.links(rel=rel, href=preview.doc.links['self'].href):
                        link.preview = preview
                        direct_link_found = True
                if not direct_link_found:
                    new_link = HALEasyLink(self_link_properties,
                                           self.httpdefaults,
                                           base_uri=preview.host,
                                           rel=rel,
                                           hal_class=type(self),
                                           preview=preview)
                    self._link_list.append(new_link)

    def __init__(self,
                 url,
                 data=None,
                 method=None,
                 headers=None,
                 json_str=None,
                 is_preview=False,
                 preview=None,
                 httpdefaults=None,
                 **kwargs):
        # If json_str is provided then we use that to build the document, otherwise we follow the url.  Note even when
        # providing a json_str you also need to provide a URL, because this is a HAL client, not a HAL document parser,
        # and without a URL it can't always know where to go next
        if not httpdefaults:
            self.httpdefaults = HttpDefaults
        if not json_str:
            json_str, url = HALEasyLink._http(url, self.httpdefaults, data=data, method=method, headers=headers, **kwargs)
        self.doc = dougrain.Document.from_object(json.loads(json_str), base_uri=url)
        self.fetched_from = url
        self.is_preview = is_preview
        self.preview = preview
        self._add_links()
        self._add_embedded_as_links()

    @property
    def host(self):
        parts = urlparse.urlsplit(self.fetched_from)
        return urlparse.urlunsplit(parts[:2]+('', '', ''))

    def _update(self, other):
        self.doc = other.doc
        self.is_preview = other.is_preview
        # we don't update our .preview property
        self._link_list = other._link_list

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
                clone = copy.deepcopy(self)
                self._update(target)
                self.preview = clone
                return self[item]
            else:
                raise

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
                for k, v in six.iteritems(want_params):
                    try:
                        if has_params[k] != v:
                            break  # the key exists but the values don't match
                    except KeyError:
                        break  # the key doesn't exist
                else:  # this else belongs to the for loop - executed if all param values matched
                    yield link

    def link(self, **want_params):
        """
        Return only the first link matching the want_params dict.  Use this if you are confident there is only one link
        for a given match, which is quite common for singular rels.  It will raise a LinkNotFoundError if no matching
        link is found, to help avoid subtle bugs if the returned value isn't used immediately
        """
        try:
            return six.next(self.links(**want_params))
        except StopIteration:
            raise LinkNotFoundError('no link matching %s found, document is %s' % (want_params, self))

    def __repr__(self):
        return str(self.__dict__)


class HALEasyLink(dougrain.link.Link):
    """
    A small wrapper around dougrain.link.Link which tracks base_uris, hal_classes and previews, as
    well as a .follow() method to create the next HAL doc
    """
    def __init__(self, json_object, httpdefaults, base_uri=None, rel=None, hal_class=None, preview=None):
        super(HALEasyLink, self).__init__(json_object, base_uri)
        self.base_uri = base_uri
        self.rel = rel
        self.hal_class = hal_class
        self.httpdefaults = httpdefaults
        self.preview = preview

    def as_object_with_rel(self):
        o = {'rel': self.rel}
        o.update(self.as_object())
        return o

    @classmethod
    def _http(cls, url, httpdefaults, method=None, headers=None, data=None, **kwargs):
        """
        The kwargs will are passed in to the requests.Session.send() function after populating with defaults if needed
        for HTTP method (GET), and the Accept and Content-Type headers (both application/json)
        """
        # logging.debug("cls: %s" % cls)
        # logging.debug("hal_class: %s" % hal_class)
        # logging.debug("url: %s" % url)
        # logging.debug("method: %s" % method)
        if method not in httpdefaults.SUPPORTED_METHODS:
            raise NotImplementedError('HTTP method %s is not implemented by the HALEasy client' % method)
        if data is not None and not isinstance(data, six.string_types):
            data = json.dumps(data)
        session = requests.Session()
        req = requests.Request(method or httpdefaults.DEFAULT_METHOD,
                               url,
                               headers=headers or httpdefaults.DEFAULT_HEADERS,
                               data=data).prepare()
        resp = session.send(req, **kwargs)
        if resp.status_code in (200, 203):
            # The server is returning data we should interpret as a HAL document
            return resp.text, url
        elif resp.status_code in (301, 302, 307, 308):
            # We should follow a Location header using the original method to find the document.  The absence of such a
            # header is an error
            return cls._http(resp.headers['Location'],
                             httpdefaults,
                             method=method or httpdefaults.DEFAULT_METHOD,
                             headers=headers or httpdefaults.DEFAULT_HEADERS,
                             data=data,
                             **kwargs)
        elif resp.status_code in (201, 303):
            # We should follow a Location header with a GET to find the document.  The absence of such a header is an
            # error
            return cls._http(resp.headers['Location'],
                             httpdefaults,
                             method='GET',
                             headers=headers or httpdefaults.DEFAULT_HEADERS,
                             **kwargs)
        elif resp.status_code in (202, 204, 205):
            # We should _try_ to follow a Location header with a GET to find the document, but there may not be such a
            # header, and that is OK.
            if resp.headers['Location']:
                return cls._http(resp.headers['Location'],
                                 httpdefaults,
                                 method='GET',
                                 headers=headers or httpdefaults.DEFAULT_HEADERS,
                                 **kwargs)
            else:
                return resp.text, url
        else:
            resp.raise_for_status()
        # Response wasn't an error, or a non-error we know how to deal with
        raise NotImplementedError('haleasylink.follow() does not handle HTTP status code %s.  Response headers were %s',
                                  (resp.status_code, resp.headers))

    def follow(self, httpdefaults=None, method=None, headers=None, data=None, **link_params):
        if not httpdefaults:
            httpdefaults = self.httpdefaults
        if self.preview:
            return self.preview
        else:
            url = self.url(**link_params)
            body, url = HALEasyLink._http(url, httpdefaults, method=method, headers=headers, data=data, preview=self.preview)
            return self.hal_class(url, body)

    def __getitem__(self, item):
        return self.as_object()[item]

    def __repr__(self):
        return str(self.as_object_with_rel())
