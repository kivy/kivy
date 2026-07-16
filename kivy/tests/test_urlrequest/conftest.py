"""
Shared fixtures for UrlRequest tests.

Provides a ``trustme``-backed CA so that an ``HTTPServer`` from
``pytest-httpserver`` can be served over HTTPS in addition to the default
HTTP one, and exposes the path of the CA's PEM file as ``ca_cert_path``
so the client (UrlRequest) can validate the local server's certificate
via the ``ca_file=`` parameter.

Two server fixtures are exposed:

* ``httpserver`` (provided by ``pytest-httpserver``): plain HTTP, bound
  to ``127.0.0.1`` on a random port via the
  ``httpserver_listen_address`` override below.
* ``httpsserver``: a separately constructed HTTPS server backed by the
  same ``trustme`` CA used for ``ca_cert_path``.

Both servers bind explicitly to ``127.0.0.1``. Binding to ``localhost``
turned out to be a 1000x slowdown on Windows: the client side resolves
``localhost`` to ``::1`` first and waits ~2 seconds for the IPv6
connection attempt to time out before falling back to IPv4 (the server
only listens on IPv4). Using ``127.0.0.1`` avoids the dual-stack
fallback entirely.

Also installs a session-scoped, autouse stub for ``socket.getfqdn``.
``werkzeug``'s ``BaseWSGIServer`` (which backs ``pytest-httpserver``)
calls ``socket.getfqdn(host)`` after binding to populate
``server_name``. On some CI hosts (notably macOS GitHub runners) the
reverse-DNS lookup for the loopback address hangs for tens of seconds,
which trips ``pytest-timeout`` before the server even finishes
starting. The FQDN is purely cosmetic for our loopback servers, so we
short-circuit it.
"""
import socket
import ssl

import pytest


@pytest.fixture(scope="session", autouse=True)
def _fast_loopback_getfqdn():
    """Bypass slow reverse-DNS for loopback addresses during this session."""
    original = socket.getfqdn
    loopback = {'', '0.0.0.0', '::', '127.0.0.1', '::1', 'localhost'}

    def _stub(name=''):
        if name in loopback:
            return 'localhost'
        return original(name)

    socket.getfqdn = _stub
    try:
        yield
    finally:
        socket.getfqdn = original


@pytest.fixture(scope="session")
def httpserver_listen_address():
    """Force ``pytest-httpserver`` to bind to ``127.0.0.1`` on a random port.

    Binding to ``127.0.0.1`` (rather than ``localhost``) avoids a ~2s
    IPv6 connection-timeout penalty on Windows when the client side
    tries ``::1`` first and the server only listens on IPv4.
    """
    return ("127.0.0.1", 0)


@pytest.fixture(scope="session")
def ca():
    trustme = pytest.importorskip("trustme")
    return trustme.CA()


@pytest.fixture(scope="session")
def ca_cert_path(ca, tmp_path_factory):
    cert_path = tmp_path_factory.mktemp("ca") / "ca.pem"
    ca.cert_pem.write_to_path(str(cert_path))
    return str(cert_path)


@pytest.fixture(scope="session")
def _https_ssl_context(ca):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    localhost_cert = ca.issue_cert("localhost", "127.0.0.1")
    localhost_cert.configure_cert(context)
    return context


@pytest.fixture(scope="session")
def _httpsserver_session(_https_ssl_context):
    pytest.importorskip("pytest_httpserver")
    from pytest_httpserver import HTTPServer

    server = HTTPServer(host="127.0.0.1", port=0, ssl_context=_https_ssl_context)
    server.start()
    try:
        yield server
    finally:
        if server.is_running():
            server.stop()


@pytest.fixture
def httpsserver(_httpsserver_session):
    """A pytest-httpserver instance serving over HTTPS.

    Mirrors the function-scoped/session-backed pattern used by
    pytest-httpserver's own ``httpserver`` fixture: the server is
    started once per session and reused across tests, with each test
    seeing a clean expectation slate.
    """
    yield _httpsserver_session
    _httpsserver_session.clear()
