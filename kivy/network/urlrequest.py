'''
UrlRequest
==========

.. versionadded:: 1.0.8

You can use the :class:`UrlRequest` to make asynchronous requests on the
web and get the result when the request is completed. The spirit is the
same as the XHR object in Javascript.

The content is also decoded if the Content-Type is
application/json and the result automatically passed through json.loads.


The syntax to create a request::

    from kivy.network.urlrequest import UrlRequest
    req = UrlRequest(url, on_success, on_redirect, on_failure, on_error,
                     on_progress, req_body, req_headers, chunk_size,
                     timeout, method, decode, debug, file_path, ca_file,
                     verify)


Only the first argument is mandatory: the rest are optional.
By default, a "GET" request will be sent. If the :attr:`UrlRequest.req_body` is
not None, a "POST" request will be sent. It's up to you to adjust
:attr:`UrlRequest.req_headers` to suit your requirements and the response
to the request will be accessible as the parameter called "result" on
the callback function of the on_success event.


Example of fetching JSON::

    def got_json(req, result):
        for key, value in result['headers'].items():
            print('{}: {}'.format(key, value))

    req = UrlRequest('https://httpbin.org/headers', got_json)

Example of Posting data (adapted from httplib example)::

    import urllib

    def bug_posted(req, result):
        print('Our bug is posted!')
        print(result)

    params = urllib.urlencode({'@number': 12524, '@type': 'issue',
        '@action': 'show'})
    headers = {'Content-type': 'application/x-www-form-urlencoded',
              'Accept': 'text/plain'}
    req = UrlRequest('bugs.python.org', on_success=bug_posted, req_body=params,
            req_headers=headers)

If you want a synchronous request, you can call the wait() method.

'''

from collections import deque
from threading import Thread
from json import loads
from time import sleep
from kivy.compat import PY2

if PY2:
    from httplib import HTTPConnection
    from urlparse import urlparse, urlunparse
else:
    from http.client import HTTPConnection
    from urllib.parse import urlparse, urlunparse

try:
    import ssl

    HTTPSConnection = None
    if PY2:
        from httplib import HTTPSConnection
    else:
        from http.client import HTTPSConnection
except ImportError:
    # depending the platform, if openssl support wasn't compiled before python,
    # this class is not available.
    pass

from kivy.clock import Clock
from kivy.weakmethod import WeakMethod
from kivy.logger import Logger


# list to save UrlRequest and prevent GC on un-referenced objects
g_requests = []


