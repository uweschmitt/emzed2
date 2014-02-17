def install_emzed(user_ns=None):

    import emzed

    emzed.project.install_builtins()
    emzed.project.activate_last_project()

    import os, sys
    user_ns.update(locals())
