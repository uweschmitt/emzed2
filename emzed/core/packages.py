# encoding:latin-1

EMZED_PKG_MARKER_FILE = ".emzed_pkg_marker"

import os
import sys
import requests
import subprocess
import pkg_resources

import helpers
from config import global_config
import licenses


SETUP_PY_TEMPLATE = """

# YOU CAN EDIT THESE FIELDS ######################################################################

# install package as emzed extension ?
# -> package will appear in emzed.ext namespace after installation

IS_EXTENSION = True

# Install package as emzed app ?
# will can be started as app.%(pkg_name)s.run()

# set this variable to None if this is a pure extension and not an emzed app
APP_MAIN = "%(pkg_name)s.main:run"

VERSION = %(version)r
AUTHOR = %(author)r
AUTHOR_EMAIL = %(author_email)r
AUTHOR_URL = %(author_url)r

PKG_NAME = %(pkg_name)r

DESCRIPTION = "please describe here %(pkg_name)s in one line"
LONG_DESCRIPTION = \"\"\"

describe %(pkg_name)s here in more than one line

\"\"\"

LICENSE = "http://opensource.org/licenses/GPL-3.0"

# DO NOT TOUCH THE CODE BELOW UNLESS YOU KNOW WHAT YOU DO !!!!  # ################################

if APP_MAIN is not None:
    try:
        mod_name, fun_name = APP_MAIN.split(":")
        exec "import %%s as _mod" %% mod_name
        fun = getattr(_mod, fun_name)
    except:
        raise Exception("invalid specification %%r of APP_MAIN" %% APP_MAIN)


entry_points = dict()
entry_points['emzed_package'] = [ "package = " + PKG_NAME, ]
if IS_EXTENSION:
    entry_points['emzed_package'].append("extension = " + PKG_NAME)
if APP_MAIN is not None:
    entry_points['emzed_package'].append("main = %%s" %% APP_MAIN)


if __name__ == "__main__":   # allows import setup.py for version checking

    import distutils.config

    def patched(self):
        return dict(realm="pypi",
                    username=%(user)r,
                    password=%(password)r,
                    repository=%(repository)r,
                    server="local",
                    )
    distutils.config.PyPIRCCommand._read_pypirc = patched


    from setuptools import setup
    setup(name=PKG_NAME,
        packages=[ PKG_NAME ],
        version=".".join(map(str, VERSION)),
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        url=AUTHOR_URL,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        license=LICENSE,
        entry_points = entry_points
        )
   """

def _normalize(folder):
    return os.path.abspath(os.path.normpath(folder))

def _check_name(pkg_name):
    forbidden = " .-"
    if any(c in pkg_name for c in forbidden) or pkg_name.lower() != pkg_name:
        suggested = pkg_name.lower()
        for f in forbidden:
            suggested = suggested.replace(f, "_")
        raise Exception("name %r invalid. you could use %r instead" % ( pkg_name, suggested))


def _test_if_folder_is_inside_existing_pkg(folder):
    folder = _normalize(folder)
    # normpath replaces "/" to r"\" on win:
    for __ in range(100):
        if folder.endswith(os.path.sep):
            return None # reached top folder (maybe something like C:\ on win)
        # go one folder level upwards:
        folder, __ = os.path.split(folder)
        if os.path.exists(os.path.join(folder, EMZED_PKG_MARKER_FILE)):
                return folder
    raise Exception("unlimited loop for folder %r" % folder)


def _test_if_folder_already_exists(folder):
    if os.path.exists(folder):
        raise Exception("%s already exists" % folder)


def _create_pkg_folder(pkg_folder, pkg_name, version):
    path_to_existing_pkg = _test_if_folder_is_inside_existing_pkg(pkg_folder)
    if path_to_existing_pkg:
        raise Exception("found existing emzed package in %s" % path_to_existing_pkg)

    os.makedirs(pkg_folder)
    open(os.path.join(pkg_folder, EMZED_PKG_MARKER_FILE), "w").close()
    _create_package_folder(pkg_folder, pkg_name, version)
    _create_test_folder(pkg_folder, pkg_name)


