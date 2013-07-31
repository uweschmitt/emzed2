# encoding:latin-1

EMZED_APP_MARKER_FILE = ".emzed_app_marker"

import os
import requests
import subprocess
import pkg_resources
import urllib

import helpers
import config
import licenses


SETUP_PY_TEMPLATE = """

# YOU CAN EDIT THESE FIELDS ##################################################

VERSION = %(version)r
AUTHOR = %(author)r
AUTHOR_EMAIL = %(author_email)r
AUTHOR_URL = %(author_url)r

DESCRIPTION = "please describe here %(app_name)s in one line"
LONG_DESCRIPTION = \"\"\"

describe %(app_name)s here in more than one line

\"\"\"

LICENSE = "http://opensource.org/licenses/GPL-3.0"

# DO NOT TOUCH THE CODE BELOW UNLESS YOU KNOW WHAT YOU DO !!!! ###############

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

setup(name=%(app_name)r,
      packages=[ %(app_name)r],
      version=".".join(map(str, VERSION)),
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=AUTHOR_URL,
      description=DESCRIPTION,
      long_description=LONG_DESCRIPTION,
      license=LICENSE,
      entry_points = {
          'emzed_plugin' :
          [
              "package = %(app_name)s",
              ]
          }
     )
"""

def _normalize(folder):
    return os.path.abspath(os.path.normpath(folder))

def _check_name(app_name):
    forbidden = " .-"
    if any(c in app_name for c in forbidden) or app_name.lower() != app_name:
        suggested = app_name.lower()
        for f in forbidden:
            suggested = suggested.replace(f, "_")
        raise Exception("name %r invalid. you could use %r instead" % (
            app_name, suggested))


def _test_if_folder_is_inside_existing_app(folder):
    folder = _normalize(folder)
    # normpath replaces "/" to r"\" on win:
    for __ in range(100):
        if folder.endswith(os.path.sep):
            return None # reached top folder (maybe something like C:\ on win)
        # go one folder level upwards:
        folder, __ = os.path.split(folder)
        if os.path.exists(os.path.join(folder, EMZED_APP_MARKER_FILE)):
                return folder
    raise Exception("unlimited loop for folder %r" % folder)


def _test_if_folder_already_exists(folder):
    if os.path.exists(folder):
        raise Exception("%s already exists" % folder)


def _create_app_folder(app_folder, app_name, version):
    path_to_existing_app = _test_if_folder_is_inside_existing_app(app_folder)
    if path_to_existing_app:
        raise Exception("found existing app in %s" % path_to_existing_app)

    os.makedirs(app_folder)
    open(os.path.join(app_folder, EMZED_APP_MARKER_FILE), "w").close()
    _create_package_folder(app_folder, app_name, version)
    _create_test_folder(app_folder, app_name)


def _create_package_folder(app_folder, app_name, version):
    package_folder = os.path.join(app_folder, app_name)
    os.makedirs(package_folder)
    with open(os.path.join(package_folder, "__init__.py"), "w") as fp:
        fp.write("""
from hello import hello
    """)

    with open(os.path.join(package_folder, "hello.py"), "w") as fp:
        fp.write("""
def hello():
    return "this is %s"
    """ % app_name)

    with open(os.path.join(app_folder, "setup.py"), "w") as fp:
        user = config.get_value("app_store", "user")
        password = config.get_value("app_store", "password")
        repository = config.get_url("app_store", "app_store_url")
        author = config.get_value("app_store", "author")
        author_email = config.get_value("app_store", "author_email")
        author_url = config.get_url("app_store", "author_url")
        #version = "0.0.1"
        fp.write(SETUP_PY_TEMPLATE % locals())

    with open(os.path.join(app_folder, "LICENSE"), "w") as fp:
        fp.write(licenses.GPL_3)

    with open(os.path.join(app_folder, "README"), "w") as fp:
        fp.write("please describe your app here\n")

def _create_test_folder(app_folder, app_name):
    tests_folder = os.path.join(app_folder, "tests")
    os.makedirs(tests_folder)
    with open(os.path.join(tests_folder, "__init__.py"), "w") as fp:
        pass

    with open(os.path.join(tests_folder, "test_hello.py"), "w") as fp:
        fp.write("""
import %(app_name)s
def test_hello():
    assert isinstance(%(app_name)s.hello(), basestring), %(app_name)s.hello()
    """ % locals())


def create_app_scaffold(folder, app_name, version=(0,0,1)):
    _check_name(app_name)
    folder = _normalize(folder)
    _test_if_folder_already_exists(folder)
    _create_app_folder(folder, app_name, version)

def delete_from_app_store(app_name):
    user = config.get_value("app_store", "user")
    password = config.get_value("app_store", "password")
    app_url = urllib.basejoin(config.get_url("app_store", "app_store_url"), app_name)
    response = requests.delete(app_url, auth=(user, password))
    response.raise_for_status()

def upload_to_app_store(app_folder):
    os.chdir(app_folder)
    rc = subprocess.call("python setup.py sdist upload", shell=True)
    if rc:
        raise Exception("upload failed")

def install_from_app_store(app_name, version=None):
    if version:
        assert isinstance(version, tuple)
        assert len(version) == 3
    index_url = config.get_url("app_store", "app_store_index_url")
    app_query = app_name
    if version:
        app_query += "==%s.%s.%s" % version
    exit_code = subprocess.call("pip install -i %s %s" % (index_url, app_query),
        shell=True)
    assert exit_code == 0

def uninstall_app(app_name):
    exit_code = subprocess.call("pip uninstall --yes %s" % app_name,
        shell=True)
    assert exit_code == 0
    import emzed.ext
    delattr(emzed.ext, app_name)

def installed_apps():
    reload(pkg_resources)
    return [ep.module_name\
                for ep in pkg_resources.iter_entry_points("emzed_plugin",
                                                           name="package")]

def list_apps_from_appstore():
    index_url = config.get_url("app_store", "app_store_url")
    response = helpers.get_json(index_url)
    response.raise_for_status()
    apps = [ name.encode("latin-1") for name in response.json()["result"]]
    result = []
    for app in apps:
        response = helpers.get_json(index_url + app)
        response.raise_for_status()
        version_strings = response.json()["result"].keys()
        versions = [map(int, version_str.split(".")) for version_str in
                                                               version_strings]
        result.append((app, map(tuple, versions)))
    return result

def list_newest_apps_from_appstore():
    apps = list_apps_from_appstore()
    return [ (app, max(versions)) for (app, versions) in apps]
