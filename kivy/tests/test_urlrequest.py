'''
UrlRequest tests
================
'''
import pytest
import threading

from datetime import datetime
from time import sleep
from base64 import b64encode
import os


def wait_request_is_finished(kivy_clock, request, timeout=10):
    start_time = datetime.now()
    timed_out = False
    while not request.is_finished and not timed_out:
        kivy_clock.tick()
        sleep(.1)
        timed_out = (datetime.now() - start_time).total_seconds() > timeout
    assert request.is_finished


def ensure_called_from_thread(queue):
    """Ensures the callback is called from this thread (main)."""
    tid = threading.get_ident()
    assert queue[0][0] == tid
    assert queue[-2][0] == tid
    assert queue[-1][0] == tid


def check_queue_values(queue):
    """Helper function verifying the queue contains the expected values."""
    # we should have 2 progress minimum and one success
    assert len(queue) >= 3

    assert queue[0][1] == 'progress'
    assert queue[-2][1] == 'progress'
    assert queue[-1][1] in ('success', 'redirect')

    assert queue[0][2][0] == 0
    assert queue[-2][2][0] == queue[-2][2][1]


class UrlRequestQueue:

    def __init__(self, queue):
        self.queue = queue

    def _on_success(self, req, *args):
        self.queue.append((threading.get_ident(), 'success', args))

    def _on_redirect(self, req, *args):
        self.queue.append((threading.get_ident(), 'redirect', args))

    def _on_error(self, req, *args):
        self.queue.append((threading.get_ident(), 'error', args))

    def _on_progress(self, req, *args):
        self.queue.append((threading.get_ident(), 'progress', args))


@pytest.mark.skipif(os.environ.get('NONETWORK'), reason="No network")
def test_callbacks(kivy_clock):
    from kivy.network.urlrequest import UrlRequest
    obj = UrlRequestQueue([])
    queue = obj.queue
    req = UrlRequest('http://google.com',
                     on_success=obj._on_success,
                     on_progress=obj._on_progress,
                     on_error=obj._on_error,
                     on_redirect=obj._on_redirect,
                     debug=True)
    wait_request_is_finished(kivy_clock, req)

    if req.error and req.error.errno == 11001:
        pytest.skip('Cannot connect to get address')

    ensure_called_from_thread(queue)
    check_queue_values(queue)


@pytest.mark.skipif(os.environ.get('NONETWORK'), reason="No network")
def test_auth_header(kivy_clock):
    from kivy.network.urlrequest import UrlRequest
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
    wait_request_is_finished(kivy_clock, req)

    if req.error and req.error.errno == 11001:
        pytest.skip('Cannot connect to get address')

    ensure_called_from_thread(queue)
    check_queue_values(queue)
    assert queue[-1][2] == ({'authenticated': True, 'user': 'user'}, )


@pytest.mark.skipif(os.environ.get('NONETWORK'), reason="No network")
def test_auth_auto(kivy_clock):
    from kivy.network.urlrequest import UrlRequest
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
    wait_request_is_finished(kivy_clock, req)

    if req.error and req.error.errno == 11001:
        pytest.skip('Cannot connect to get address')

    ensure_called_from_thread(queue)
    check_queue_values(queue)
    assert queue[-1][2] == ({'authenticated': True, 'user': 'user'}, )


@pytest.mark.skipif(os.environ.get('nonetwork'), reason="no network")
@pytest.mark.parametrize("scheme", ("http", "https"))
def test_ca_file(kivy_clock, scheme):
    """Passing a `ca_file` should not crash on http scheme, refs #6946"""
    from kivy.network.urlrequest import UrlRequest
    import certifi
    obj = UrlRequestQueue([])
    queue = obj.queue
    req = UrlRequest(
        f"{scheme}://httpbin.org/get",
        on_success=obj._on_success,
        on_progress=obj._on_progress,
        on_error=obj._on_error,
        on_redirect=obj._on_redirect,
        ca_file=certifi.where(),
        debug=True
    )
    wait_request_is_finished(kivy_clock, req)

    if req.error and req.error.errno == 11001:
        pytest.skip('Cannot connect to get address')

    ensure_called_from_thread(queue)
    check_queue_values(queue)
