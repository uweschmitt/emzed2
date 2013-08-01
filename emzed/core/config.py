#encoding: latin-1

#class ConfiGroup(object):
#
    #def __init__(self);
        #self.dd = dict()
#
    #def add_
    #

config_pkg_store = {
        "url" : "http://127.0.0.1:3141/root/dev/",
        "index_url" : "http://127.0.0.1:3141/root/dev/+simple/",
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
        "emzed_store": config_pkg_store,
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
    # URLS allways end with "/" !!!
    return config[group][id_].rstrip("/")+ "/"

#
#
# hier dann zwei instanzen !
# eine fixed zum testen
# eine andere für den betrieb


#class Config(object):

#    @classmethod
#    def fromDirectory(clz, path):
#        # lade config.json falls vorhanden
#        # lade current_default.json falls vorhanden
#        # lada old_default.json fallls vorhanden

class Config(object):

    pass
    # holds groups, keys, description, type, is_expert, editable

    @classmethod
    def fromFile(clz, path):
        pass

    @classmethod
    def fromDict(clz, dd):
        pass

    def storeFile(self, path):
        pass


