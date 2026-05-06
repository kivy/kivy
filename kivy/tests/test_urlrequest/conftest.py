"""
Shared fixtures for UrlRequest tests.

Provides a ``trustme``-backed CA so that an ``HTTPServer`` from
``pytest-httpserver`` can be served over HTTPS in addition to the default
HTTP one, and exposes the path of the CA's PEM file as ``ca_cert_path``
so the client (UrlRequest) can validate the local server's certificate
via the ``ca_file=`` parameter.

Two server fixtures are exposed:

* ``httpserver`` (provided by ``pytest-httpserver``): plain HTTP.
* ``httpsserver``: a separately constructed HTTPS server backed by the
  same ``trustme`` CA used for ``ca_cert_path``.
"""
import ssl

import pytest


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


@pytest.fixture
def httpsserver(_https_ssl_context):
    """A pytest-httpserver instance serving over HTTPS."""
    pytest.importorskip("pytest_httpserver")
    from pytest_httpserver import HTTPServer

    server = HTTPServer(host="localhost", port=0, ssl_context=_https_ssl_context)
    server.start()
    yield server
    server.clear()
    if server.is_running():
        server.stop()
