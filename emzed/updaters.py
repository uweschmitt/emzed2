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
                print "%s: copied update from exchange folder" % name
            else:
                print "%s: failed to update from exchange folder: %s" % (name, msg)
        elif flag is False:
            print "local version still up to date"
        else:
            assert flag is None
            print "no exchange folder configured"

    print

    for name, updater in registry.updaters.items():
        print "%-20s :" % name,
        if updater.offer_update_lookup():
            id_, ts, info, offer_update = updater.query_update_info()
            print info
            print "%-20s +" % "",
            if offer_update:
                print "call emzed.updaters.run(%r) for running update" % id_
            else:
                print
        else:
            print "local version is new enough"
    print

def interactive_update():
    from core.update_handling import registry
    from core.dialogs.update_dialog import UpdateDialog, qapplication

    def script(dlg):
        for name, updater in registry.updaters.items():
            flag, msg = updater.check_for_newer_version_on_exchange_folder()
            if flag is True:
                flag, msg = updater.fetch_update_from_exchange_folder()
                if flag:
                    yield dlg.add_info_line("%s: copied update from exchange folder" % name)
                else:
                    yield dlg.add_info_line("%s: failed to update from exchange folder: %s" % (name, msg))
            elif flag is False:
                yield dlg.add_info_line("%s: local version still up to date" % name)
            else:
                yield dlg.add_info_line("%s: no exchange folder configured" % name)
            if updater.offer_update_lookup():
                id_, ts, info, offer_update = updater.query_update_info()
                yield dlg.add_update_info(name, info, offer_update)
            else:
                yield dlg.add_update_info(name, "no lookup today", False)

    app = qapplication()
    dlg = UpdateDialog(script)
    dlg.exec_()

    for id_ in dlg.get_updates_to_run():
        run(id_)



from db import _register_pubchem_updater
_register_pubchem_updater()

from core.r_connect.xcms_connector import _register_xcms_updater
_register_xcms_updater()
