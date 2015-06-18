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


class LinkNotFoundError(Exception):
    pass


def listify(item_or_list):
    if isinstance(item_or_list, list):
        return item_or_list
    else:
        return [item_or_list]


def make_preview_url(url_string, host):
    """
    If the given URL has a base (scheme + host) then do nothing, otherwise use the host param to create a full url
    """
    if not url_string:
        # this is here to support anonymous resources - the full url for an anonymous resource is ''
        return ''
    if url_string.startswith('http://'):
        return url_string
    else:
        return urlparse.urljoin(host, url_string)


class HALHttpClient(object):
    DEFAULT_HEADERS = {'Accept': 'application/json',
                       'Content-Type': 'application/json'}
    DEFAULT_METHOD = 'GET'
    SUPPORTED_METHODS = ('GET', 'POST', 'PUT', 'DELETE')
    OK_CODES = {200, 203}
    REDIRECT_WITH_ORIGINAL_METHOD_CODES = {301, 302, 307, 308}
    REDIRECT_WITH_GET_CODES = {201, 303}
    MAYBE_REDIRECT_WITH_GET_CODES = {202, 204, 205}

    @classmethod
    def request(cls, url, method=None, data=None, session=None, **kwargs):
        """
        Public facing request method that does initial setup and sanitisation:
        * checks and supplies defaults
        * creates a session object to be used for this chain of requests, unless one is passed in.
        * if data is passed as an object instead of a string, JSONifies it
        * calls protected _request method, which may recurse and omits all the steps above
        """
        method = method or cls.DEFAULT_METHOD
        if method not in cls.SUPPORTED_METHODS:
            raise NotImplementedError('HTTP method %s is not implemented by this client' % method)

        if not session:
            # The user hasn't given us a session to use, so create a new session with headers and authentication
            # taken from **kwargs or defaults
            session = requests.Session()
            for k, v in six.iteritems(kwargs.get('headers', cls.DEFAULT_HEADERS)):
                session.headers[k] = v  # setting the header dict directly stops the case-insensitivity working
            session.auth = kwargs.get('auth', None)

        if data is not None and not isinstance(data, six.string_types):
            data = json.dumps(data)

        return cls._request(url, method, data, session, **kwargs)

    @classmethod
    def _request(cls, url, method, data, session, **kwargs):
        """
        A potentially recursive method which implements the standard behaviour for a REST client in response to various
        status codes and situations.
        """
        resp = session.request(method,
                               url,
                               data=data,
                               **kwargs)
        if resp.status_code in cls.OK_CODES:
            # The server is returning data we should interpret as a HAL document
            return resp
        elif resp.status_code in cls.REDIRECT_WITH_ORIGINAL_METHOD_CODES:
            # We should follow a Location header using the original method to find the document.  The absence of such a
            # header is an error
            return cls._request(resp.headers['Location'],
                                method=method,
                                session=session,
                                data=data,
                                **kwargs)
        elif resp.status_code in cls.REDIRECT_WITH_GET_CODES:
            # We should follow a Location header with a GET to find the document.  The absence of such a header is an
            # error
            return cls._request(resp.headers['Location'],
                                method='GET',
                                session=session,
                                data=None,
                                **kwargs)
        elif resp.status_code in cls.MAYBE_REDIRECT_WITH_GET_CODES:
            # We should _try_ to follow a Location header with a GET to find the document, but there may not be such a
            # header, in which case return the body and url we have
            if resp.headers['Location']:
                return cls._request(resp.headers['Location'],
                                    method='GET',
                                    session=session,
                                    data=None,
                                    **kwargs)
            else:
                return resp
        else:
            # Let requests raise any errors as it usually would
            resp.raise_for_status()
        # Response wasn't an error, or a non-error we know how to deal with
        raise NotImplementedError('HALHttpClient._http() does not handle HTTP status code %s. Response headers were %s',
                                  (resp.status_code, resp.headers))


class HALEasyLink(dougrain.link.Link):
    """
    A small wrapper around dougrain.link.Link which tracks base_uris, hal_classes and previews, as
    well as a .follow() method to create the next HAL doc
    """
    HTTP_CLIENT_CLASS = HALHttpClient

    def __init__(self, json_object, base_uri=None, rel=None, hal_class=None, preview=None):
        super(HALEasyLink, self).__init__(json_object, base_uri)
        self.base_uri = base_uri
        self.rel = rel
        self._hal_class = hal_class
        self.preview = preview

    def as_object_with_rel(self):
        o = {'rel': self.rel}
        o.update(self.as_object())
        return o

    def follow(self, method=None, data=None, **link_params):
        if self.preview:
            return self.preview
        else:
            url = self.url(**link_params)
            response = self.HTTP_CLIENT_CLASS.request(url, method=method, data=data)
            return self._hal_class(response.url, response.text, preview=self.preview)

    def __getitem__(self, item):
        return self.as_object()[item]

    def __repr__(self):
        return str(self.as_object_with_rel())


