# encoding:latin-1

import requests
import os
import time
import random
import core.config as config
import glob


def get_latest_emzed_version_from_pypi():
    url = config.global_config.get_url("pypi_url")
    response = requests.get(url + "emzed/json")
    response.raise_for_status()
    version_str = response.json()["info"]["version"]
    return tuple(map(int, version_str.split(".")))


def is_writable(folder):
    if not os.access(folder, os.W_OK):
        return False

    f_name = ".write_test_%f_%f" % (time.time(), random.random())
    path = os.path.join(folder, f_name)
    try:
        open(path, "w").close()
    except IOError:
        return False
    else:
        for test_file in glob.glob(os.path.join(folder, ".write_test_*")):
            try:
                os.remove(test_file)
            except IOError:
                pass
        return True


import abc

class AbstractUpdaterImpl(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_id(self):
        pass

    @abc.abstractmethod
    def get_update_time_delta_in_seconds(self):
        pass

    @abc.abstractmethod
    def query_update_info(self, data_home):
        pass

    @abc.abstractmethod
    def trigger_update(self, data_home):
        pass

    @abc.abstractmethod
    def upload_to_exchange_folder(self, data_home, exchange_folder):
        pass

    @abc.abstractmethod
    def check_for_newer_version_on_exchange_folder(self, data_home, exchange_folder):
        pass

    @abc.abstractmethod
    def update_from_exchange_folder(self, data_home, exchange_folder):
        pass

class Updater(object):

    def __init__(self, impl):
        self.impl = impl

    def get_id(self):
        return self.impl.get_id()

    def get_ts_file_path(self):
        dir_name = os.path.join(config.folders.getEmzedFolder(), self.impl.get_id())
        path = os.path.join(dir_name, "latest_update")
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        return path

    def get_latest_update_ts(self):
        path = self.get_ts_file_path()
        if not os.path.exists(path):
            return 0.0
        with open(path, "rt") as fp:
            try:
                line = fp.readlines()[0]
                if "#" in line:
                    line = line.split("#")[0]
                seconds_since_epoch = float(line)
                return seconds_since_epoch
            except Exception, e:
                raise "reading %s failed: %s" % (path, e.message)

    def _reset_latest_update_ts(self, seconds_since_epoch):
        path = self.get_ts_file_path()
        with open(path, "wt") as fp:
            readable = time.asctime(time.localtime(seconds_since_epoch))
            print >> fp, "%f # %s" % (seconds_since_epoch, readable)

    def offer_update_lookup(self):
        """ shall I offer update lookup ??? """
        return self.get_latest_update_ts() + self.impl.get_update_time_delta_in_seconds() <= time.time()

    def query_update_info(self):
        """ queries if update is available and delivers info about that"""
        data_home = config.folders.getDataHome()
        info = self.impl.query_update_info(data_home)
        return (self.impl.get_id(), self.get_latest_update_ts(), info)

    def do_update(self):
        """ returns flag, message """
        data_home = config.folders.getDataHome()
        try:
            self.impl.trigger_update(data_home)
        except Exception, e:
            return False, e.message
        # update succeeded
        ts = time.time()
        self._reset_latest_update_ts(ts)
        exchange_folder = config.folders.getExchangeSubFolder(None)
        if exchange_folder is not None:
            if is_writable(exchange_folder):
                self.impl.upload_to_exchange_folder(data_home, exchange_folder)

        return True, "ok"

    def check_for_newer_version_on_exchange_folder(self):
        """ returns flag, message
            flag = None means: no exchange folder configuered
        """
        exchange_folder = config.global_config.get("exchange_folder")
        if not exchange_folder:
            return None, None
        try:
            os.listdir(exchange_folder)
        except Exception, e:
            return None, e.message
        data_home = config.folders.getDataHome()
        is_newer  = self.impl.check_for_newer_version_on_exchange_folder(data_home, exchange_folder)
        return is_newer, None

    def fetch_update_from_exchange_folder(self):
        """ returns flag, message
            flag = None means: no exchange folder configuered
        """
        exchange_folder = config.global_config.get("exchange_folder")
        if not exchange_folder:
            return None, None
        try:
            os.listdir(exchange_folder)
        except Exception, e:
            return False, e.message
        data_home = config.folders.getDataHome()
        message = self.impl.update_from_exchange_folder(data_home, exchange_folder)
        self._reset_latest_update_ts(time.time())
        return True, message


class UpdaterRegistry(object):

    # singleton
    _instance = None
    def __new__(cls, *args, **kwargs):

        if not cls._instance:
            cls._instance = super(UpdaterRegistry, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.updaters = []

    def register(self, updater):
        assert isinstance(updater, Updater)
        self.updaters.append(updater)

#
# workflow gui
# 1. versuche von exchange folder zu laden
# 2 iteriere über alle updaters und sammle offer_update_lookup()
# 3 zeige offers an
# 4 entweder: skip, oder lookup
# 5 nach llokup: infos anzeigen, einzelen updates auswählen und ausführen
#

# workflow commandline:
# 4: ausgabe: emzed.upldates.lookup()
#    -> schöne printausgag
# 5: pro zeile: anelitung emzed.updates.update("id") aufzurufen
#    