class UrlRequest(Thread):
    '''A UrlRequest. See module documentation for usage.

    .. versionchanged:: 1.5.1
        Add `debug` parameter

    .. versionchanged:: 1.0.10
        Add `method` parameter

    .. versionchanged:: 1.8.0

        Parameter `decode` added.
        Parameter `file_path` added.
        Parameter `on_redirect` added.
        Parameter `on_failure` added.

    .. versionchanged:: 1.9.1

        Parameter `ca_file` added.
        Parameter `verify` added.

    .. versionchanged:: 1.10.0

        Parameters `proxy_host`, `proxy_port` and `proxy_headers` added.

    :Parameters:
        `url`: str
            Complete url string to call.
        `on_success`: callback(request, result)
            Callback function to call when the result has been fetched.
        `on_redirect`: callback(request, result)
            Callback function to call if the server returns a Redirect.
        `on_failure`: callback(request, result)
            Callback function to call if the server returns a Client or
            Server Error.
        `on_error`: callback(request, error)
            Callback function to call if an error occurs.
        `on_progress`: callback(request, current_size, total_size)
            Callback function that will be called to report progression of the
            download. `total_size` might be -1 if no Content-Length has been
            reported in the http response.
            This callback will be called after each `chunk_size` is read.
        `req_body`: str, defaults to None
            Data to sent in the request. If it's not None, a POST will be done
            instead of a GET.
        `req_headers`: dict, defaults to None
            Custom headers to add to the request.
        `chunk_size`: int, defaults to 8192
            Size of each chunk to read, used only when `on_progress` callback
            has been set. If you decrease it too much, a lot of on_progress
            callbacks will be fired and will slow down your download. If you
            want to have the maximum download speed, increase the chunk_size
            or don't use ``on_progress``.
        `timeout`: int, defaults to None
            If set, blocking operations will timeout after this many seconds.
        `method`: str, defaults to 'GET' (or 'POST' if ``body`` is specified)
            The HTTP method to use.
        `decode`: bool, defaults to True
            If False, skip decoding of the response.
        `debug`: bool, defaults to False
            If True, it will use the Logger.debug to print information
            about url access/progression/errors.
        `file_path`: str, defaults to None
            If set, the result of the UrlRequest will be written to this path
            instead of in memory.
        `ca_file`: str, defaults to None
            Indicates a SSL CA certificate file path to validate HTTPS
            certificates against
        `verify`: bool, defaults to True
            If False, disables SSL CA certificate verification
        `proxy_host`: str, defaults to None
            If set, the proxy host to use for this connection.
        `proxy_port`: int, defaults to None
            If set, and `proxy_host` is also set, the port to use for
            connecting to the proxy server.
        `proxy_headers`: dict, defaults to None
            If set, and `proxy_host` is also set, the headers to send to the
            proxy server in the ``CONNECT`` request.
    '''

    def __init__(self, url, on_success=None, on_redirect=None,
                 on_failure=None, on_error=None, on_progress=None,
                 req_body=None, req_headers=None, chunk_size=8192,
                 timeout=None, method=None, decode=True, debug=False,
                 file_path=None, ca_file=None, verify=True, proxy_host=None,
                 proxy_port=None, proxy_headers=None):
        super(UrlRequest, self).__init__()
        self._queue = deque()
        self._trigger_result = Clock.create_trigger(self._dispatch_result, 0)
        self.daemon = True
        self.on_success = WeakMethod(on_success) if on_success else None
        self.on_redirect = WeakMethod(on_redirect) if on_redirect else None
        self.on_failure = WeakMethod(on_failure) if on_failure else None
        self.on_error = WeakMethod(on_error) if on_error else None
        self.on_progress = WeakMethod(on_progress) if on_progress else None
        self.decode = decode
        self.file_path = file_path
        self._debug = debug
        self._result = None
        self._error = None
        self._is_finished = False
        self._resp_status = None
        self._resp_headers = None
        self._resp_length = -1
        self._chunk_size = chunk_size
        self._timeout = timeout
        self._method = method
        self.ca_file = ca_file
        self.verify = verify
        self._proxy_host = proxy_host
        self._proxy_port = proxy_port
        self._proxy_headers = proxy_headers

        #: Url of the request
        self.url = url

        #: Request body passed in __init__
        self.req_body = req_body

        #: Request headers passed in __init__
        self.req_headers = req_headers

        # save our request to prevent GC
        g_requests.append(self)

        self.start()

    def run(self):
        q = self._queue.appendleft
        url = self.url
        req_body = self.req_body
        req_headers = self.req_headers

        try:
            result, resp = self._fetch_url(url, req_body, req_headers, q)
            if self.decode:
                result = self.decode_result(result, resp)
        except Exception as e:
            q(('error', None, e))
        else:
            q(('success', resp, result))

        # using trigger can result in a missed on_success event
        self._trigger_result()

        # clean ourself when the queue is empty
        while len(self._queue):
            sleep(.1)
            self._trigger_result()

        # ok, authorize the GC to clean us.
        if self in g_requests:
            g_requests.remove(self)

    def _fetch_url(self, url, body, headers, q):
        # Parse and fetch the current url
        trigger = self._trigger_result
        chunk_size = self._chunk_size
        report_progress = self.on_progress is not None
        timeout = self._timeout
        file_path = self.file_path
        ca_file = self.ca_file
        verify = self.verify

        if self._debug:
            Logger.debug('UrlRequest: {0} Fetch url <{1}>'.format(
                id(self), url))
            Logger.debug('UrlRequest: {0} - body: {1}'.format(
                id(self), body))
            Logger.debug('UrlRequest: {0} - headers: {1}'.format(
                id(self), headers))

        # parse url
        parse = urlparse(url)

        # translate scheme to connection class
        cls = self.get_connection_for_scheme(parse.scheme)

        # correctly determine host/port
        port = None
        host = parse.netloc.split(':')
        if len(host) > 1:
            port = int(host[1])
        host = host[0]

        # reconstruct path to pass on the request
        path = parse.path
        if parse.params:
            path += ';' + parse.params
        if parse.query:
            path += '?' + parse.query
        if parse.fragment:
            path += '#' + parse.fragment

        # create connection instance
        args = {}
        if timeout is not None:
            args['timeout'] = timeout

        if ca_file is not None and hasattr(ssl, 'create_default_context'):
            ctx = ssl.create_default_context(cafile=ca_file)
            ctx.verify_mode = ssl.CERT_REQUIRED
            args['context'] = ctx

        if not verify and parse.scheme == 'https' and (
            hasattr(ssl, 'create_default_context')):
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            args['context'] = ctx

        if self._proxy_host:
            Logger.debug('UrlRequest: {0} - proxy via {1}:{2}'.format(
                id(self), self._proxy_host, self._proxy_port
            ))
            req = cls(self._proxy_host, self._proxy_port, **args)
            if parse.scheme == 'https':
                req.set_tunnel(host, port, self._proxy_headers)
            else:
                path = urlunparse(parse)
        else:
            req = cls(host, port, **args)

        # send request
        method = self._method
        if method is None:
            method = 'GET' if body is None else 'POST'
        req.request(method, path, body, headers or {})

        # read header
        resp = req.getresponse()

        # read content
        if report_progress or file_path is not None:
            try:
                total_size = int(resp.getheader('content-length'))
            except:
                total_size = -1

            # before starting the download, send a fake progress to permit the
            # user to initialize his ui
            if report_progress:
                q(('progress', resp, (0, total_size)))

            def get_chunks(fd=None):
                bytes_so_far = 0
                result = b''
                while 1:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break

                    if fd:
                        fd.write(chunk)
                    else:
                        result += chunk

                    bytes_so_far += len(chunk)
                    # report progress to user
                    if report_progress:
                        q(('progress', resp, (bytes_so_far, total_size)))
                        trigger()
                return bytes_so_far, result

            if file_path is not None:
                with open(file_path, 'wb') as fd:
                    bytes_so_far, result = get_chunks(fd)
            else:
                bytes_so_far, result = get_chunks()

            # ensure that results are dispatched for the last chunk,
            # avoid trigger
            if report_progress:
                q(('progress', resp, (bytes_so_far, total_size)))
                trigger()
        else:
            result = resp.read()
            try:
                if isinstance(result, bytes):
                    result = result.decode('utf-8')
            except UnicodeDecodeError:
                # if it's an image? decoding would not work
                pass
        req.close()

        # return everything
        return result, resp

    def get_connection_for_scheme(self, scheme):
        '''Return the Connection class for a particular scheme.
        This is an internal function that can be expanded to support custom
        schemes.

        Actual supported schemes: http, https.
        '''
        if scheme == 'http':
            return HTTPConnection
        elif scheme == 'https' and HTTPSConnection is not None:
            return HTTPSConnection
        else:
            raise Exception('No class for scheme %s' % scheme)

    def decode_result(self, result, resp):
        '''Decode the result fetched from url according to his Content-Type.
        Currently supports only application/json.
        '''
        # Entry to decode url from the content type.
        # For example, if the content type is a json, it will be automatically
        # decoded.
        content_type = resp.getheader('Content-Type', None)
        if content_type is not None:
            ct = content_type.split(';')[0]
            if ct == 'application/json':
                if isinstance(result, bytes):
                    result = result.decode('utf-8')
                try:
                    return loads(result)
                except:
                    return result
        return result

    def _dispatch_result(self, dt):
        while True:
            # Read the result pushed on the queue, and dispatch to the client
            try:
                result, resp, data = self._queue.pop()
            except IndexError:
                return
            if resp:
                # XXX usage of dict can be dangerous if multiple headers
                # are set even if it's invalid. But it look like it's ok
                # ?  http://stackoverflow.com/questions/2454494/..
                # ..urllib2-multiple-set-cookie-headers-in-response
                self._resp_headers = dict(resp.getheaders())
                self._resp_status = resp.status
            if result == 'success':
                status_class = resp.status // 100

                if status_class in (1, 2):
                    if self._debug:
                        Logger.debug('UrlRequest: {0} Download finished with'
                                     ' {1} datalen'.format(id(self),
                                                           len(data)))
                    self._is_finished = True
                    self._result = data
                    if self.on_success:
                        func = self.on_success()
                        if func:
                            func(self, data)

                elif status_class == 3:
                    if self._debug:
                        Logger.debug('UrlRequest: {} Download '
                                     'redirected'.format(id(self)))
                    self._is_finished = True
                    self._result = data
                    if self.on_redirect:
                        func = self.on_redirect()
                        if func:
                            func(self, data)

                elif status_class in (4, 5):
                    if self._debug:
                        Logger.debug('UrlRequest: {} Download failed with '
                                     'http error {}'.format(id(self),
                                                            resp.status))
                    self._is_finished = True
                    self._result = data
                    if self.on_failure:
                        func = self.on_failure()
                        if func:
                            func(self, data)

            elif result == 'error':
                if self._debug:
                    Logger.debug('UrlRequest: {0} Download error '
                                 '<{1}>'.format(id(self), data))
                self._is_finished = True
                self._error = data
                if self.on_error:
                    func = self.on_error()
                    if func:
                        func(self, data)

            elif result == 'progress':
                if self._debug:
                    Logger.debug('UrlRequest: {0} Download progress '
                                 '{1}'.format(id(self), data))
                if self.on_progress:
                    func = self.on_progress()
                    if func:
                        func(self, data[0], data[1])

            else:
                assert(0)

    @property
    def is_finished(self):
        '''Return True if the request has finished, whether it's a
        success or a failure.
        '''
        return self._is_finished

    @property
    def result(self):
        '''Return the result of the request.
        This value is not determined until the request is finished.
        '''
        return self._result

    @property
    def resp_headers(self):
        '''If the request has been completed, return a dictionary containing
        the headers of the response. Otherwise, it will return None.
        '''
        return self._resp_headers

    @property
    def resp_status(self):
        '''Return the status code of the response if the request is complete,
        otherwise return None.
        '''
        return self._resp_status

    @property
    def error(self):
        '''Return the error of the request.
        This value is not determined until the request is completed.
        '''
        return self._error

    @property
    def chunk_size(self):
        '''Return the size of a chunk, used only in "progress" mode (when
        on_progress callback is set.)
        '''
        return self._chunk_size

    def wait(self, delay=0.5):
        '''Wait for the request to finish (until :attr:`resp_status` is not
        None)

        .. note::
            This method is intended to be used in the main thread, and the
            callback will be dispatched from the same thread
            from which you're calling.

        .. versionadded:: 1.1.0
        '''
        while self.resp_status is None:
            self._dispatch_result(delay)
            sleep(delay)


if __name__ == '__main__':

    from pprint import pprint

    def on_success(req, result):
        pprint('Got the result:')
        pprint(result)

    def on_error(req, error):
        pprint('Got an error:')
        pprint(error)

    req = UrlRequest('https://en.wikipedia.org/w/api.php?format'
        '=json&action=query&titles=Kivy&prop=revisions&rvprop=content',
        on_success, on_error)
    while not req.is_finished:
        sleep(1)
        Clock.tick()

    print('result =', req.result)
    print('error =', req.error)