class HALEasy(object):
    HTTP_CLIENT_CLASS = HALHttpClient
    LINK_CLASS = HALEasyLink

    def _add_links(self):
        self._link_list = []
        for rel, links in six.iteritems(self.doc.links):
            for link in listify(links):
                self._link_list.append(self.LINK_CLASS(link.as_object(),
                                                       base_uri=self.host,
                                                       rel=rel,
                                                       hal_class=type(self)))

    def _add_embedded_as_links(self):
        for rel in self.doc.embedded:
            for embedded_resource in listify(self.doc.embedded[rel]):
                # create a HALEasy object for each embedded resource
                preview = type(self)(make_preview_url(embedded_resource.url(), self.host),
                                     json_str=json.dumps(embedded_resource.as_object()),
                                     is_preview=True)
                try:
                    # if there are links to the embedded resource in the parent document, set the .preview attribute
                    # of those links to the embedded resource
                    direct_links = []
                    for link in self.links(rel=rel, href=preview.doc.links['self'].href):
                        link.preview = preview
                        direct_links.append(link)
                    if not direct_links:
                        raise LinkNotFoundError
                except (LinkNotFoundError, KeyError):
                    # the embedded resource is not linked to in the _links section of the parent document, so we will
                    # make it accessible via our links() method by adding a new link using the embedded resource's
                    # self link.  If the embedded resource does not have a self link we will create an 'anonymous'
                    # resource with a self link href of ''
                    try:
                        self_link_properties = preview.link(rel='self').as_object()
                    except LinkNotFoundError:
                        self_link_properties = {'href': ''}
                    new_link = self.LINK_CLASS(self_link_properties,
                                               base_uri=preview.host,
                                               rel=rel,
                                               hal_class=type(self),
                                               preview=preview)
                    self._link_list.append(new_link)

    def __init__(self,
                 url,
                 data=None,
                 method=None,
                 json_str=None,
                 is_preview=False,
                 preview=None,
                 http_client_class=None,
                 **kwargs):
        # If json_str is provided then we use that to build the document, otherwise we follow the url.  Note even when
        # providing a json_str you also need to provide a URL, because this is a HAL client, not a HAL document parser,
        # and without a URL it can't always know where to go next
        self._maybe_set_http_client_class(http_client_class)
        if not json_str:
            self.from_url(url, method=method, data=data, **kwargs)
        else:
            self.from_json(url, json_str, is_preview=is_preview)
            self.preview = preview

    def _maybe_set_http_client_class(self, http_client_class):
        if not hasattr(self, 'http_client_class'):
            self.http_client_class = http_client_class or self.HTTP_CLIENT_CLASS

    def from_url(self, url, method=None, data=None, http_client_class=None, **kwargs):
        self._maybe_set_http_client_class(http_client_class)
        response = self.http_client_class.request(url, method=method, data=data, **kwargs)
        self.from_response(response, http_client_class=http_client_class)

    def from_response(self, response, http_client_class=None):
        self._maybe_set_http_client_class(http_client_class)
        self.from_json(response.url, response.text, is_preview=False)

    def from_json(self, url, json_str, is_preview=None, http_client_class=None):
        self._maybe_set_http_client_class(http_client_class)
        self.fetched_from = url
        self.doc = dougrain.Document.from_object(json.loads(json_str), base_uri=url)
        self.is_preview = is_preview
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
        links_found = []
        for link in self._link_list:
            if not want_params:
                links_found.append(link)
            else:
                has_params = link.as_object_with_rel()
                for k, v in six.iteritems(want_params):
                    try:
                        if has_params[k] != v:
                            break  # the key exists but the values don't match
                    except KeyError:
                        break  # the key doesn't exist
                else:  # this else belongs to the for loop - executed if all param values matched
                    links_found.append(link)
        return links_found

    def link(self, **want_params):
        """
        Return only the first link matching the want_params dict.  Use this if you are confident there is only one link
        for a given match, which is quite common for singular rels.  It will raise a LinkNotFoundError if no matching
        link is found, to help avoid subtle bugs if the returned value isn't used immediately
        """
        try:
            return self.links(**want_params)[0]
        except IndexError:
            raise LinkNotFoundError('no link matching %s found, document is %s' % (want_params, self))

    def rels(self):
        return self.doc.links.keys()