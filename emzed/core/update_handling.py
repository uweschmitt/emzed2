# encoding:latin-1

import requests
import os
import time
import random
from  ..core import config
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

    #@abc.abstractmethod
    #def __init__(self, data_home, exchange_folder):
        #pass

    @staticmethod
    @abc.abstractmethod
    def get_id(self):
        pass

    @abc.abstractmethod
    def get_update_time_delta_in_seconds(self):
        pass

    @abc.abstractmethod
    def query_update_info(self, limit):
        pass

    @abc.abstractmethod
    def do_update(self, limit):
        pass

    @abc.abstractmethod
    def upload_to_exchange_folder(self):
        pass

    @abc.abstractmethod
    def check_for_newer_version_on_exchange_folder(self):
        pass

    @abc.abstractmethod
    def update_from_exchange_folder(self):
        pass

class Updater(object):

    def __init__(self, impl, data_home, exchange_folder):
        self.impl = impl
        self.set_folders(data_home, exchange_folder)

    def set_folders(self, data_home, exchange_folder):
        self.data_home = data_home
        self.impl.data_home = data_home

        self.exchange_folder = exchange_folder
        self.impl.exchange_folder = exchange_folder

    def get_id(self):
        return self.impl.get_id()

    def _get_ts_file_path(self):
        dir_name = os.path.join(config.folders.getEmzedFolder(), self.impl.get_id())
        path = os.path.join(dir_name, "latest_update")
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        return path

    def get_latest_update_ts(self):
        path = self._get_ts_file_path()
        if not os.path.exists(path):
            return -1.0
        with open(path, "rt") as fp:
            try:
                line = fp.readlines()[0]
                if "#" in line:
                    line = line.split("#")[0]
                seconds_since_epoch = float(line)
                return seconds_since_epoch
            except Exception, e:
                raise "reading %s failed: %s" % (path, str(e))

    def remove_ts_file(self):
        path = self._get_ts_file_path()
        if os.path.exists(path):
            os.remove(path)

    def _update_latest_update_ts(self, seconds_since_epoch):
        path = self._get_ts_file_path()
        with open(path, "wt") as fp:
            readable = time.asctime(time.localtime(seconds_since_epoch))
            print >> fp, "%f # %s" % (seconds_since_epoch, readable)

    def offer_update_lookup(self):
        """ shall I offer update lookup ??? """
        return self.get_latest_update_ts() + self.impl.get_update_time_delta_in_seconds() <= time.time()

    def query_update_info(self, limit=None):
        """ queries if update is available and delivers info about that"""
        info = self.impl.query_update_info(limit)
        return (self.impl.get_id(), self.get_latest_update_ts(), info)

    def do_update(self, limit=None):
        """ returns flag, message """
        try:
            self.impl.do_update(limit)
        except Exception, e:
            return False, str(e)
        # update succeeded
        ts = time.time()
        self._update_latest_update_ts(ts)
        if self.exchange_folder is not None:
            if is_writable(self.exchange_folder):
                self.impl.upload_to_exchange_folder()

        return True, "ok"

    def check_for_newer_version_on_exchange_folder(self):
        """ returns flag, message
            flag = None means: no exchange folder configuered
        """
        if not self.exchange_folder:
            return None, None
        try:
            # is readable ?
            os.listdir(self.exchange_folder)
        except Exception, e:
            return None, str(e)
        is_newer  = self.impl.check_for_newer_version_on_exchange_folder()
        return is_newer, None

    def fetch_update_from_exchange_folder(self):
        """ returns flag, message
            flag = None means: no exchange folder configuered
        """
        if not self.exchange_folder:
            return None, None
        try:
            # is readable ?
            os.listdir(self.exchange_folder)
        except Exception, e:
            return False, str(e)
        message = self.impl.update_from_exchange_folder()
        self._update_latest_update_ts(time.time())
        return True, message


class UpdaterRegistry(object):

    def __init__(self):
        self.updaters = dict()

    def register(self, updater):
        assert isinstance(updater, Updater)
        self.updaters[updater.get_id()]=updater

    def get(self, id_):
        return self.updaters.get(id_)

    def install(self, module):
        for name, updater in self.updaters.items():
            setattr(module, name, updater.do_update)

registry = UpdaterRegistry()
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
# 5: pro zeile: anelitung emzed.updaters.update("id") aufzurufen

