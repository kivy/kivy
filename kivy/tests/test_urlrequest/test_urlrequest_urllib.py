'''
UrlRequest tests
================

These tests exercise the ``urllib``-backed UrlRequest implementation
against a local ``pytest-httpserver`` instance instead of public services
like ``httpbin.org``. Running everything in-process makes the suite both
fast and deterministic, eliminating the historical CI flakiness that
came from depending on third-party HTTP services.
'''
import json
import socket
import threading
from base64 import b64encode
from datetime import datetime
from time import sleep
from urllib.parse import urlparse, urlunparse

import pytest

from kivy.network.urlrequest import UrlRequestUrllib as UrlRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# 'finish' is included because, when ``on_finish`` is registered, it is
# the very last callback dispatched after the terminal event (success /
# redirect / error / failure) and therefore the right thing to wait for.
TERMINAL_EVENTS = ('success', 'redirect', 'error', 'failure', 'finish')


def wait_for_terminal_event(kivy_clock, queue, timeout=10):
    """Wait until the test queue's last event is a terminal one.

    Polling ``UrlRequest.is_finished`` is racy: depending on Clock
    scheduling, the worker thread may have produced its terminal item
    before the main-thread Clock dispatcher has actually delivered every
    pending ``progress`` event to the registered callback. By keying off
    the queue contents instead we observe the same state the assertions
    do.
    """
    start = datetime.now()
    while True:
        if queue and queue[-1][1] in TERMINAL_EVENTS:
            return
        if (datetime.now() - start).total_seconds() > timeout:
            break
        kivy_clock.tick()
        sleep(.05)
    raise AssertionError(
        f"Timed out waiting for a terminal event; queue={list(queue)!r}"
    )


def ensure_called_from_thread(queue):
    """Ensures every callback was dispatched from this (main) thread."""
    tid = threading.get_ident()
    for item in queue:
        assert item[0] == tid, f"Callback dispatched from wrong thread: {item!r}"


def check_progress_then_terminal(queue, expected=('success', 'redirect')):
    """Assert the queue follows the expected ``progress*`` + terminal pattern.

    ``expected`` is the set of acceptable terminal event names. The default
    matches the historical "happy path" assertion. The first and
    second-to-last events must be ``progress``, the last must be in
    ``expected``, the initial progress must report 0 bytes so far, and
    the final progress must report ``bytes_so_far == total_size``.
    """
    assert len(queue) >= 3, f"Expected >=3 events, got {list(queue)!r}"
    assert queue[0][1] == 'progress'
    assert queue[-2][1] == 'progress'
    assert queue[-1][1] in expected, \
        f"Expected terminal in {expected!r}, got {queue[-1]!r}"
    assert queue[0][2][0] == 0
    assert queue[-2][2][0] == queue[-2][2][1]


class UrlRequestQueue:

    def __init__(self):
        self.queue = []

    def _on_success(self, req, *args):
        self.queue.append((threading.get_ident(), 'success', args))

    def _on_redirect(self, req, *args):
        self.queue.append((threading.get_ident(), 'redirect', args))

    def _on_error(self, req, *args):
        self.queue.append((threading.get_ident(), 'error', args))

    def _on_failure(self, req, *args):
        self.queue.append((threading.get_ident(), 'failure', args))

    def _on_progress(self, req, *args):
        self.queue.append((threading.get_ident(), 'progress', args))

    def _on_finish(self, req, *args):
        self.queue.append((threading.get_ident(), 'finish', args))


def _basic_auth_header(user, password):
    token = b64encode(f"{user}:{password}".encode('utf-8')).decode('utf-8')
    return {'Authorization': f'Basic {token}'}


def _embed_userinfo(url, user, password):
    """Insert ``user:password@`` into ``url``'s authority component."""
    parsed = urlparse(url)
    netloc = f"{user}:{password}@{parsed.hostname}"
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    return urlunparse(parsed._replace(netloc=netloc))


