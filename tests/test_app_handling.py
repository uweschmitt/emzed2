import pdb
#encoding: latin-1

import unittest

class AppTests(unittest.TestCase):

    def test_emzed_version_check(self):

        import emzed.core.updaters as updaters
        latest_version = updaters.get_latest_emzed_version_from_pypi()
        self.assertEquals(latest_version, (3, 1375178237, 93))

    def test_scaffold(self):
        import tempfile
        import os.path
        import emzed.core.apps
        tmpdir = os.path.join(tempfile.mkdtemp(), "app_folder")

        emzed.core.apps.create_app_scaffold(tmpdir, "minimal_app")

        files = os.listdir(tmpdir)

        self.assertIn("minimal_app", files)
        self.assertIn("tests", files)
        self.assertIn("setup.py", files)

        files = os.listdir(os.path.join(tmpdir, "minimal_app"))
        self.assertIn("hello.py", files)
        self.assertIn("__init__.py", files)

        files = os.listdir(os.path.join(tmpdir, "tests"))
        self.assertIn("test_hello.py", files)
        self.assertIn("__init__.py", files)

        # try to use existing folder:
        with self.assertRaises(Exception) as ctx:
            emzed.core.apps.create_app_scaffold(tmpdir, "minimal_app")

        # try to start app inside exising app folder:
        with self.assertRaises(Exception) as ctx:
            app_dir = os.path.join(tmpdir, "tests")
            emzed.core.apps.create_app_scaffold(app_dir, "minimal_app2")

    def test_minimal_app(self):
        import tempfile
        import os.path
        import emzed.core.apps
        tmpdir = os.path.join(tempfile.mkdtemp(), "app_folder")

        # create minimal app files
        emzed.core.apps.create_app_scaffold(tmpdir, "test_minimal_app")

        # upload minimal app file
        emzed.core.apps.upload_to_app_store(tmpdir)

        # remove eventually installed test app
        try:
            emzed.core.apps.uninstall_app("test_minimal_app")
        except:
            pass

        # install app
        emzed.core.apps.install_from_app_store("test_minimal_app")

        # use app
        import emzed.ext
        self.assertIsInstance(emzed.ext.test_minimal_app.hello(), basestring)

        # check if listed
        self.assertEqual(emzed.core.apps.installed_apps(), ["test_minimal_app"])

        # remove app
        emzed.core.apps.uninstall_app("test_minimal_app")

        # check if not listed any more
        self.assertEqual(emzed.core.apps.installed_apps(), [])
        # test if app is removed
        with self.assertRaises(Exception) as ctx:
            reload(emzed.ext)
            emzed.ext.test_minimal_app

        # remove test app from app store
        emzed.core.apps.delete_from_app_store("test_minimal_app")


    def test_delete_nonexisting(self):
        with self.assertRaises(Exception) as ctx:
            emzed.core.apps.delete_from_appstore("abc123")
