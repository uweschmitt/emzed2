#encoding: latin-1

import unittest
import emzed.core.config
import tempfile, os.path


class ConfigTests(unittest.TestCase):

    def setUp(self):
        # create nonexisting temp dir
        self.path = os.path.join(tempfile.mkdtemp() + "x", "test_config.ini")

    def test_global_config(self):

        config = emzed.core.config.global_config

        config.set_("user_name", "Hans Dampf")
        self.assertEqual(config.get("user_name"), "Hans Dampf")
        config.store(self.path)

        config.set_("user_name", "Udo Juergens")
        assert config.load(self.path)
        self.assertEqual(config.get("user_name"), "Hans Dampf")
