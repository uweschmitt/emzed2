#encoding: latin-1

import unittest

class UpdaterTTests(unittest.TestCase):

    def test_emzed_version_check(self):

        import emzed.core.updaters as updaters
        latest_version = updaters.get_latest_emzed_version_from_pypi()
        self.assertEquals(latest_version, (3, 1375178237, 93))

