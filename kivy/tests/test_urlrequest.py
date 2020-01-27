'''
UrlRequest tests
================
'''
import pytest
import threading

from time import sleep
from base64 import b64encode
import os


class UrlRequestQueue(object):

    queue = []

    def __init__(self, queue):
        super(UrlRequestQueue, self).__init__()
        self.queue = queue

    def _on_success(self, req, *args):
        self.queue.append((threading.get_ident(), 'success', args))

    def _on_redirect(self, req, *args):
        self.queue.append((threading.get_ident(), 'redirect', args))

    def _on_error(self, req, *args):
        self.queue.append((threading.get_ident(), 'error', args))

    def _on_progress(self, req, *args):
        self.queue.append((threading.get_ident(), 'progress', args))


def test_callbacks():
    if os.environ.get('NONETWORK'):
        return
    from kivy.network.urlrequest import UrlRequest
    from kivy.clock import Clock

    obj = UrlRequestQueue([])
    queue = obj.queue
    req = UrlRequest('http://google.com',
                     on_success=obj._on_success,
                     on_progress=obj._on_progress,
                     on_error=obj._on_error,
                     on_redirect=obj._on_redirect,
                     debug=True)

    # don't use wait, but maximum 10s timeout
    for i in range(50):
        Clock.tick()
        sleep(.5)
        if req.is_finished:
            break

    assert req.is_finished

    if req.error and req.error.errno == 11001:
        pytest.skip('Cannot connect to get address')

    # we should have 2 progress minimum and one success
    assert len(queue) >= 3

    # ensure the callback is called from this thread (main).
    tid = threading.get_ident()
    assert queue[0][0] == tid
    assert queue[-2][0] == tid
    assert queue[-1][0] == tid

    assert queue[0][1] == 'progress'
    assert queue[-2][1] == 'progress'
    assert queue[-1][1] in ('success', 'redirect')

    assert queue[0][2][0] == 0
    assert queue[-2][2][0] == queue[-2][2][1]


def test_auth_header():
    if os.environ.get('NONETWORK'):
        return
    from kivy.network.urlrequest import UrlRequest
    from kivy.clock import Clock

    obj = UrlRequestQueue([])
    queue = obj.queue
    head = {
        "Authorization": "Basic {}".format(b64encode(
            "{}:{}".format('user', 'passwd').encode('utf-8')
        ).decode('utf-8'))
    }
    req = UrlRequest(
        'http://httpbin.org/basic-auth/user/passwd',
        on_success=obj._on_success,
        on_progress=obj._on_progress,
        on_error=obj._on_error,
        on_redirect=obj._on_redirect,
        req_headers=head,
        debug=True
    )

    # don't use wait, but maximum 10s timeout
    for i in range(50):
        Clock.tick()
        sleep(.5)
        if req.is_finished:
            break

    assert req.is_finished

    if req.error and req.error.errno == 11001:
        pytest.skip('Cannot connect to get address')

    # we should have 2 progress minimum and one success
    assert len(queue) >= 3

    # ensure the callback is called from this thread (main).
    tid = threading.get_ident()
    assert queue[0][0] == tid
    assert queue[-2][0] == tid
    assert queue[-1][0] == tid

    assert queue[0][1] == 'progress'
    assert queue[-2][1] == 'progress'
    assert queue[-1][1] in ('success', 'redirect')
    assert queue[-1][2] == ({'authenticated': True, 'user': 'user'}, )

    assert queue[0][2][0] == 0
    assert queue[-2][2][0] == queue[-2][2][1]


def test_auth_auto():
    if os.environ.get('NONETWORK'):
        return
    from kivy.network.urlrequest import UrlRequest
    from kivy.clock import Clock

    obj = UrlRequestQueue([])
    queue = obj.queue
    req = UrlRequest(
        'http://user:passwd@httpbin.org/basic-auth/user/passwd',
        on_success=obj._on_success,
        on_progress=obj._on_progress,
        on_error=obj._on_error,
        on_redirect=obj._on_redirect,
        debug=True
    )

    # don't use wait, but maximum 10s timeout
    for i in range(50):
        Clock.tick()
        sleep(.5)
        if req.is_finished:
            break

    assert req.is_finished

    if req.error and req.error.errno == 11001:
        pytest.skip('Cannot connect to get address')

    # we should have 2 progress minimum and one success
    assert len(queue) >= 3

    # ensure the callback is called from this thread (main).
    tid = threading.get_ident()
    assert queue[0][0] == tid
    assert queue[-2][0] == tid
    assert queue[-1][0] == tid

    assert queue[0][1] == 'progress'
    assert queue[-2][1] == 'progress'
    assert queue[-1][1] in ('success', 'redirect')
    assert queue[-1][2] == ({'authenticated': True, 'user': 'user'}, )

    assert queue[0][2][0] == 0
    assert queue[-2][2][0] == queue[-2][2][1]
