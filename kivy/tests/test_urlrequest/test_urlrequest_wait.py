'''Synchronous request completion without a running UI event loop.'''

import socket
import threading
from time import monotonic, sleep

import pytest

from kivy.network import urlrequest


@pytest.mark.parametrize('backend', [
    urlrequest.UrlRequestUrllib, urlrequest.UrlRequestRequests,
])
@pytest.mark.parametrize('status', [200, 500])
@pytest.mark.parametrize('progress', [False, True])
def test_wait_http_response(backend, status, progress, httpserver,
                           monkeypatch, kivy_clock):
    callbacks = []
    main_thread = threading.get_ident()

    def terminal(request, result):
        callbacks.append((threading.get_ident(), result))

    def on_progress(request, current, total):
        pass

    httpserver.expect_request('/wait').respond_with_data(
        'response', status=status, content_type='text/plain',
    )
    request = backend(
        httpserver.url_for('/wait'), timeout=1,
        on_success=terminal, on_failure=terminal,
        on_progress=on_progress if progress else None,
    )
    deadline = monotonic() + 3

    def bounded_sleep(delay):
        if threading.get_ident() == main_thread:
            assert monotonic() < deadline, 'wait did not receive a response'
        sleep(delay)

    monkeypatch.setattr(urlrequest, 'sleep', bounded_sleep)
    try:
        request.wait(delay=.001)
        # requests treats an HTTP-error Response as false, so the existing
        # dispatcher records its failure without populating resp_status.
        expected_status = None if backend is urlrequest.UrlRequestRequests \
            and status == 500 else status
        assert request.resp_status == expected_status
    finally:
        # Progress can expose a status before the body finishes. Keep draining
        # the dispatcher until the terminal callback lets the worker exit.
        while not request.is_finished:
            assert monotonic() < deadline, 'response did not finish'
            request._dispatch_result(0)
            sleep(.001)
        request.join(timeout=2)
        assert not request.is_alive()
    assert callbacks == [(main_thread, b'response' if progress else 'response')]
    assert request.error is None


@pytest.mark.parametrize('backend', [
    urlrequest.UrlRequestUrllib, urlrequest.UrlRequestRequests,
])
def test_wait_returns_after_transport_error(backend, monkeypatch, kivy_clock):
    callbacks = []
    main_thread = threading.get_ident()

    def on_error(request, error):
        callbacks.append(('error', threading.get_ident(), error))

    def on_finish(request):
        callbacks.append(('finish', threading.get_ident()))

    # Keep the port reserved, but do not listen: the real HTTP client gets a
    # connection refusal without depending on DNS or an external server.
    with socket.socket() as reserved:
        reserved.bind(('127.0.0.1', 0))
        port = reserved.getsockname()[1]
        request = backend(
            f'http://127.0.0.1:{port}/', timeout=1,
            on_error=on_error, on_finish=on_finish,
        )
        deadline = monotonic() + 3
        completed_sleeps = 0

        def bounded_sleep(delay):
            nonlocal completed_sleeps
            if threading.get_ident() == main_thread:
                assert monotonic() < deadline, 'wait did not complete'
                if request.is_finished:
                    completed_sleeps += 1
                    assert completed_sleeps <= 1, (
                        'wait kept polling after the transport error finished'
                    )
            sleep(delay)

        monkeypatch.setattr(urlrequest, 'sleep', bounded_sleep)
        try:
            request.wait(delay=.001)
            assert request.is_finished
            assert request.resp_status is None
            assert request.error is not None
            assert [event[0] for event in callbacks] == ['error', 'finish']
            assert all(event[1] == main_thread for event in callbacks)
            assert callbacks[0][2] is request.error
        finally:
            request._dispatch_result(0)
            request.join(timeout=2)
            assert not request.is_alive()
