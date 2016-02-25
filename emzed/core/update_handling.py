# encoding:latin-1

import abc
import os
import time
import random
import glob
import subprocess
import tempfile

from .. import version
from ..core import config

from .emzed_update_downloader import load_updater_from_website


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


class AbstractUpdaterImpl(object):
    __metaclass__ = abc.ABCMeta

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

    def do_update_with_gui(self, limit):
        self.do_update(limit)  # default implementation

    @abc.abstractmethod
    def upload_to_exchange_folder(self, exchange_folder):
        pass

    @abc.abstractmethod
    def touch_data_home_files(self):
        pass

    @abc.abstractmethod
    def check_for_newer_version_on_exchange_folder(self, exchange_folder):
        pass

    @abc.abstractmethod
    def update_from_exchange_folder(self, exchange_folder):
        pass


class Updater(object):

    def __init__(self, impl, data_home):
        self.impl = impl
        self.set_folders(data_home)

    def set_folders(self, data_home):
        self.data_home = data_home
        self.impl.data_home = data_home

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
            except BaseException, e:
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
        try:
            info, offer_update = self.impl.query_update_info(limit)
        except Exception, e:
            info = str(e)
            offer_update = False
        return (self.impl.get_id(), self.get_latest_update_ts(), info, offer_update)

    def do_update_with_gui(self, limit=None):
        try:
            msg = self.impl.do_update_with_gui(limit)
            msg = "ok" if msg is None else msg
        except BaseException, e:
            import traceback
            traceback.print_exc()
            return False, str(e)
        self._finalize_update()
        return True, msg

    def do_update(self, limit=None):
        """ returns flag, message """
        try:
            msg = self.impl.do_update(limit)
            msg = "ok" if msg is None else msg
        except BaseException, e:
            import traceback
            traceback.print_exc()
            return False, str(e)
        self._finalize_update()
        return True, msg

    def _finalize_update(self):
        # update succeeded
        self._update_latest_update_ts(time.time())
        exchange_folder = config.global_config.get("exchange_folder")
        if exchange_folder is not None:
            if is_writable(exchange_folder):
                self.impl.upload_to_exchange_folder(exchange_folder)
                # make data_home data "newer" than those on exchange folder:
                self.impl.touch_data_home_files()

    def check_for_newer_version_on_exchange_folder(self):
        """ returns flag, message
            flag = None means: no exchange folder configuered
        """
        exchange_folder = config.global_config.get("exchange_folder")
        if not exchange_folder:
            return None, None
        try:
            # is readable ?
            os.listdir(exchange_folder)
        except BaseException, e:
            return None, str(e)
        try:
            is_newer = self.impl.check_for_newer_version_on_exchange_folder(exchange_folder)
        except:
            return False, None
        return is_newer, None

    def fetch_update_from_exchange_folder(self):
        """ returns flag, message
            flag = None means: no exchange folder configuered
        """
        exchange_folder = config.global_config.get("exchange_folder")
        if not exchange_folder:
            return None, None
        try:
            # is readable ?
            os.listdir(exchange_folder)
        except BaseException, e:
            return False, str(e)
        try:
            message = self.impl.update_from_exchange_folder(exchange_folder)
            self._update_latest_update_ts(time.time())
            self.impl.touch_data_home_files()
        except Exception, e:
            return False, str(e)
        return True, message


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


class EmzedUpdateImpl(AbstractUpdaterImpl):

    @staticmethod
    def get_id():
        return "emzed_updater"

    def get_update_time_delta_in_seconds(self):
        minutes = 1
        return minutes * 60

    def query_update_info(self, limit):
        updater = load_updater_from_website()
        latest_version = updater.version()
        if latest_version > version.version:
            description = updater.description()
            version_str = ".".join(map(str, latest_version))
            return "new emzed version %s available\n%s" % (version_str, description), True
        return "emzed still up to date", False

    def do_update(self, limit):
        updater = load_updater_from_website()
        is_venv = os.getenv("VIRTUAL_ENV") is not None
        updater.run_update(locally=not is_venv)
        return "please restart emzed to enable updates"

    def upload_to_exchange_folder(self, exchange_folder):
        pass

    def touch_data_home_files(self):
        pass

    def check_for_newer_version_on_exchange_folder(self, exchange_folder):
        return None

    def update_from_exchange_folder(self, exchange_folder):
        pass


class UpdaterRegistry(object):

    def reset(self):
        self.updaters = dict()
        updater = Updater(EmzedUpdateImpl(), None)
        self.register(updater)

    def register(self, updater):
        assert isinstance(updater, Updater)
        self.updaters[updater.get_id()] = updater

    def get(self, id_):
        return self.updaters.get(id_)

    def updater_ids(self):
        return self.updaters.keys()

    def install(self, module):
        for name, updater in self.updaters.items():
            setattr(module, name, updater.do_update)

registry = UpdaterRegistry()
registry.reset()
