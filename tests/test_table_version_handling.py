import sys
from  emzed.utils import loadTable

import pytest

@pytest.mark.xfail
def test_1_3_8(path):
    print >> sys.stderr, "TEST LOADING OF TABLE FROM EMZED 1.3.8"
    t = loadTable(path("data/feature_table_1.3.8.table"))
    assert t.version == "1.3.8", "PLEASE READ cocepts/konzept_table_versions"
