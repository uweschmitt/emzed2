#encoding: latin-1


def check_emzed_updates():
    import version
    from core.updaters import get_latest_emzed_version_from_pypi
    latest_version = get_latest_emzed_version_from_pypi()
    if latest_version > version.version:
        print "please update emzed, new version %s.%s.%s on pypi" % latest_version
        print "run emzed.updaters.update_emzed() and restart workbench"
        print

def update_emzed():
    import subprocess
    exit_code = subprocess.call("pip install -U emzed", shell=True)
    assert exit_code == 0

def run(id_):
    from core.updaters import registry
    updater = registry.get(id_)
    if updater is None:
        raise Exception("no updater with id %r registered" % id_)
    updater.do_update(10)

def reset(id_):
    from core.updaters import registry
    updater = registry.get(id_)
    if updater is None:
        raise Exception("no updater with id %r registered" % id_)
    updater.remove_ts_file()
#
# zum testen: ts_file vorher löschen, oder update_intervall auf 0 setzen
#

def get(id_):
    from core.updaters import registry
    updater = registry.get(id_)
    return updater

def print_update_status():
    from core.updaters import registry
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

