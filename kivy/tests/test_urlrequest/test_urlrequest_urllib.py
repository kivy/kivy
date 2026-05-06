'''
UrlRequest tests
================

These tests exercise the ``urllib``-backed UrlRequest implementation
against a local ``pytest-httpserver`` instance instead of public services
like ``httpbin.org``. Running everything in-process makes the suite both
fast and deterministic, eliminating the historical CI flakiness that
came from depending on third-party HTTP services.
'''
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

TERMINAL_EVENTS = ('success', 'redirect', 'error', 'failure')


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


def check_progress_then_terminal(queue):
    """Assert the queue follows the expected progress* + terminal pattern."""
    assert len(queue) >= 3, f"Expected >=3 events, got {list(queue)!r}"
    assert queue[0][1] == 'progress'
    assert queue[-2][1] == 'progress'
    assert queue[-1][1] in ('success', 'redirect')
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

    The body is intentionally larger than the default ``chunk_size`` of
    8192 bytes is *not* required; we just need enough bytes that
    ``UrlRequest`` actually emits a couple of ``on_progress`` events
    before the terminal one.
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
