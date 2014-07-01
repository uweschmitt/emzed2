from emzed.core.config import global_config


def edit(reset_to_defaults=False):
    if reset_to_defaults:
        global_config.set_defaults()
    aborted = global_config.edit()
    if not aborted:
        global_config.store()


def load():
    global_config.load()


def store():
    global_config.store()


def _check_first_start():
    # is_started_from_cmdline() == True iff invoked via emzed.workbench command line command
    # in this case nothing should happen, because we want this actions
    # later in spyders ipython console where is_started_from_cmdline() is False.
    from _tools import (runs_inside_emzed_console, runs_inside_emzed_workbench, gui_running,
                        is_first_start)
    if is_first_start() and runs_inside_emzed_console():
        global_config.set_defaults()
        print
        print "loading emzed.config ".ljust(80, ".")
        print
        print "This is the first time you use emzed. Configuration values are set to their"
        print "default values. You can use "
        print
        print "     emzed.config.edit()"
        print
        print "to inspect and modify these."
        print
        print "".ljust(80, ".")
        store()
    elif is_first_start() and runs_inside_emzed_workbench():
        if gui_running():
            aborted = edit(reset_to_defaults=True)
            if not aborted:
                store()
            load()
        else:
            global_config.set_defaults()
            print
            print "loading emzed.config ".ljust(80, ".")
            print
            print "This is the first time you use emzed. Configuration values are set to their"
            print "default values. You can use "
            print
            print "     emzed.config.edit()"
            print
            print "to inspect and modify these."
            print
            print "".ljust(80, ".")
            store()
    else:
        load()

_check_first_start()
del _check_first_start
