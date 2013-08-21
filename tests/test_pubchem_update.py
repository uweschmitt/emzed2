from emzed.core.data_bases import PubChemDB

import os.path
import pytest


@pytest.mark.slow
def x_testPubChemUpdate(tmpdir):

    dp = tmpdir.strpath
    dbPath = os.path.join(dp, "pubchem.db")
    db = PubChemDB(dbPath)
    assert len(db.table)==0

    unknown, missing = db.getDiff(100)
    assert len(unknown)==100, len(unknown)
    assert len(missing)==0, len(missing)

    db.update(100)
    assert len(db.table) == 100
    assert db.table.rows[0][-1].startswith("http")
    assert len(db.table.rows[0]) == len(db.getColNames())
    assert db.table.getColNames()[0] == "m0"

    row = db.table.rows[0]
    assert db.table.getValue(row, "is_in_kegg") in [0,1]
    assert db.table.getValue(row, "is_in_hmdb") in [0,1]

    unknown, missing = db.getDiff(100)
    assert len(unknown)==100, len(unknown)
    #assert len(missing)==100, len(missing)
    assert len(set(unknown) & set(db.table.cid.values)) == 0 # no interscetion

    db.store()
    db = PubChemDB(dbPath)
    assert len(db.table) == 100
    assert db.table.rows[0][-1].startswith("http")
    assert len(db.table.rows[0]) == len(db.getColNames())

@pytest.mark.slow
def unicodeWorkaround():
    # this request failed after some update of pubchen as the delivered
    # document contains french latin-1 characters but is declared as utf-8
    data = PubChemDB._get_summary_data([247])
    PubChemDB._parse_data(data)

import emzed.db
import emzed.updaters

def test_pubchem_import():
    db = emzed.db.init_pubchem()
    assert db is not None
    assert len(db) >= 0

def test_pubchem_updaters_without_exchange_folder(tmpdir):

    db = emzed.db.init_pubchem(tmpdir.strpath, None)
    updater = emzed.updaters.get("pubchem_updater")

    # reset updater
    emzed.updaters.reset("pubchem_updater")

    # no ts_file, so update should be offered:
    assert updater.offer_update_lookup() is True

    # ask pubchem for info about eventual update:
    id_, ts, info = updater.query_update_info()
    assert id_ == "pubchem_updater"
    assert ts < 0
    assert len(info) > 0

    # download 10 items
    updater.do_update(10)
    assert len(updater.impl.db) == 10

    # exchange folder is not configuredd, so we get None results:
    assert updater.check_for_newer_version_on_exchange_folder() == (None, None)
    assert updater.fetch_update_from_exchange_folder() == (None, None)


def test_pubchem_updaters_with_exchange_folder(tmpdir):

    # create folders
    import os
    data_home = tmpdir.join("data_home").strpath
    exchange_folder = tmpdir.join("exchange_folder").strpath

    db = emzed.db.init_pubchem(data_home, exchange_folder)

    updater = emzed.updaters.get("pubchem_updater")

    # reset updater
    emzed.updaters.reset("pubchem_updater")

    # no ts_file, so update should be offered:
    assert updater.offer_update_lookup() is True

    # ask pubchem for info about eventual update:
    id_, ts, info = updater.query_update_info()
    assert id_ == "pubchem_updater"
    assert ts < 0
    assert len(info) > 0

    # download 10 items
    assert updater.do_update(10) == (True, "ok")
    assert len(updater.impl.db) == 10

    # simulate next startup, make db on exchange folder more current than local db
    import time
    time.sleep(0.05)
    from emzed.db.pubchem import db_path
    os.utime(db_path(exchange_folder), None)  # like "touch" command on linux

    # now we should get back that a more update version on exchange folder exists
    flag, msg =  updater.check_for_newer_version_on_exchange_folder()
    assert flag is True
    assert msg is None

    # fetching up to date db from exchange folder should work now:
    flag, msg = updater.fetch_update_from_exchange_folder()
    assert flag is True
    assert msg is None

    # todo: test local version for time stamp !





