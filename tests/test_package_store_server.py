from contextlib import contextmanager
import StringIO # cStringIO for upload does not work !
import requests

import emzed.package_store.server
import emzed.package_store.client as client


@contextmanager
def run_background_server(dir_, port):
    srv = emzed.package_store.server.BackgroundWebserver(dir_, port)
    srv.start()
    try:
        yield srv
    finally:
        srv.stop()


def test_start_stop(tmpdir):
    with run_background_server(tmpdir.strpath, 55555) as srv:
        assert srv.is_alive()


def test_store_upload(tmpdir):
    with run_background_server(tmpdir.strpath, 55556) as srv:

        # register user
        srv.create_account("test_account", "password")

        base_url = "http://localhost:55556"

        assert client.list_public_packages(base_url) == dict()

        # list public files of test_account
        assert client.list_files(base_url, "test_account", "/")  == []

        # upload public file
        data = StringIO.StringIO("abc123abccdd") # cStringIO for upload does not work !

        client.upload_file(base_url, "test_account", "password", "/abc.txt", data)
        assert client.list_files(base_url, "test_account", "/") == ["abc.txt"]
        assert client.download_file(base_url, "test_account", "/abc.txt") == data.getvalue()

        # upload hidden file
        data = StringIO.StringIO("abc123abccdd")

        client.upload_file(base_url, "test_account", "password", "/hidden/abcd.txt", data)
        assert client.list_files(base_url, "test_account", "/") == ["abc.txt"]
        assert client.list_files(base_url, "test_account", "/hidden") == ["abcd.txt"]
        assert client.download_file(base_url, "test_account", "/hidden/abc.txt") == data.getvalue()

        # list all public files
        assert client.list_public_packages(base_url) == { 'abc.txt': "test_account/abc.txt" }

        # delete file
        client.delete_file(base_url, "test_account", "password", "/hidden/abcd.txt")
        assert client.list_files(base_url, "test_account", "/hidden") == []

def test_errors(tmpdir):

    @contextmanager
    def expect(status_code):
        try:
            yield
        except Exception, e:
            if isinstance(e, requests.HTTPError) and e.response.status_code == status_code:
                return
            else:
                raise Exception("expected HTTPError(%d), got %s" % (status_code, e))
        raise Exception("expected HTTPError(%d)" % status_code)


    with run_background_server(tmpdir.strpath, 55557) as srv:

        base_url = "http://localhost:55557"
        data = StringIO.StringIO() # empty file

        # register user
        srv.create_account("test_account", "password")

        # wrong pw
        with expect(401):
            client.upload_file(base_url, "test_account", "false_password", "/abcd.txt", data)

        # wrong account
        with expect(401):
            client.upload_file(base_url, "none_exisiting_account", "false_password", "/abcd.txt",
                    data)

        # delete non existing
        with expect(404):
            client.delete_file(base_url, "test_account", "password", "/abcd.txt")

        # download non existing
        with expect(404):
            client.download_file(base_url, "test_account", "/abcd.txt")

        client.upload_file(base_url, "test_account", "password", "/abcd.txt", data)
        with expect(409):
            client.upload_file(base_url, "test_account", "password", "/abcd.txt", data)

