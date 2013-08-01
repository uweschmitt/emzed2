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
        import emzed.core.packages
        tmpdir = os.path.join(tempfile.mkdtemp(), "pkg_folder")

        emzed.core.packages.create_package_scaffold(tmpdir, "minimal_package")

        files = os.listdir(tmpdir)

        self.assertIn("minimal_package", files)
        self.assertIn("tests", files)
        self.assertIn("setup.py", files)
        self.assertIn("README", files)
        self.assertIn("LICENSE", files)

        files = os.listdir(os.path.join(tmpdir, "minimal_package"))
        self.assertIn("main.py", files)
        self.assertIn("hello.py", files)
        self.assertIn("__init__.py", files)

        files = os.listdir(os.path.join(tmpdir, "tests"))
        self.assertIn("test_main.py", files)
        self.assertIn("__init__.py", files)

        # try to use existing folder:
        with self.assertRaises(Exception):
            emzed.core.packages.create_package_scaffold(tmpdir, "minimal_package")

        # try to create package inside exising package folder:
        with self.assertRaises(Exception):
            pkg_dir = os.path.join(tmpdir, "tests")
            emzed.core.packages.create_package_scaffold(pkg_dir, "minimal_package2")

    def test_minimal_package(self):
        import tempfile
        import os.path
        import emzed.core.packages
        tmpdir = os.path.join(tempfile.mkdtemp(), "pkg_folder")

        # create minimal set package files
        emzed.core.packages.create_package_scaffold(tmpdir, "test_minimal_package")

        # upload minimal package file
        emzed.core.packages.upload_to_emzed_store(tmpdir)

        # remove eventually installed test packages
        try:
            emzed.core.packages.uninstall_emzed_package("test_minimal_package")
        except:
            pass

        pkgs = emzed.core.packages.list_packages_from_emzed_store()
        self.assertEquals(pkgs,[ ("test_minimal_package", [(0,0,1)]) ])

        pkgs = emzed.core.packages.list_newest_packages_from_emzed_store()
        self.assertEquals(pkgs,[ ("test_minimal_package", (0,0,1)) ])

        # install package
        emzed.core.packages.install_from_emzed_store("test_minimal_package", (0, 0, 1))

        # use package as extension
        import emzed.ext
        self.assertIsInstance(emzed.ext.test_minimal_package.hello(), basestring)

        import emzed.app
        self.assertEquals(emzed.app.test_minimal_package(), 42)

        # check if listed
        self.assertEqual(emzed.core.packages.installed_emzed_packages(),
                                                          [("test_minimal_package", True, False)])

        # remove package
        emzed.core.packages.uninstall_emzed_package("test_minimal_package")

        # check if not listed any more
        self.assertEqual(emzed.core.packages.installed_emzed_packages(), [])
        # test if package is removed
        with self.assertRaises(Exception):
            reload(emzed.ext)
            emzed.ext.test_minimal_package

        # remove test package from emzed package store
        emzed.core.packages.delete_from_emzed_store("test_minimal_package")

        packages = emzed.core.packages.list_packages_from_emzed_store()
        self.assertEqual(packages, [])
        packages = emzed.core.packages.list_newest_packages_from_emzed_store()
        self.assertEqual(packages, [])


    def test_delete_nonexisting(self):
        with self.assertRaises(Exception):
            emzed.core.packages.delete_from_emzed_store("abc123")
