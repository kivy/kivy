"""Raw responses must retain their bytes with either HTTP backend."""
import pytest

from kivy.network.urlrequest import UrlRequestRequests, UrlRequestUrllib


@pytest.mark.parametrize('request_class', [UrlRequestUrllib, UrlRequestRequests])
@pytest.mark.parametrize('report_progress', [False, True])
@pytest.mark.parametrize('payload', [b'\x00binary', 'café'.encode('utf-8')])
@pytest.mark.timeout(30)
def test_decode_false_preserves_bytes(
        kivy_clock, httpserver, request_class, report_progress, payload):
    httpserver.expect_request('/raw').respond_with_data(
        payload, content_type='application/octet-stream')
    results = []
    request = request_class(
        httpserver.url_for('/raw'), decode=False,
        on_success=lambda request, result: results.append(result),
        on_progress=(lambda *args: None) if report_progress else None)
    request.wait(delay=.01)
    assert request.error is None
    assert results == [payload]
    assert isinstance(results[0], bytes)


@pytest.mark.parametrize('request_class', [UrlRequestUrllib, UrlRequestRequests])
@pytest.mark.parametrize('report_progress', [False, True])
@pytest.mark.parametrize('payload, content_type', [
    (b'{"ok": true}', 'application/json'),
    (b'plain text', 'text/plain'),
    (b'\xffbinary', 'application/octet-stream'),
])
@pytest.mark.timeout(30)
def test_default_decoding_unchanged(
        kivy_clock, httpserver, request_class, report_progress,
        payload, content_type):
    httpserver.expect_request('/default').respond_with_data(
        payload, content_type=content_type)
    results = []
    request = request_class(
        httpserver.url_for('/default'),
        on_success=lambda request, result: results.append(result),
        on_progress=(lambda *args: None) if report_progress else None)
    request.wait(delay=.01)
    assert request.error is None
    if content_type == 'application/json':
        assert results == [{'ok': True}]
    elif content_type == 'text/plain' and not report_progress:
        assert results == ['plain text']
    else:
        assert results == [payload]
