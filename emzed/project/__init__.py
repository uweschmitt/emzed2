

def init(name=None):
    from ..core.config import global_config
    from ..gui import DialogBuilder, showWarning
    project_home = global_config.get("project_home").strip()
    if not project_home:
        raise Exception("no project folder configured. please run emzed.config.edit()")

    from ..core.packages import create_package_scaffold, check_name
    if name is None:
        while True:
            pkg_name = DialogBuilder().addString("Package Name")\
                    .addInstruction("valid package names contain a-z, 0-9 and '_' and start " \
                    "with a lower case letter").show()
            complaint = check_name(pkg_name)
            if not complaint:
                break
            showWarning(complaint)

    import os
    folder = os.path.join(project_home, name)
    try:
        create_package_scaffold(folder, name)
    except Exception ,e:
        showWarning(str(e))
        return

    print
    print "project scaffold created, enter emzed.project.activate() to start working on it."
    print
    print "please edit setup.py for your needs"
    os.chdir(folder)
    try:
        # should be set during ipython shell startup
        open_in_spyder(os.path.join(folder, "setup.py"))
    except:
        pass


def _get_active_project():
    return __builtins__.get("__emzed_project__")

def _set_active_project(project):
    if project is not None:
        import os
        project = os.path.abspath(project)
    __builtins__["__emzed_project__"] = project


def _run_setup_py_develop(uninstall=False):
    #subprocess runnint "setup.py develop [-u]"  kills socket for monitor thread !!!, so:
    import sys, os

    from setuptools.command.develop import develop
    from setuptools import Distribution

    import sys
    sys.path.insert(0, ".")
    import setup
    sys.path.pop(0)

    d = Distribution(dict(name=setup.PKG_NAME,
                          packages=[setup.PKG_NAME],
                          version=setup.VERSION_STRING,
                          entry_points=setup.ENTRY_POINTS))
    d.script_name = "setup.py"
    cmd = develop(d)
    cmd.user = 1
    cmd.uninstall = uninstall
    cmd.ensure_finalized()
    import site
    cmd.install_dir = site.USER_SITE
    cmd.user = 1
    cmd.run()

def deactivate():
    ap = _get_active_project()
    if ap is not None:
        import subprocess
        subprocess.call("python setup.py develop -u", shell=True)

        _set_active_project(None)
        del __builtins__["___deactivate"]
        del __builtins__["___run_tests"]
        del __builtins__["___upload"]
        try:
            from IPython import ipapi
            ipapi.get().IP.home_dir = __builtins__["__old_home"]
        except:
            pass

    else:
        raise Exception("no active project set")

def run_tests():

    ap = _get_active_project()
    if ap is not None:
        import os
        import subprocess
        path = os.path.join(ap, "tests")
        subprocess.call("py.test %s" % path, shell=True)
    else:
        raise Exception("no active project set")

def upload():
    ap = _get_active_project()
    if ap is not None:
        from emzed.core.packages import upload_to_emzed_store
        upload_to_emzed_store(ap)
    else:
        raise Exception("no active project set")


def activate(name=None):
    import os
    from emzed.core.packages import is_project_folder
    if name is None:
        if is_project_folder("."):
            _set_active_project(os.getcwd())
        else:
            raise Exception("either cd to emzed project before you call emzed.project.activate, "\
                    "or provide a project name or a full path")
    else:
        if is_project_folder(name):
            _set_active_project(name)
            os.chdir(name)
        else:
            from ..core.config import global_config
            project_home = global_config.get("project_home").strip()
            path_in_project_home = os.path.join(project_home, name)
            if is_project_folder(path_in_project_home):
                _set_active_project(path_in_project_home)
                os.chdir(path_in_project_home)
            else:
                raise Exception("'%s' is not a valid project folder" % name)

    __builtins__["___deactivate"] = deactivate
    __builtins__["___run_tests"] = run_tests
    __builtins__["___upload"] = upload

    try:
        from IPython import ipapi
        __builtins__["__old_home"] = ipapi.get().IP.home_dir
        ipapi.get().IP.home_dir = os.getcwd()
    except:
        pass

    import subprocess
    subprocess.call("python setup.py develop", shell=True)
    #_run_setup_py_develop()


__builtins__["___activate"] = activate
__builtins__["___init"] = init








