# encoding: latin-1

import pytest

import emzed.core.package_store.server as server
import emzed.core.packages

from contextlib import contextmanager


@contextmanager
def run_background_server(dir_, port):
    srv = server.create_file_server(dir_, port)
    srv.start()
    try:
        yield srv
    finally:
        srv.stop()


def setup_config():
    from emzed.core.config import global_config

    global_config.parameters.user_name = "Uwe Schmitt"
    global_config.parameters.user_email = "uschmitt@uschmitt.info"
    global_config.parameters.user_url = ""

    global_config.parameters.metlin_token = ""

    global_config.parameters.emzed_store_user = "uweschmitt"
    global_config.parameters.emzed_store_password = "pillepalle"
    global_config.set_("emzed_store_url", "http://localhost:33336")


@pytest.mark.xfail
def test_basics(tmpdir):
    setup_config()

    with run_background_server(tmpdir.strpath, 33336):
        assert emzed.core.packages.list_packages_from_emzed_store() == dict()


def test_project_scaffold(tmpdir):
    import os.path
    setup_config()

    tmpdir = os.path.join(tmpdir.strpath, "minimal_package")

    emzed.core.packages.create_package_scaffold(tmpdir, "minimal_package")

    files = os.listdir(tmpdir)

    assert "minimal_package" in files
    assert "tests" in files
    assert "setup.py" in files
    assert "README" in files
    assert "LICENSE" in files

    files = os.listdir(os.path.join(tmpdir, "minimal_package"))
    assert "app.py" in files
    assert "minimal_module.py" in files
    assert "__init__.py" in files

    files = os.listdir(os.path.join(tmpdir, "tests"))
    assert ("test_extension.py" in files)
    assert ("__init__.py" in files)

    # try to use existing folder:
    with pytest.raises(Exception):
        emzed.core.packages.create_package_scaffold(tmpdir, "minimal_package")

    # try to create package inside exising package folder:
    with pytest.raises(Exception):
        pkg_dir = os.path.join(tmpdir, "tests")
        emzed.core.packages.create_package_scaffold(pkg_dir, "minimal_package2")


@pytest.mark.xfail
def test_minimal_package(tmpdir):
    setup_config()

    from emzed.core.config import global_config

    tmp_repos = tmpdir.join("data_dir").strpath
    tmp_project_folder = tmpdir.join("projects").strpath

    with run_background_server(tmp_repos, 33336) as srv:
        srv.app.create_account("uweschmitt", "pillepalle")
        _test_minimal_package(tmp_project_folder, srv)


def _test_minimal_package(tmpdir, srv):

    setup_config()

    import os.path
    import emzed.ext
    import emzed.app

    # create minimal set package files
    tmpdir = os.path.join(tmpdir, "minimal_test_package")
    emzed.core.packages.create_package_scaffold(tmpdir, "minimal_test_package")

    # remove test package from emzed package store if exists
    assert emzed.core.packages.delete_from_emzed_store("minimal_test_package", "0.0.1") is False

    # upload minimal package file
    emzed.core.packages.upload_to_emzed_store(tmpdir)

    # duplicate upload should fail
    with pytest.raises(Exception):
        emzed.core.packages.upload_to_emzed_store(tmpdir)

    # remove eventually installed test packages
    try:
        emzed.core.packages.uninstall_emzed_package("minimal_test_package")
    except:
        pass

    pkgs = emzed.core.packages.list_packages_from_emzed_store()
    assert (0, 0, 1) in [v for (v, path) in pkgs["minimal_test_package"]]

    pkgs = emzed.core.packages.list_newest_packages_from_emzed_store()
    newest_version, __ = pkgs["minimal_test_package"]
    assert newest_version == (0, 0, 1)

    # install package
    emzed.core.packages.install_from_emzed_store("minimal_test_package", (0, 0, 1))

    exec "import minimal_test_package"

    # use package as extension
    reload(emzed.ext)
    assert isinstance(emzed.ext.minimal_test_package.hello(), basestring)

    reload(emzed.app)
    assert (emzed.app.minimal_test_package() == 42)

    # check if listed
    assert(("minimal_test_package", True, False) in emzed.core.packages.installed_emzed_packages())

    # remove package
    emzed.core.packages.uninstall_emzed_package("minimal_test_package")

    # check if not listed any more
    assert(("minimal_test_package", True, False) not in
           emzed.core.packages.installed_emzed_packages())

    # test if package is removed
    with pytest.raises(Exception):
        reload(emzed.ext)
        emzed.ext.minimal_test_package

    # remove test package from emzed package store
    assert emzed.core.packages.delete_from_emzed_store("minimal_test_package", "0.0.1") is True

    pkgs = emzed.core.packages.list_packages_from_emzed_store()
    assert (0, 0, 1) not in [v for (v, path) in pkgs["minimal_test_package"]]

    pkgs = emzed.core.packages.list_newest_packages_from_emzed_store()
    assert "minimal_test_package" not in pkgs.keys()
