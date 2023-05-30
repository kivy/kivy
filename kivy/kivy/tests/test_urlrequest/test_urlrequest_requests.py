"""
UrlRequest tests
================
"""
import threading
from base64 import b64encode
from datetime import datetime
from time import sleep

import certifi
import pytest
import responses
from kivy.network.urlrequest import UrlRequestRequests as UrlRequest
from requests.auth import HTTPBasicAuth
from responses import matchers


class UrlRequestQueue:
    def __init__(self, queue):
        self.queue = queue

    def _on_success(self, req, *args):
        self.queue.append((threading.get_ident(), "success", args))

    def _on_redirect(self, req, *args):
        self.queue.append((threading.get_ident(), "redirect", args))

    def _on_error(self, req, *args):
        self.queue.append((threading.get_ident(), "error", args))

    def _on_failure(self, req, *args):
        self.queue.append((threading.get_ident(), "failure", args))

    def _on_progress(self, req, *args):
        self.queue.append((threading.get_ident(), "progress", args))

    def _on_finish(self, req, *args):
        self.queue.append((threading.get_ident(), "finish", args))


class TestCallbacks:
    url = "https://example.com"

    def _ensure_called_from_thread(self, queue):
        tid = threading.get_ident()

        for item in queue:
            assert item[0] == tid

    def _check_queue_values(self, queue_element, status):
        assert queue_element[1] == status

    def wait_request_is_finished(self, kivy_clock, request, timeout=10):
        start_time = datetime.now()
        timed_out = False

        while not request.is_finished and not timed_out:
            kivy_clock.tick()
            sleep(0.1)
            timed_out = (datetime.now() - start_time).total_seconds() > timeout

        assert request.is_finished

    @responses.activate
    def test_on_success(self, kivy_clock):
        _queue = UrlRequestQueue([])
        responses.get(
            self.url,
            body="{}",
            status=200,
            content_type="application/json",
        )

        req = UrlRequest(
            self.url,
            on_success=_queue._on_success,
            debug=True,
        )
        self.wait_request_is_finished(kivy_clock, req)

        processed_queue = _queue.queue
        assert len(processed_queue) == 1
        self._ensure_called_from_thread(processed_queue)
        self._check_queue_values(processed_queue[0], "success")

    @responses.activate
    def test_on_success_with_finish(self, kivy_clock):
        _queue = UrlRequestQueue([])
        responses.get(
            self.url,
            body="{}",
            status=200,
            content_type="application/json",
        )

        req = UrlRequest(
            self.url,
            on_success=_queue._on_success,
            on_finish=_queue._on_finish,
            debug=True,
        )
        self.wait_request_is_finished(kivy_clock, req)

        processed_queue = _queue.queue
        assert len(processed_queue) == 2
        self._ensure_called_from_thread(processed_queue)
        self._check_queue_values(processed_queue[0], "success")
        self._check_queue_values(processed_queue[1], "finish")

    @responses.activate
    def test_on_redirect(self, kivy_clock):
        _queue = UrlRequestQueue([])
        responses.get(
            self.url,
            body="{}",
            status=301,
            content_type="application/json",
        )

        req = UrlRequest(
            self.url,
            on_redirect=_queue._on_redirect,
            debug=True,
        )
        self.wait_request_is_finished(kivy_clock, req)

        processed_queue = _queue.queue
        assert len(processed_queue) == 1
        self._ensure_called_from_thread(processed_queue)
        self._check_queue_values(processed_queue[0], "redirect")

    @responses.activate
    def test_on_redirect_with_finish(self, kivy_clock):
        _queue = UrlRequestQueue([])
        responses.get(
            self.url,
            body="{}",
            status=301,
            content_type="application/json",
        )

        req = UrlRequest(
            self.url,
            on_redirect=_queue._on_redirect,
            on_finish=_queue._on_finish,
            debug=True,
        )
        self.wait_request_is_finished(kivy_clock, req)

        processed_queue = _queue.queue
        assert len(processed_queue) == 2
        self._ensure_called_from_thread(processed_queue)
        self._check_queue_values(processed_queue[0], "redirect")
        self._check_queue_values(processed_queue[1], "finish")

    @responses.activate
    def test_on_error(self, kivy_clock):
        _queue = UrlRequestQueue([])
        responses.get(
            self.url,
            body=Exception("..."),
            status=400,
            content_type="application/json",
        )

        req = UrlRequest(
            self.url,
            on_error=_queue._on_error,
            debug=True,
        )
        self.wait_request_is_finished(kivy_clock, req)

        processed_queue = _queue.queue
        assert len(processed_queue) == 1
        self._ensure_called_from_thread(processed_queue)
        self._check_queue_values(processed_queue[0], "error")

    @responses.activate
    def test_on_error_with_finis(self, kivy_clock):
        _queue = UrlRequestQueue([])
        responses.get(
            self.url,
            body=Exception("..."),
            status=400,
            content_type="application/json",
        )

        req = UrlRequest(
            self.url,
            on_error=_queue._on_error,
            on_finish=_queue._on_finish,
            debug=True,
        )
        self.wait_request_is_finished(kivy_clock, req)

        processed_queue = _queue.queue
        assert len(processed_queue) == 2
        self._ensure_called_from_thread(processed_queue)
        self._check_queue_values(processed_queue[0], "error")
        self._check_queue_values(processed_queue[1], "finish")

    @responses.activate
    def test_on_failure(self, kivy_clock):
        _queue = UrlRequestQueue([])
        responses.get(
            self.url,
            body="{}",
            status=400,
            content_type="application/json",
        )

        req = UrlRequest(
            self.url,
            on_failure=_queue._on_failure,
            debug=True,
        )
        self.wait_request_is_finished(kivy_clock, req)

        processed_queue = _queue.queue
        assert len(processed_queue) == 1
        self._ensure_called_from_thread(processed_queue)
        self._check_queue_values(processed_queue[0], "failure")

    @responses.activate
    def test_on_failure_with_finish(self, kivy_clock):
        _queue = UrlRequestQueue([])
        responses.get(
            self.url,
            body="{}",
            status=400,
            content_type="application/json",
        )

        req = UrlRequest(
            self.url,
            on_failure=_queue._on_failure,
            on_finish=_queue._on_finish,
            debug=True,
        )
        self.wait_request_is_finished(kivy_clock, req)

        processed_queue = _queue.queue
        assert len(processed_queue) == 2
        self._ensure_called_from_thread(processed_queue)
        self._check_queue_values(processed_queue[0], "failure")
        self._check_queue_values(processed_queue[1], "finish")

    @responses.activate
    def test_on_progress(self, kivy_clock):
        _queue = UrlRequestQueue([])
        responses.get(
            self.url,
            body="x" * 100,
            status=200,
            content_type="text/plain",
            auto_calculate_content_length=True
        )

        req = UrlRequest(
            self.url,
            on_progress=_queue._on_progress,
            chunk_size=70,
            debug=True,
        )
        self.wait_request_is_finished(kivy_clock, req)

        processed_queue = _queue.queue
        assert len(processed_queue) == 4
        self._ensure_called_from_thread(processed_queue)
        self._check_queue_values(processed_queue[0], "progress")
        self._check_queue_values(processed_queue[1], "progress")
        self._check_queue_values(processed_queue[2], "progress")
        self._check_queue_values(processed_queue[3], "progress")

    @responses.activate
    def test_on_progress_with_finish(self, kivy_clock):
        _queue = UrlRequestQueue([])
        responses.get(
            self.url,
            body="x" * 100,
            status=200,
            content_type="text/plain",
            auto_calculate_content_length=True
        )

        req = UrlRequest(
            self.url,
            on_progress=_queue._on_progress,
            on_finish=_queue._on_finish,
            chunk_size=70,
            debug=True,
        )
        self.wait_request_is_finished(kivy_clock, req)

        processed_queue = _queue.queue
        assert len(processed_queue) == 5
        self._ensure_called_from_thread(processed_queue)
        self._check_queue_values(processed_queue[0], "progress")
        self._check_queue_values(processed_queue[1], "progress")
        self._check_queue_values(processed_queue[2], "progress")
        self._check_queue_values(processed_queue[3], "progress")
        self._check_queue_values(processed_queue[4], "finish")

    @responses.activate
    def test_on_finish(self, kivy_clock):
        _queue = UrlRequestQueue([])
        responses.get(
            self.url,
            body="{}",
            status=400,
            content_type="application/json",
        )

        req = UrlRequest(
            self.url,
            on_finish=_queue._on_finish,
            debug=True,
        )
        self.wait_request_is_finished(kivy_clock, req)

        processed_queue = _queue.queue
        assert len(processed_queue) == 1
        self._ensure_called_from_thread(processed_queue)
        self._check_queue_values(processed_queue[0], "finish")

    @responses.activate
    def test_auth_header(self, kivy_clock):
        _queue = UrlRequestQueue([])
        head = {
            "Authorization": "Basic {}".format(
                b64encode(b"exampleuser:examplepassword").decode("utf-8")
            )
        }
        responses.get(
            self.url,
            body="{}",
            status=400,
            content_type="application/json",
            match=[matchers.header_matcher(head)],
        )

        req = UrlRequest(
            self.url,
            req_headers=head,
            on_finish=_queue._on_finish,
            debug=True,
            auth=HTTPBasicAuth("exampleuser", "examplepassword")
        )
        self.wait_request_is_finished(kivy_clock, req)

        processed_queue = _queue.queue
        assert len(processed_queue) == 1
        self._ensure_called_from_thread(processed_queue)
        self._check_queue_values(processed_queue[0], "finish")

    @pytest.mark.parametrize("scheme", ("http", "https"))
    @responses.activate
    def test_ca_file(self, scheme, kivy_clock):
        _queue = UrlRequestQueue([])
        responses.get(
            f"{scheme}://example.com",
            body="{}",
            status=400,
            content_type="application/json",
        )

        req = UrlRequest(
            f"{scheme}://example.com",
            on_finish=_queue._on_finish,
            ca_file=certifi.where(),
            debug=True,
        )
        self.wait_request_is_finished(kivy_clock, req)

        processed_queue = _queue.queue
        assert len(processed_queue) == 1
        self._ensure_called_from_thread(processed_queue)
        self._check_queue_values(processed_queue[0], "finish")
