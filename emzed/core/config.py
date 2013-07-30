config_app_store = {
        "app_store_url" : "http://127.0.0.1:3142/root/dev/",
        "app_store_index_url" : "http://127.0.0.1:3142/root/dev/+simple",
        "user" : "uschmitt",
        "password" : "pillepalle",
        "author": "Uwe Schmitt",
        "author_email": "uschmitt@uschmitt.info",
        "author_url": "",
        }

config_testpypi  = {
        "url" : "http://testpypi.python.org/pypi",
        }


test_config = {
        "app_store": config_app_store,
        "testpypi": config_testpypi,
        }

config = test_config.copy()

import os

def get_value(group, id_):
    is_test = os.environ.get("IS_TEST")
    if is_test:
        return test_config[group][id_]
    else:
        return config[group][id_]

def get_url(group, id_):
    return config[group][id_].rstrip("/")
