# encoding: latin-1


def run(id_):
    from core.update_handling import registry
    updater = registry.get(id_)
    if updater is None:
        raise Exception("no updater with id %r registered" % id_)
    updater.do_update(10)


def reset(id_):
    from core.update_handling import registry
    updater = registry.get(id_)
    if updater is None:
        raise Exception("no updater with id %r registered" % id_)
    updater.remove_ts_file()
#
# zum testen: ts_file vorher löschen, oder update_intervall auf 0 setzen
#


def get(id_):
    from core.update_handling import registry
    updater = registry.get(id_)
    return updater


def print_update_status():
    from core.update_handling import registry
    print
    print
    for name, updater in registry.updaters.items():
        print "%-20s :" % name,
        flag, msg = updater.check_for_newer_version_on_exchange_folder()
        if flag is True:
            flag, msg = updater.fetch_update_from_exchange_folder()
            if flag:
                print "copied update from exchange folder" % name
            else:
                print "failed to update from exchange folder: %s" % (name, msg)
        elif flag is False:
            print "local version still up to date"
        else:
            assert flag is None
            print "no exchange folder configured"

    print

    for name, updater in registry.updaters.items():
        print "%-20s :" % name,
        if updater.offer_update_lookup():
            id_, ts, info = updater.query_update_info()
            print info
            print "%-20s +" % "",
            print "call emzed.updaters.run(%r) for running update" % id_
        else:
            print "local version is new enough"
    print

from db import _register_pubchem_updater
_register_pubchem_updater()
