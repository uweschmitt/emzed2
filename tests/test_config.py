#encoding: latin-1

import unittest

class ConfigTests(unittest.TestCase):

    def test_config(self):

        import emzed.core.config
        cf = emzed.core.config.UserConfig(dict(section=dict(a=3)))
        self.assertEquals(cf.get_value("section", "a"), 3)

        cf.set_value("section", "a", 5)
        self.assertEquals(cf.get_value("section", "a"), 5)

        import cStringIO

        fp = cStringIO.StringIO()
        cf.write(fp)

        fp.seek(0)

        cf2 = emzed.core.config.UserConfig()
        cf2.read(fp)
        self.assertEquals(cf2.get_value("section", "a"), 5)


