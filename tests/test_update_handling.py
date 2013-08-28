#encoding: latin-1

import unittest
import emzed.core.update_handling
import emzed.core.config as config

import os
import shutil
import time

class UpdaterTests(unittest.TestCase):


    def __test_emzed_version_check(self):

        latest_version = emzed.core.update_handling.get_latest_emzed_version_from_pypi()
        self.assertEquals(latest_version, (3, 1375178237, 93))


class TestUpdaterImpl(emzed.core.update_handling.AbstractUpdaterImpl):

    def get_data_home(self):
        return config.folders.getDataHome()

    @staticmethod
    def get_id():
        return "test_updater"

    def get_update_time_delta_in_seconds(self):
        return 0.5 # seconds

    def query_update_info(self, limit):
        return "new_update_available"

    def do_update(self, limit):
        open(os.path.join(self.data_home, "test_data"), "w").close()

    def upload_to_exchange_folder(self):
        shutil.copy(os.path.join(self.data_home, "test_data"),
                    os.path.join(self.exchange_folder))

    def check_for_newer_version_on_exchange_folder(self):
        return True

    def update_from_exchange_folder(self):
        pass


def test_01(tmpdir):
    data_home = tmpdir.join("data_home").strpath
    exchange_folder = tmpdir.join("exchange_folder").strpath
    os.makedirs(exchange_folder)
    os.makedirs(data_home)

    tt = emzed.core.update_handling.Updater(TestUpdaterImpl(), data_home, exchange_folder)

    # prepare
    tt.remove_ts_file()

    assert tt.offer_update_lookup()

    id_, ts, info = tt.query_update_info()
    assert id_ == TestUpdaterImpl.get_id()
    assert info == "new_update_available"
    assert ts < 0.0

    flag, msg = tt.do_update()

    assert flag is True, msg

    assert "test_data" in os.listdir(data_home)
    assert "test_data" in os.listdir(exchange_folder), os.listdir(exchange_folder)

    assert not tt.offer_update_lookup()
    time.sleep(0.5)
    assert tt.offer_update_lookup()

    status, msg = tt.check_for_newer_version_on_exchange_folder()
    assert status is True

    status, msg = tt.fetch_update_from_exchange_folder()
    assert status is True
    print msg




