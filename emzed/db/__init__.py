

def _db_path(master_folder):
    from .. import version
    import os.path
    FILE_NAME = "pubchem.table"
    version_str = "%d.%d.%d" % version.version
    path = os.path.join(master_folder, version_str, FILE_NAME)
    return path

def _default_pubchem_folder():
    from ..core import config
    return config.folders.getDataHome()

def _load_pubchem(folder=None):

    from ..core.data_bases.pubchem_db import PubChemDB

    if folder is None:
        folder = _default_pubchem_folder()
    path = _db_path(folder)
    return PubChemDB.cached_load_from(path)

def load_pubchem(folder=None):
    return _load_pubchem(folder).table


from ..core import update_handling as _update_handling

class _PubChemUpdateImpl(_update_handling.AbstractUpdaterImpl):

    def get_db(self):
        return _load_pubchem(self.data_home)

    @staticmethod
    def get_id():
        return "pubchem_updater"

    def get_update_time_delta_in_seconds(self):
        days = 1
        return days * 24 * 60 * 60

    def query_update_info(self, limit):
        unknown, missing = self.get_db().getDiff(limit)
        if unknown or missing:
            return "%d unknown and %d deleted entries on website" % (len(unknown), len(missing))
        return "data on website unchanged"

    def do_update(self, limit):
        import os
        self.get_db().update(maxIds=limit)
        target_path = _db_path(self.data_home)
        target_dir = os.path.dirname(target_path)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        self.get_db().store(target_path)

    def upload_to_exchange_folder(self):
        import os
        target_path = _db_path(self.exchange_folder)
        target_dir = os.path.dirname(target_path)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        self.get_db().store(target_path)

    def touch_data_home_files(self):
        import os
        os.utime(_db_path(self.data_home), None)

    def check_for_newer_version_on_exchange_folder(self):
        import os
        return os.stat(_db_path(self.data_home)).st_mtime \
            <  os.stat(_db_path(self.exchange_folder)).st_mtime

    def update_from_exchange_folder(self):
        import os, shutil
        source_path = _db_path(self.exchange_folder)
        target_path = _db_path(self.data_home)

        target_dir = os.path.dirname(target_path)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        shutil.copy(source_path, target_path)
        self.get_db().reload_()

def _register_pubchem_updater():

    from ..core.config import folders
    ecf = folders.getExchangeSubFolder(None)

    updater = _update_handling.Updater(_PubChemUpdateImpl(), _default_pubchem_folder(), ecf)
    _update_handling.registry.register(updater)

