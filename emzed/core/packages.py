# encoding:latin-1

import contextlib
import glob
import os
import pkg_resources
import re
import shutil
import subprocess
import sys
import tempfile

import requests

from collections import defaultdict

from config import global_config

import licenses

from package_store import client

EMZED_PKG_MARKER_FILE = ".emzed_pkg_marker"


def match_name(f):
    match = re.match("(.*)-(\d+\.\d+\.\d+)\.(tar\.gz|zip)", f)
    return match


def check_secret(secret):
    return re.match("[a-zA-Z0-9]*$", secret) is not None


def assert_valid_secret(secret):
    assert check_secret(secret), "only a-z, a-Z and 0-9 are allowed for secret string"

SETUP_PY_TEMPLATE = """

######################################################################################
#
# YOU CAN / SHOULD EDIT THE FOLLOWING SETTING
#
######################################################################################

PKG_NAME = %(pkg_name)r

VERSION = %(version)r

# list all required packages here:

REQUIRED_PACKAGES = ["emzed", ]


### install package as emzed extension ? #############################################
#   -> package will appear in emzed.ext namespace after installation

IS_EXTENSION = True


### install package as emzed app ?  ##################################################
#   -> can be started as app.%(pkg_name)s()
#   set this variable to None if this is a pure extension and not an emzed app

APP_MAIN = "%(pkg_name)s.app:run"


### author information ###############################################################

AUTHOR = %(author)r
AUTHOR_EMAIL = %(author_email)r
AUTHOR_URL = %(author_url)r


### package descriptions #############################################################

DESCRIPTION = "please describe here %(pkg_name)s in one line"
LONG_DESCRIPTION = \"\"\"

describe %(pkg_name)s here in more than one line

\"\"\"

LICENSE = "http://opensource.org/licenses/GPL-3.0"


######################################################################################
#                                                                                    #
# DO NOT TOUCH THE CODE BELOW UNLESS YOU KNOW WHAT YOU DO !!!!                       #
#                                                                                    #
#                                                                                    #
#       _.--""--._                                                                   #
#      /  _    _  \                                                                  #
#   _  ( (_\  /_) )  _                                                               #
#  { \._\   /\   /_./ }                                                              #
#  /_"=-.}______{.-="_\                                                              #
#   _  _.=('""')=._  _                                                               #
#  (_'"_.-"`~~`"-._"'_)                                                              #
#   {_"            "_}                                                               #
#                                                                                    #
######################################################################################


VERSION_STRING = "%%s.%%s.%%s" %% VERSION

ENTRY_POINTS = dict()
ENTRY_POINTS['emzed_package'] = [ "package = " + PKG_NAME, ]
if IS_EXTENSION:
    ENTRY_POINTS['emzed_package'].append("extension = " + PKG_NAME)
if APP_MAIN is not None:
    ENTRY_POINTS['emzed_package'].append("main = %%s" %% APP_MAIN)


if __name__ == "__main__":   # allows import setup.py for version checking

    from setuptools import setup
    setup(name=PKG_NAME,
        packages=[ PKG_NAME ],
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        url=AUTHOR_URL,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        license=LICENSE,
        version=VERSION_STRING,
        entry_points = ENTRY_POINTS,
        install_requires = REQUIRED_PACKAGES,
        )
   """


def _normalize(folder):
    return os.path.abspath(os.path.normpath(folder))


def check_name(pkg_name):
    if pkg_name != pkg_name.lower():
        return "'%s' contains upper case letters" % pkg_name
    if re.match("[a-z]", pkg_name[0]) is None:
        return "first character of '%s' is not in [a-z]" % pkg_name
    if re.match("[a-z][a-z0-9_]*$", pkg_name) is None:
        return "invalid characters in '%s'. only [a-z], [0-9] and '_' are allowed" % pkg_name
    return None


def is_project_folder(path):
    return os.path.exists(path) and os.path.isdir(path) and EMZED_PKG_MARKER_FILE in os.listdir(path)


def _test_if_folder_is_inside_existing_pkg(folder):
    folder = _normalize(folder)
    # normpath replaces "/" to r"\" on win:
    for __ in range(100):
        if folder.endswith(os.path.sep):
            return None  # reached top folder (maybe something like C:\ on win)
        # go one folder level upwards:
        folder, __ = os.path.split(folder)
        if is_project_folder(folder):
                return folder
    raise Exception("unlimited loop for folder %r" % folder)


def _test_if_folder_already_exists(folder):
    if os.path.exists(folder):
        raise Exception("%s already exists" % folder)


def _create_pkg_folder(pkg_folder, pkg_name, version):
    path_to_existing_pkg = _test_if_folder_is_inside_existing_pkg(pkg_folder)
    if path_to_existing_pkg:
        raise Exception("found existing emzed package in %s" % path_to_existing_pkg)

    try:
        os.makedirs(pkg_folder)
    except:
        if os.listdir(pkg_folder):
            raise Exception("destination folder is not empty")

    open(os.path.join(pkg_folder, EMZED_PKG_MARKER_FILE), "w").close()
    _create_package_folder(pkg_folder, pkg_name, version)
    _create_test_folder(pkg_folder, pkg_name)


