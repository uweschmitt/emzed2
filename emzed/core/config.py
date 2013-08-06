import pdb
#encoding: latin-1

# keep namespace clean:

import guidata.dataset.datatypes as _dt
import guidata.dataset.dataitems as _di

_is_expert = _dt.ValueProp(False)

class _UserConfig(object):


    class Parameters(_dt.DataSet):

        g1 = _dt.BeginGroup("User Settings")

        user_name = _di.StringItem("Full Name", notempty=True)
        user_email = _di.StringItem("Email Adress", notempty=True)
        user_url = _di.StringItem("Website URL")

        _g1 = _dt.EndGroup("User Settings")

        g2 = _dt.BeginGroup("Webservice Settings")

        metlin_token  = _di.StringItem("Metlin Token")

        _g2 = _dt.EndGroup("Webservice Settings")

        g3 = _dt.BeginGroup("Emzed Store User Account")

        emzed_store_user = _di.StringItem("User Name")
        emzed_store_password = _di.StringItem("User Password")

        _g3 = _dt.EndGroup("Emzed Store Settings")

        g4 = _dt.BeginGroup("Emzed Store Expert Settings")
        enable_expert_settings = _di.BoolItem("Enable Settings").set_prop("display",
                store=_is_expert)
        emzed_store_url = _di.StringItem("Emzed Store URL").set_prop("display", active=_is_expert)
        emzed_store_index_url = _di.StringItem("Emzed Store Index URL").set_prop("display", active=_is_expert)
        pypi_url = _di.StringItem("PyPi URL").set_prop("display", active=_is_expert)

        _g4 = _dt.EndGroup("Expert Settings")

    def __init__(self, *a, **kw):
        self.parameters = _UserConfig.Parameters()
        if "_no_load" not in kw:
            loaded = self.load()
            if not loaded:
                self.set_defaults()
        else:
            self.set_defaults()

    def get(self, key):
        val = getattr(self.parameters, key)
        if isinstance(val, unicode):
            val = val.encode("latin-1")
        return val

    def set_(self, key, value):
        return setattr(self.parameters, key, value)

    def get_url(self, key):
        return self.get(key).rstrip("/") + "/"

    def store(self, path=None):

        # path UserConfig for not writing to ~/.config/.none.ini as default:
        import guidata.userconfig
        __save = guidata.userconfig.UserConfig.__save
        try:
            guidata.userconfig.UserConfig.__save = lambda self: None
            if path is None:
                path = self.config_file_path()
            cf = guidata.userconfig.UserConfig(dict())
            self.parameters.write_config(cf, "emzed", "")
            with open(path, "wt") as fp:
                cf.write(fp)
        finally:
            # undo patch
            guidata.userconfig.UserConfig.__save = __save


    def load(self, path=None):
        import os
        import guidata.userconfig
        cf = guidata.userconfig.UserConfig(dict())
        if path is None:
            path = self.config_file_path()
        if os.path.exists(path):
            with open(path, "rt") as fp:
                try:
                    cf.readfp(fp)
                    self.parameters.read_config(cf, "emzed", "")
                    return True
                except:
                    pass
        return False

    def edit(self):
        self.parameters.edit()
        self.store()

    def config_file_path(self):
        import os
        from emzed.core.platform_dependent import getEmzedFolder
        return os.path.join(getEmzedFolder(), "config.ini")

    def set_defaults(self):
        self.parameters.emzed_store_url = "http://uweschmitt.info:3141/root/dev"
        self.parameters.emzed_store_index_url = "http://uweschmitt.info:3141/root/dev/+simple/"
        self.parameters.pypi_url = "http://testpypi.python.org/pypi"

global_config = _UserConfig()