def _create_package_folder(pkg_folder, pkg_name, version):
    package_folder = os.path.join(pkg_folder, pkg_name)
    os.makedirs(package_folder)
    with open(os.path.join(package_folder, "__init__.py"), "w") as fp:
        fp.write("""
from hello import hello
    """)

    with open(os.path.join(package_folder, "main.py"), "w") as fp:
        fp.write("""
def run():
    return 42
    """)

    with open(os.path.join(package_folder, "hello.py"), "w") as fp:
        fp.write("""
def hello():
    return "%s says hello"
    """ % pkg_name)

    with open(os.path.join(pkg_folder, "setup.py"), "w") as fp:
        user = global_config.get("emzed_store_user")
        password = global_config.get("emzed_store_password")
        repository = global_config.get_url("emzed_store_url")
        author = global_config.get("user_name")
        author_email = global_config.get("user_email")
        author_url = global_config.get("user_url")
        fp.write(SETUP_PY_TEMPLATE % locals())

    with open(os.path.join(pkg_folder, "LICENSE"), "w") as fp:
        fp.write(licenses.GPL_3)

    with open(os.path.join(pkg_folder, "README"), "w") as fp:
        fp.write("please describe your emzed package here\n")

def _create_test_folder(pkg_folder, pkg_name):
    tests_folder = os.path.join(pkg_folder, "tests")
    os.makedirs(tests_folder)
    with open(os.path.join(tests_folder, "__init__.py"), "w") as fp:
        pass

    with open(os.path.join(tests_folder, "test_main.py"), "w") as fp:
        fp.write("""
import %(pkg_name)s.main
def test_hello():
    assert isinstance(%(pkg_name)s.main.run(), basestring)
    """ % locals())


def create_package_scaffold(folder, pkg_name, version=(0,0,1)):
    _check_name(pkg_name)
    folder = _normalize(folder)
    _test_if_folder_already_exists(folder)
    _create_pkg_folder(folder, pkg_name, version)

def delete_from_emzed_store(pkg_name):
    user = global_config.get("emzed_store_user")
    password = global_config.get("emzed_store_password")
    url = global_config.get_url("emzed_store_url") + pkg_name
    response = requests.delete(url, auth=(user, password))
    response.raise_for_status()

def upload_to_emzed_store(pkg_folder):
    os.chdir(pkg_folder)

    # make sure we load the right setup.py
    sys.path.insert(0, os.path.abspath(pkg_folder))
    import setup
    sys.path.pop(0)

    for p, versions in list_packages_from_emzed_store():
        if p == setup.PKG_NAME and setup.VERSION  in versions:
            raise Exception("package %s with version %s already exists" % (setup.PKG_NAME,
                                                                           setup.VERSION))

    rc = subprocess.call("python setup.py sdist upload", shell=True)
    if rc:
        raise Exception("upload failed")

def install_from_emzed_store(pkg_name, version=None):
    if version:
        assert isinstance(version, tuple)
        assert len(version) == 3
    index_url = global_config.get_url("emzed_store_index_url")
    pkg_query = pkg_name
    if version:
        pkg_query += "==%s.%s.%s" % version

    is_venv = os.environ.get("VIRTUAL_ENV") is not None
    user_flag = "" if is_venv else "--user"

    exit_code = subprocess.call("pip install %s -i %s %s" % (user_flag, index_url, pkg_query),
                                shell=True)
    assert exit_code == 0

def uninstall_emzed_package(pkg_name):
    exit_code = subprocess.call("pip uninstall --yes %s" % pkg_name, shell=True)
    assert exit_code == 0
    import emzed.ext
    delattr(emzed.ext, pkg_name)


def installed_emzed_packages():
    reload(pkg_resources)
    entry_points = pkg_resources.iter_entry_points
    packages = [ep.module_name for ep in entry_points("emzed_package", name="package")]
    extensions = [ep.module_name for ep in entry_points("emzed_package", name="extension")]
    apps = [ep.module_name for ep in entry_points("emzed_package", name="main")]

    return [ (p, p in extensions, p in apps) for p in packages]

def list_packages_from_emzed_store():
    url = global_config.get_url("emzed_store_url")
    response = helpers.get_json(url)
    response.raise_for_status()
    packages = [ name.encode("latin-1") for name in response.json()["result"]]
    result = []
    for package in packages:
        response = helpers.get_json(url + package)
        response.raise_for_status()
        version_strings = response.json()["result"].keys()
        versions = [map(int, version_str.split(".")) for version_str in version_strings]
        result.append((package, map(tuple, versions)))
    return result

def list_newest_packages_from_emzed_store():
    packages = list_packages_from_emzed_store()
    return [ (pkg, max(versions)) for (pkg, versions) in packages]