def _create_package_folder(pkg_folder, pkg_name, version):
    package_folder = os.path.join(pkg_folder, pkg_name)
    os.makedirs(package_folder)
    with open(os.path.join(package_folder, "__init__.py"), "w") as fp:
        fp.write("""

# IMPORTS WHICH SHOULD APPEAR IN emzed.ext AFTER INSTALLING THE PACKAGE:
from minimal_module import hello # makes emzed.ext.%s.hello() visible

# DO NOT TOUCH THE FOLLOWING LINE:
import pkg_resources
__version__ = tuple(map(int, pkg_resources.require(__name__)[0].version.split(".")))
del pkg_resources""" % pkg_name)

    with open(os.path.join(package_folder, "app.py"), "w") as fp:
        fp.write("""
def run():
    return 42
    """)

    with open(os.path.join(package_folder, "minimal_module.py"), "w") as fp:
        fp.write("""
def hello():
    return "hello from %s"
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

    with open(os.path.join(tests_folder, "test_extension.py"), "w") as fp:
        fp.write("""
def test_hello():
    import emzed.ext
    reload(emzed.ext)
    assert emzed.ext.%(pkg_name)s.hello().startswith("hello")
    """ % locals())


def create_package_scaffold(folder, pkg_name, version=(0, 0, 1)):
    complaint = check_name(pkg_name)
    if complaint:
        raise Exception(complaint)
    folder = _normalize(folder)
    _test_if_folder_already_exists(folder)
    _create_pkg_folder(folder, pkg_name, version)


def delete_from_emzed_store(pkg_name, version_string, secret=""):
    assert_valid_secret(secret)
    assert version_string, "empty version_string not allowed"
    user = global_config.get("emzed_store_user")
    password = global_config.get("emzed_store_password")
    url = global_config.get_url("emzed_store_url")  # + pkg_name + "/" + version_string

    folder = "/" + secret
    try:
        files = client.list_files(url, user, folder)
    except requests.HTTPError, e:
        print str(e)
        print
        print "MAYBE USER %s IS NOT KNOWN OR SECRET %r IS NOT VALID" % (user, secret)
        print
        return False
    deleted = False
    for f in files:
        match = match_name(f)
        if match is not None:
            name, vstr, __ = match.groups()
            if name == pkg_name and vstr == version_string:
                path = "/%s/%s" % (secret, f)
                client.delete_file(url, user, password, path)
                deleted = True
    return deleted


@contextlib.contextmanager
def changed_working_directory(target):
    old_dir = os.getcwd()
    os.chdir(target)
    try:
        yield
    finally:
        os.chdir(old_dir)


def upload_to_emzed_store(pkg_folder, secret=""):
    assert_valid_secret(secret)
    with changed_working_directory(pkg_folder):
        # make sure we load the right setup.py
        sys.path.insert(0, os.path.abspath(pkg_folder))
        import setup
        reload(setup)
        sys.path.pop(0)

        existing_versions = list_packages_from_emzed_store()[setup.PKG_NAME]
        if existing_versions:
            if any(setup.VERSION == v for (v, __) in existing_versions):

                raise Exception("package %s with version %s already exists" % (setup.PKG_NAME,
                                                                               setup.VERSION))
        if os.path.exists("dist"):
            shutil.rmtree("dist")

        rc = subprocess.call("python setup.py sdist", shell=True,
                stdout=sys.__stdout__,
                stderr= sys.__stdout__)
        if rc:
            raise Exception("upload failed")

        user = global_config.get("emzed_store_user")
        password = global_config.get("emzed_store_password")
        url = global_config.get_url("emzed_store_url")

        for p in glob.glob("dist/*"):
            if os.path.isfile(p):
                path = "/%s/%s" % (secret, os.path.basename(p))
                with open(p, "rb") as fp:
                    try:
                        client.upload_file(url, user, password, path, fp)
                    except requests.HTTPError, e:
                        print str(e)
                        print
                        print "MAYBE USER %s IS UNKNOWN OR PASSWORD DOES NOT MATCH" % user
                        print
                        print "USE emzed.config.edit() TO CHANGE THEM."
                        print
                        break


def install_from_emzed_store(pkg_name, wanted_version=None):
    if wanted_version:
        if isinstance(wanted_version, str):
            wanted_version = tuple(map(int, wanted_version.split(".")))
        assert isinstance(wanted_version, tuple)
        assert len(wanted_version) == 3

    url = global_config.get_url("emzed_store_url")

    version_infos = list_packages_from_emzed_store().get(pkg_name, [])
    for version, target_path in version_infos:
        if version == wanted_version:
            path = target_path
            break

    if path is None:
        raise Exception("version %s of %s not found on package store" % (wanted_version, pkg_name))

    is_venv = os.environ.get("VIRTUAL_ENV") is not None
    user_flag = "" if is_venv else "--user"

    # I first tried to download the file and run easy_install locally on it. But this
    # did not update pkg_resources, so reload(emzed.ext) in the same python interpeter process
    # did not find the new extension point.
    # pip does not show this problem.

    with changed_working_directory(tempfile.mkdtemp()):
        rc = subprocess.call("pip install %s %s" % (user_flag, url + path), shell=True)
        if rc:
            raise Exception("download failed")


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
    return [(p, p in extensions, p in apps) for p in packages]


def list_packages_from_emzed_store(secret=""):
    url = global_config.get_url("emzed_store_url")
    result = defaultdict(list)
    if not secret:
        packages = client.list_public_files(url)
    else:
        user = global_config.get("emzed_store_user")
        folder = "/" + secret
        try:
            packages = client.list_files(url, user, folder)
        except requests.HTTPError, e:
            print str(e)
            print
            print "MAYBE USER %s IS UNKNOWN OR SECRET '%s' IS INVALID" % (user, secret)
            print
            return result
    for name, path in packages.items():
        m = match_name(name)
        if m is not None:
            name, version_str, __ = m.groups()
            version_tuple = tuple(map(int, version_str.split(".")))
            result[name].append((version_tuple, path))
    return result


def list_newest_packages_from_emzed_store():
    packages = list_packages_from_emzed_store()
    return dict([(pkg, max(versions)) for (pkg, versions) in packages.items()])
