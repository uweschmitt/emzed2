#encoding: latin-1

from core.updaters import registry

def run(id_):
    updater = registry.get(id_)
    if updater is None:
        raise Exception("no updater with id %r registered" % id_)
    updater.do_update(10)

def reset(id_):
    updater = registry.get(id_)
    if updater is None:
        raise Exception("no updater with id %r registered" % id_)
    updater.remove_ts_file()
#
# zum testen: ts_file vorher löschen, oder update_intervall auf 0 setzen
#

def get(id_):
    updater = registry.get(id_)
    return updater


def print_update_status():
    print
    printed = False
    for name, updater in registry.updaters.items():
        flag, msg = updater.check_for_newer_version_on_exchange_folder()
        if flag is True:
            flag, msg = updater.fetch_update_from_exchange_folder()
            if flag:
                print "%s copied update from exchange folder" % name
            else:
                print "%s failed to update from exchange folder: %s" % (name, msg)
            printed = True

    if printed:
        print

    for name, updater in registry.updaters.items():
        if updater.offer_update_lookup():
            id_, ts, info = updater.query_update_info()
            print "%s says: %s" % (id_, info)
            print "call emzed.updaters.run(%r) for running update" % id_
            print

