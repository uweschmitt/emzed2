#encoding: latin-1

import unittest

import emzed.core.config as config

class ConfigTests(unittest.TestCase):

    def test_config(self):

        return

        self.assertEqual(config.get("user_name"), "Uwe Schmitt")
        config.set_("user_name", "Hans Dampf")
        self.assertEqual(config.get("user_name"), "Hans Dampf")

        import cStringIO
        fp = cStringIO.StringIO()
        config.store(fp)
        fp.seek(0)

        config.set_("user_name", "Udo Juergens")
        config.load(fp)

        config.set_("user_name", "Hans Dampf")







