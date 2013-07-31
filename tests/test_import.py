# encoding: latin-1
import unittest

class ImportTest(unittest.TestCase):

    def test_version(self):
        import emzed
        self.assertGreaterEqual(emzed.__version__, (2, 0, 0))