def _grab_unused_port():
    """Bind a temporary loopback socket, return its port, then release.

    Used by ``test_on_error`` to obtain an address that will refuse a TCP
    connection. There is a small race window before the OS could rebind
    the port, but on a CI runner during a single test the chance of
    collision is negligible.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]
    finally:
        s.close()


# ---------------------------------------------------------------------------
# Server route registration
# ---------------------------------------------------------------------------

def _register_basic_auth_route(server, user, password):
    """Register a ``/basic-auth/<user>/<password>`` endpoint on ``server``.

    Mirrors the ``httpbin`` semantics used by previous revisions of these
    tests: returns a small JSON object on success and 401 otherwise.
    """
    expected = _basic_auth_header(user, password)['Authorization']
    path = f"/basic-auth/{user}/{password}"

    server.expect_request(path, headers={'Authorization': expected}) \
        .respond_with_json({'authenticated': True, 'user': user})
    server.expect_request(path) \
        .respond_with_data('Unauthorized', status=401)


def _register_get_route(server, path='/get', body=b'a' * 4096):
    """Register a ``/get`` endpoint that returns a sized payload.

    The body is sized so that with a small ``chunk_size`` (the tests
    pass ``chunk_size=512``) ``UrlRequest`` emits a handful of
    ``on_progress`` events before the terminal one. The default
    ``chunk_size`` of 8192 would yield only a single chunk for this
    payload, so callers exercising the progress callback should pass a
    smaller ``chunk_size``.
    """
    server.expect_request(path).respond_with_data(
        body, content_type='application/octet-stream'
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.timeout(30)
def test_callbacks(kivy_clock, httpserver):
    """A plain GET fires progress* + success on the main thread."""
    _register_get_route(httpserver)
    obj = UrlRequestQueue()

    req = UrlRequest(
        httpserver.url_for('/get'),
        on_success=obj._on_success,
        on_progress=obj._on_progress,
        on_error=obj._on_error,
        on_redirect=obj._on_redirect,
        chunk_size=512,
        debug=True,
    )
    wait_for_terminal_event(kivy_clock, obj.queue)
    assert req.is_finished

    ensure_called_from_thread(obj.queue)
    check_progress_then_terminal(obj.queue)


@pytest.mark.timeout(30)
def test_auth_header(kivy_clock, httpserver):
    """An explicit Authorization header is forwarded to the server."""
    _register_basic_auth_route(httpserver, 'user', 'passwd')
    obj = UrlRequestQueue()
    head = _basic_auth_header('user', 'passwd')

    req = UrlRequest(
        httpserver.url_for('/basic-auth/user/passwd'),
        on_success=obj._on_success,
        on_progress=obj._on_progress,
        on_error=obj._on_error,
        on_redirect=obj._on_redirect,
        req_headers=head,
        debug=True,
    )
    wait_for_terminal_event(kivy_clock, obj.queue)
    assert req.is_finished

    ensure_called_from_thread(obj.queue)
    check_progress_then_terminal(obj.queue)
    assert obj.queue[-1][2] == ({'authenticated': True, 'user': 'user'},)


@pytest.mark.timeout(30)
def test_auth_auto(kivy_clock, httpserver):
    """``user:passwd@`` in the URL is converted into a Basic auth header."""
    _register_basic_auth_route(httpserver, 'user', 'passwd')
    obj = UrlRequestQueue()
    url = _embed_userinfo(
        httpserver.url_for('/basic-auth/user/passwd'), 'user', 'passwd'
    )

    req = UrlRequest(
        url,
        on_success=obj._on_success,
        on_progress=obj._on_progress,
        on_error=obj._on_error,
        on_redirect=obj._on_redirect,
        debug=True,
    )
    wait_for_terminal_event(kivy_clock, obj.queue)
    assert req.is_finished

    ensure_called_from_thread(obj.queue)
    check_progress_then_terminal(obj.queue)
    assert obj.queue[-1][2] == ({'authenticated': True, 'user': 'user'},)


@pytest.mark.timeout(30)
@pytest.mark.parametrize('scheme', ('http', 'https'))
def test_ca_file(request, kivy_clock, scheme, ca_cert_path):
    """Passing a `ca_file` should not crash on either scheme, refs #6946."""
    if scheme == 'http':
        server = request.getfixturevalue('httpserver')
    else:
        server = request.getfixturevalue('httpsserver')

    _register_get_route(server)
    obj = UrlRequestQueue()

    req = UrlRequest(
        server.url_for('/get'),
        on_success=obj._on_success,
        on_progress=obj._on_progress,
        on_error=obj._on_error,
        on_redirect=obj._on_redirect,
        ca_file=ca_cert_path,
        chunk_size=512,
        debug=True,
    )
    wait_for_terminal_event(kivy_clock, obj.queue)
    assert req.is_finished

    ensure_called_from_thread(obj.queue)
    check_progress_then_terminal(obj.queue)


@pytest.mark.timeout(30)
def test_on_finish(kivy_clock, httpserver):
    """``on_finish`` fires after the terminal callback for a successful GET."""
    httpserver.expect_request('/get').respond_with_data(b'ok')
    obj = UrlRequestQueue()

    req = UrlRequest(
        httpserver.url_for('/get'),
        on_success=obj._on_success,
        on_finish=obj._on_finish,
        debug=True,
    )
    wait_for_terminal_event(kivy_clock, obj.queue)
    assert req.is_finished

    ensure_called_from_thread(obj.queue)
    assert [event for _, event, _ in obj.queue] == ['success', 'finish']


@pytest.mark.timeout(30)
def test_on_redirect(kivy_clock, httpserver):
    """A 3xx response invokes ``on_redirect`` rather than ``on_success``."""
    httpserver.expect_request('/redirect').respond_with_data(
        b'', status=302,
        headers={'Location': httpserver.url_for('/elsewhere')},
    )
    obj = UrlRequestQueue()

    req = UrlRequest(
        httpserver.url_for('/redirect'),
        on_success=obj._on_success,
        on_progress=obj._on_progress,
        on_error=obj._on_error,
        on_redirect=obj._on_redirect,
        on_failure=obj._on_failure,
        debug=True,
    )
    wait_for_terminal_event(kivy_clock, obj.queue)
    assert req.is_finished

    ensure_called_from_thread(obj.queue)
    check_progress_then_terminal(obj.queue, expected=('redirect',))
    assert req.resp_status in (301, 302, 303, 307, 308)


