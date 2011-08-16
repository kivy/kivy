'''
Url Request
===========

.. versionadded:: 1.0.8

You can use the :class:`UrlRequest` to make asynchronous request on the web, and
get the result when the request is completed. The spirit is the same as XHR
object in Javascript.

The content is also decoded, aka for now, if the Content-Type is
application/json, the result will be automatically passed through json.loads.


The syntax to create a request::

    from kivy.network.urlrequest import UrlRequest
    req = UrlRequest(url, callback_success, callback_error, body, headers)


Only the first argument is mandatory, all the rest is optional.
By default, a "GET" request will be done. If :data:`UrlRequest.req_body` is not
None, a "POST" request will be done. It's up to you to adjust
:data:`UrlRequest.req_headers` if necessary.


Example of fetching twitter trends::

    def got_twitter_trends(req, result):
        trends = result['trends']
        print 'Last %d twitter trends:' % len(trends),
        for trend in trends:
            print trend['name'],
        print '!'

    req = UrlRequest('http://api.twitter.com/1/trends.json', 
            got_twitter_trends)

Example of Posting data (adapted from httplib example)::

    import urllib

    def bug_posted(req, result):
        print 'Our bug is posted !'
        print result

    params = urllib.urlencode({'@number': 12524, '@type': 'issue', '@action': 'show'})
    headers = {'Content-type': 'application/x-www-form-urlencoded',
              'Accept': 'text/plain'}
    req = UrlRequest('bugs.python.org', on_success=bug_posted, body=params,
            headers=headers)


'''

from collections import deque
from threading import Thread
from json import loads
from httplib import HTTPConnection, HTTPSConnection
from urlparse import urlparse
from kivy.clock import Clock


class UrlRequest(Thread):
    '''Url request. See module documentation for usage.

    :Parameters:
        `url`: str
            Complete url string to call.
        `on_success`: func or meth, default to None
            Callback function to call when the result have been fetched
        `on_error`: func or meth, default to None
            Callback function to call when an error happen
    '''

    def __init__(self, url, on_success=None, on_error=None, req_body=None,
            req_headers=None):
        super(UrlRequest, self).__init__()
        self._queue = deque()
        self._trigger_result = Clock.create_trigger(self._dispatch_result, 0)
        self.daemon = True
        self.on_success = on_success
        self.on_error = on_error
        self._result = None
        self._error = None
        self._is_finished = False

        #: Url of the request
        self.url = url

        #: Request body passed in __init__
        self.req_body = req_body

        #: Request headers passed in __init__
        self.req_headers = req_headers

        self.start()


    def run(self):
        q = self._queue.appendleft
        url = self.url
        req_body = self.req_body
        req_headers = self.req_headers
        result = e = None

        try:
            result, resp = self._fetch_url(url, req_body, req_headers)
            result = self.decode_result(result, resp)
        except Exception, e:
            pass

        if e is not None:
            q(('error', e))
        else:
            q(('success', result))

        self._trigger_result()

    def _fetch_url(self, url, body, headers):
        # Parse and fetch the current url

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

        # create connection instance
        req = cls(host, port)

        # reconstruct path to pass on the request
        path = parse.path
        if parse.query:
            path += '?' + parse.query
        if parse.fragment:
            path += '#' + parse.fragment

        # send request
        req.request('GET', path, body, headers)

        # read header
        resp = req.getresponse()

        # read content
        result = resp.read()
        req.close()

        # return everything
        return result, resp

    def get_connection_for_scheme(self, scheme):
        '''Return the Connection class from a particular scheme.
        This is an internal that can be expanded to support custom scheme.

        Actual supported schemes: http, https.
        '''
        if scheme == 'http':
            return HTTPConnection
        elif scheme == 'https':
            return HTTPSConnection
        else:
            raise Exception('No class for scheme %s' % scheme)

    def decode_result(self, result, resp):
        '''Decode the result fetched from url according to his Content-Type.
        Actually, only decode application/json.
        '''
        # Entry to decode url from the content type.
        # For example, if the content type is a json, it will be automatically
        # decoded.
        ct = resp.getheader('Content-Type', None).split(';')[0]
        if ct == 'application/json':
            try:
                return loads(result)
            except:
                return result
        return result

    def _dispatch_result(self, dt):
        # Read the result pushed on the queue, and dispatch to the client
        result, data = self._queue.pop()
        self._is_finished = True
        if result == 'success':
            self._result = data
            if self.on_success:
                self.on_success(self, data)
        elif result == 'error':
            self._error = data
            if self.on_error:
                self.on_error(self, data)
        else:
            assert(0)

    @property
    def is_finished(self):
        '''Return True if the request have finished, whatever is if it's a
        success or a failure.
        '''
        return self._is_finished

    @property
    def result(self):
        '''Return the result of the request.
        This value is not undeterminate until the request is finished.
        '''
        return self._result

    @property
    def error(self):
        '''Return the error of the request.
        This value is not undeterminate until the request is finished.
        '''
        return self._error




if __name__ == '__main__':

    from time import sleep
    from pprint import pprint

    def on_success(req, result):
        pprint('Got the result:')
        pprint(result)
    def on_error(req, error):
        pprint('Got an error:')
        pprint(error)


    req = UrlRequest('http://api.twitter.com/1/trends.json', 
            on_success, on_error)
    while not req.is_finished:
        sleep(1)
        Clock.tick()
        
    print 'result =', req.result
    print 'error =', req.error

