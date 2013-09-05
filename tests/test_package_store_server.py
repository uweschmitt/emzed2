from contextlib import contextmanager


@contextmanager
def background_server(dir_):
    import emzed.server
    srv = emzed.server.PackageStoreServer(dir_)
    srv.start()
    try:
        yield srv
    finally:
        srv.stop()


def test_start_stop(tmpdir):
    with background_server(tmpdir.strpath) as srv:
        assert srv.is_alive()


def test_store_upload(tmpdir):
    import requests
    with background_server(tmpdir.strpath) as srv:  # noqa
        assert requests.get("http://localhost:54321/+password/test_account/test").ok
        assert requests.get("http://localhost:54321").json() == dict(packages=dict())
        assert requests.get("http://localhost:54321/test_account").json() == dict(packages=dict())