@pytest.mark.timeout(30)
def test_on_failure(kivy_clock, httpserver):
    """A 4xx/5xx response invokes ``on_failure`` rather than ``on_error``."""
    httpserver.expect_request('/missing').respond_with_data(
        b'not found', status=404, content_type='text/plain',
    )
    obj = UrlRequestQueue()

    req = UrlRequest(
        httpserver.url_for('/missing'),
        on_success=obj._on_success,
        on_progress=obj._on_progress,
        on_error=obj._on_error,
        on_redirect=obj._on_redirect,
        on_failure=obj._on_failure,
        chunk_size=64,
        debug=True,
    )
    wait_for_terminal_event(kivy_clock, obj.queue)
    assert req.is_finished

    ensure_called_from_thread(obj.queue)
    check_progress_then_terminal(obj.queue, expected=('failure',))
    assert req.resp_status == 404


@pytest.mark.timeout(30)
def test_on_error(kivy_clock):
    """A connection error invokes ``on_error`` with the underlying exception.

    Points the request at a closed loopback port so the OS responds with
    a TCP RST immediately, making the test fast and deterministic.
    """
    port = _grab_unused_port()
    obj = UrlRequestQueue()

    req = UrlRequest(
        f'http://127.0.0.1:{port}/get',
        on_success=obj._on_success,
        on_progress=obj._on_progress,
        on_error=obj._on_error,
        on_redirect=obj._on_redirect,
        on_failure=obj._on_failure,
        debug=True,
    )
    wait_for_terminal_event(kivy_clock, obj.queue)
    assert req.is_finished

    ensure_called_from_thread(obj.queue)
    assert [event for _, event, _ in obj.queue] == ['error']
    assert req.error is not None
    assert isinstance(req.error, OSError)


@pytest.mark.timeout(30)
def test_post(kivy_clock, httpserver):
    """Setting ``req_body`` switches the method to POST and forwards the body."""
    payload = b'name=value&other=thing'
    httpserver.expect_request(
        '/submit', method='POST', data=payload,
    ).respond_with_data(b'ok')
    obj = UrlRequestQueue()

    req = UrlRequest(
        httpserver.url_for('/submit'),
        req_body=payload,
        on_success=obj._on_success,
        on_finish=obj._on_finish,
        debug=True,
    )
    wait_for_terminal_event(kivy_clock, obj.queue)
    assert req.is_finished

    ensure_called_from_thread(obj.queue)
    assert [event for _, event, _ in obj.queue] == ['success', 'finish']
    assert req.resp_status == 200


@pytest.mark.timeout(30)
def test_decode_json(kivy_clock, httpserver):
    """An ``application/json`` response is auto-parsed into a Python object."""
    httpserver.expect_request('/data').respond_with_json({'a': 1, 'b': [2, 3]})
    obj = UrlRequestQueue()

    req = UrlRequest(
        httpserver.url_for('/data'),
        on_success=obj._on_success,
        debug=True,
    )
    wait_for_terminal_event(kivy_clock, obj.queue)
    assert req.is_finished

    ensure_called_from_thread(obj.queue)
    assert obj.queue[-1][1] == 'success'
    (result,) = obj.queue[-1][2]
    assert result == {'a': 1, 'b': [2, 3]}


@pytest.mark.timeout(30)
def test_decode_disabled(kivy_clock, httpserver):
    """``decode=False`` bypasses the application/json auto-parser."""
    body = {'a': 1, 'b': [2, 3]}
    httpserver.expect_request('/data').respond_with_json(body)
    obj = UrlRequestQueue()

    req = UrlRequest(
        httpserver.url_for('/data'),
        on_success=obj._on_success,
        decode=False,
        debug=True,
    )
    wait_for_terminal_event(kivy_clock, obj.queue)
    assert req.is_finished

    ensure_called_from_thread(obj.queue)
    assert obj.queue[-1][1] == 'success'
    (result,) = obj.queue[-1][2]
    # Still a string (utf-8 decoded), but never passed through json.loads.
    assert isinstance(result, str)
    assert json.loads(result) == body


@pytest.mark.timeout(30)
def test_file_path(kivy_clock, httpserver, tmp_path):
    """``file_path`` writes the response body to disk instead of memory."""
    body = b'\x00\x01\x02binary payload\xff' * 64
    httpserver.expect_request('/blob').respond_with_data(
        body, content_type='application/octet-stream',
    )
    out_path = tmp_path / 'response.bin'
    obj = UrlRequestQueue()

    req = UrlRequest(
        httpserver.url_for('/blob'),
        on_success=obj._on_success,
        on_progress=obj._on_progress,
        file_path=str(out_path),
        chunk_size=64,
        debug=True,
    )
    wait_for_terminal_event(kivy_clock, obj.queue)
    assert req.is_finished

    ensure_called_from_thread(obj.queue)
    assert obj.queue[-1][1] == 'success'
    assert out_path.exists()
    assert out_path.read_bytes() == body
