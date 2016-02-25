# encoding: latin-1

import _tools


def setup_updaters(data_home=None):

    from core.update_handling import registry
    registry.reset()

    from db import _register_pubchem_updater
    _register_pubchem_updater(data_home)

    from core.r_connect.xcms_connector import _register_xcms_updater
    _register_xcms_updater(data_home)

    return registry


def run(id_):
    registry = setup_updaters()
    updater = registry.get(id_)
    if updater is None:
        raise Exception("no updater with id %r registered" % id_)
    ok, msg = updater.do_update()
    if not ok:
        print
        print "UPDATE FAILED:", msg
        print


def reset(id_):
    registry = setup_updaters()
    updater = registry.get(id_)
    if updater is None:
        raise Exception("no updater with id %r registered" % id_)
    updater.remove_ts_file()

#
# zum testen: ts_file vorher löschen, oder update_intervall auf 0 setzen
#


def get(id_):
    registry = setup_updaters()
    updater = registry.get(id_)
    return updater


def _install_commands(globals_=globals()):
    registry = setup_updaters()
    for id_ in registry.updater_ids():
        exec "run_%s=lambda: run('%s')" % (id_, id_) in globals_


_install_commands()


def _print_first_start_info():
    print
    print "loading emzed.updaters ".ljust(80, ".")
    print
    print "as this is the first time you start emzed, we recommend to run:"
    print
    registry = setup_updaters()
    for id_ in registry.updater_ids():
        print "   %s.run_%s()" % (__name__, id_)
    print
    print "".ljust(80, ".")


# is_started_from_cmdline() == True iff invoked via emzed.workbench command line command.
#
# in this case nothing should happen, because we want this actions
# later in spyders ipython console where is_started_from_cmdline() is False.
if _tools.runs_inside_emzed_console() and _tools.is_first_start():
    _print_first_start_info()


def print_update_status():
    from core.update_handling import registry
    print
    print
    for name, updater in registry.updaters.items():
        print "%-20s :" % name,
        flag, msg = updater.check_for_newer_version_on_exchange_folder()
        if flag is True:
            flag, msg = updater.fetch_update_from_exchange_folder()
            if flag is None:
                print "%s: no exchange folder configured" % name
            elif flag:
                print "%s: copied update from exchange folder" % name
            else:
                print "%s: failed to update from exchange folder: %s" % (name, msg)
        elif flag is False:
            print "local version still up to date"
        else:
            assert flag is None
            if msg is None:
                print "%s: no exchange folder configured" % name
            else:
                print "%s: can not reach exchange folder: %s" % (name, msg)

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
            print "no need to update local verison"
    print


def _interactive_update():
    from core.update_handling import registry  
    from core.dialogs.update_dialog import UpdateDialog, qapplication
    from core.config import global_config

    registry = setup_updaters()

    def script(add_info_line, add_update_info):
        """
        add_info_line and add_upate_info are two tokens to communicate with the GUI.
        Actually both are methods.
        For calling the methods we yield a pair where the first entry is the method and
        the second is a tuple of arguments.

        This method allows async updating the dialog without blocking the GUI until all
        update info is retrieved.

        add_info_line adds text to the upper text field in the dialog and add_update_info
        adds a row to the table below this text field.
        """

        exchange_folder = global_config.get("exchange_folder")
        if exchange_folder:
            yield add_info_line, ("configured exchange folder is %s" % exchange_folder,)
        else:
            yield add_info_line, ("no exchange folder configured. use emzed.config.edit() to "
                                  "configure an exchange folder",)

        for name, updater in registry.updaters.items():

            flag, msg = updater.check_for_newer_version_on_exchange_folder()
            if flag is True:
                flag, msg = updater.fetch_update_from_exchange_folder()
                if flag:
                    yield add_info_line, ("%s: copied update from exchange folder" % name,)
                elif flag is None:
                    pass
                else:
                    yield add_info_line, ("%s: failed to update from exchange folder: %s" % (name,
                                                                                             msg),)
            elif flag is False:
                yield add_info_line, ("%s: local version still up to date" % name,)
            elif flag is None:
                if msg is None:
                    pass
                else:
                    yield add_info_line, ("%s: %s" % (name, msg),)

            if updater.offer_update_lookup():
                id_, ts, info, offer_update = updater.query_update_info()
                if "\n" in info:  # multiline info
                    yield add_info_line, ("\n%s" % info,)
                yield add_update_info, (name, info, offer_update)
            else:
                yield add_update_info, (name, "no update lookup today", False)

    app = qapplication()
    dlg = UpdateDialog(script)
    dlg.exec_()

    at_least_one_sucess = False
    for id_ in dlg.get_updates_to_run():
        updater = registry.get(id_)
        ok, msg = updater.do_update(None)
        if not ok:
            print
            print "UPDATE FAILED:", msg
            print
        else:
            at_least_one_sucess = True
    if at_least_one_sucess:
        import emzed.gui
        emzed.gui.showInformation("please restart emzed to activate updates")


def interactive_update():
    # called at emzed.workbench startup, uncaught exception might freeze shell/console !
    try:
        _interactive_update()
    except:
        import traceback
        traceback.print_exc()
        raise
