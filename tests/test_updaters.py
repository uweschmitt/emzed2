#encoding: latin-1

import unittest
import emzed.updaters
import emzed.core.config as config

import os
import shutil
import time

class UpdaterTests(unittest.TestCase):


    def __test_emzed_version_check(self):

        latest_version = emzed.updaters.get_latest_emzed_version_from_pypi()
        self.assertEquals(latest_version, (3, 1375178237, 93))


class TestUpdaterImpl(emzed.updaters.AbstractUpdaterImpl):

    def get_id(self):
        return "test_updater"

    def get_update_time_delta_in_seconds(self):
        return 0.5 # seconds

    def query_update_info(self, data_home, version_str):
        return "new_update_available"

    def trigger_update(self, data_home):
        open(os.path.join(data_home, "test_data"), "w").close()

    def upload_to_exchange_folder(self, data_home, exchange_folder):
        shutil.copy(os.path.join(data_home, "test_data"),
                    os.path.join(exchange_folder))

    def check_for_newer_version_on_exchange_folder(self, data_home, exchange_folder):
        return True

    def update_from_exchange_folder(self, data_home, exchange_folder):
        pass


def test_01(tmpdir):
    config.global_config.set_("exchange_folder", tmpdir.strpath)
    impl = TestUpdaterImpl()
    tt = emzed.updaters.Updater(impl)

    # prepare
    path = tt.get_ts_file_path()
    if os.path.exists(path):
        os.remove(path)
        os.removedirs(os.path.dirname(path))
    home = config.folders.getDataHome()
    if "test_data" in os.listdir(home):
        os.remove(os.path.join(home, "test_data"))

    assert tt.offer_update_lookup()

    id_, ts, info = tt.query_update_info()
    assert id_ == impl.get_id()
    assert info == "new_update_available"
    assert ts == 0.0

    tt.do_update()

    assert "test_data" in os.listdir(config.folders.getDataHome())
    assert "test_data" in os.listdir(tmpdir.strpath)

    assert not tt.offer_update_lookup()
    time.sleep(0.5)
    assert tt.offer_update_lookup()

    status, msg = tt.check_for_newer_version_on_exchange_folder()
    assert status is True

    status, msg = tt.fetch_update_from_exchange_folder()
    assert status is True
    print msg




