import os

import pytest

from kivy.network.urlrequest import UrlRequestUrllib as UrlRequest
from kivy.tests.test_urlrequest.test_urlrequest_urllib import UrlRequestQueue, \
    wait_request_is_finished, ensure_called_from_thread, check_queue_values


@pytest.mark.skipif(os.environ.get('NONETWORK'), reason="No network")
def test_binding(kivy_clock):
    obj = UrlRequestQueue([])
    queue = obj.queue
    req = UrlRequest(
        'https://google.com',
        debug=True,
        start=False,
    )

    req.bind(
        on_success=obj._on_success,
        on_progress=obj._on_progress,
        on_error=obj._on_error,
        on_redirect=obj._on_redirect,
    )

    req.start()

    wait_request_is_finished(kivy_clock, req)

    if req.error and req.error.errno == 11001:
        pytest.skip('Cannot connect to get address')

    ensure_called_from_thread(queue)
    check_queue_values(queue)


@pytest.mark.skipif(os.environ.get('NONETWORK'), reason="No network")
def test_multiple_binding(kivy_clock):
    obj = UrlRequestQueue([])
    queue = obj.queue
    req = UrlRequest(
        'https://google.com',
        debug=True,
        start=False,
    )

    # separate binding
    req.bind(
        on_success=obj._on_success,
        on_redirect=obj._on_redirect,
    )
    req.bind(
        on_success=obj._on_success,
        on_redirect=obj._on_redirect,
    )

    # multiple binding
    req.bind(on_progress=[obj._on_progress, obj._on_progress])

    # check callback lists
    assert len(getattr(req, 'on_success')) == 2
    assert len(getattr(req, 'on_redirect')) == 2
    assert len(getattr(req, 'on_progress')) == 2

    req.start()

    wait_request_is_finished(kivy_clock, req)

    if req.error and req.error.errno == 11001:
        pytest.skip('Cannot connect to get address')

    ensure_called_from_thread(queue)

    # request may be successful or redirected if source changes. Either way,
    # assert that we get two queue elements corresponding to callbacks.
    filtered_len = len([x for x in queue if x[1] in ('success', 'redirect')])
    assert filtered_len >= 2

    # On progress should be dispatched at least twice per callback. Assert that
    # we have at least four queue elements, two from each progress callback.
    filtered_len = len([x for x in queue if x[1] == 'progress'])
    assert filtered_len >= 4
