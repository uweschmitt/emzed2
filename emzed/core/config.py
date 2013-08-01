import pdb
#encoding: latin-1

import guidata.dataset.datatypes as dt
import guidata.dataset.dataitems as di
import guidata.userconfig

is_expert = dt.ValueProp(False)

class UserConfig(dt.DataSet):

    g1 = dt.BeginGroup("User Settings")

    user_name = di.StringItem("Full Name", notempty=True)
    user_email = di.StringItem("Email Adress", notempty=True)
    user_url = di.StringItem("Website URL")

    _g1 = dt.EndGroup("User Settings")

    g2 = dt.BeginGroup("Webservice Settings")

    metlin_token  = di.StringItem("Metlin Token")

    _g2 = dt.EndGroup("Webservice Settings")

    g3 = dt.BeginGroup("Emzed Store User Account")

    emzed_store_user = di.StringItem("User Name")
    emzed_store_password = di.StringItem("User Password")

    _g3 = dt.EndGroup("Emzed Store Settings")

    g4 = dt.BeginGroup("Emzed Store Expert Settings")
    enable_expert_settings = di.BoolItem("Enable Settings").set_prop("display",
            store=is_expert)
    emzed_store_url = di.StringItem("Emzed Store URL").set_prop("display", active=is_expert)
    emzed_store_index_url = di.StringItem("Emzed Store Index URL").set_prop("display", active=is_expert)
    pypi_url = di.StringItem("PyPi URL").set_prop("display", active=is_expert)

    _g4 = dt.EndGroup("Expert Settings")

test_config = UserConfig()

test_config.user_name = "Uwe Schmitt"
test_config.user_email = "uschmitt@uschmitt.info"
test_config.user_url = ""

test_config.metlin_token = ""

test_config.emzed_store_user = "uschmitt"
test_config.emzed_store_password = "pillepalle"

test_config.emzed_store_url = "http://127.0.0.1:3141/root/dev"
test_config.emzed_store_index_url = "http://127.0.0.1:3141/root/dev/+simple/"
test_config.pypi_url = "http://testpypi.python.org/pypi"

import os
is_test = os.environ.get("IS_TEST")
if is_test:
    config = test_config

def get(key):
    return getattr(config, key)

def set_(key, value):
    return setattr(config, key, value)

def get_url(key):
    return get(key).rstrip("/") + "/"

def store(fp):
    cf = guidata.userconfig.UserConfig(dict())
    config.write_config(cf, "emzed", "")
    cf.write(fp)

def load(fp):
    cf = guidata.userconfig.UserConfig(dict())
    cf.read(fp)
    config.read_config(cf, "emzed", "")
