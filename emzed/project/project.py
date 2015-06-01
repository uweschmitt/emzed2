from ..core.config import global_config
from ..core.packages import is_project_folder
import os
import glob
import shutil
import sys
import subprocess


def _get_local_package_folder(p):
    project_home = global_config.get("project_home").strip()
    folder = os.path.join(project_home, p)
    return folder


def is_emzed_package(p):
    """ tests if package named p exists in project home and is marked as emzed project """
    project_home = global_config.get("project_home").strip()
    local_packages = os.listdir(project_home)
    if p in local_packages:
        return is_project_folder(os.path.join(project_home, p))
    return False


def _run_setup_py_develop(p, flag):
    if is_emzed_package(p):
        f = _get_local_package_folder(p)
        old_dir = os.getcwd()
        try:
            os.chdir(f)
            subprocess.call("python setup.py develop %s" % flag, shell=True)
        finally:
            os.chdir(old_dir)
    else:
        raise Exception("%s is no local emzed project")


def deactivate(p):
    """ after calling deactivate the package p can not be imported any more """
    _run_setup_py_develop(p, "-u")
    if p in sys.modules:
        del sys.modules[p]


def activate(p):
    """ after calling activate the package p can be imported """
    _run_setup_py_develop(p, "")


def list_projects():
    """ prints list of project in project home folder and returns list of
        names of emzed projects found """
    project_home = global_config.get("project_home").strip()
    print
    print "LOCAL EMZED PROJECTS: ".ljust(80, "-")
    print
    result = []

    if not project_home:
        print
        print "project_home not set.please use emzed.config.edit() to fix this."
        print
    elif not os.path.exists(project_home):
        print
        print "... invalid settings", project_home, "does not exist please use emzed.config.edit()"
        print "to fix this."
        print
    else:
        for p in os.listdir(project_home):
            folder = os.path.join(project_home, p)
            if is_project_folder(folder):
                print (p + " ").ljust(19, " "),
                result.append(p)
                try:
                    pp = __import__(p)
                    folder = os.path.dirname(pp.__file__)
                    folder = folder.rjust(60, " ")
                    if len(folder) > 60:
                        print "/...", folder[-55:]
                    else:
                        print folder
                except:
                    print "INACTIVE".rjust(60, " ")
    if not result:
        print "NO PROJECTS FOUND"
    print
    print "".ljust(80, "-")
    print
    return result


def init(name=None, project_home=None):
    """ creates new project named 'name' in project home folder """
    from ..gui import DialogBuilder, showWarning
    if project_home is None:
        project_home = global_config.get("project_home").strip()
        if not project_home:
            raise Exception("no project folder configured. please run emzed.config.edit()")

    from ..core.packages import create_package_scaffold, check_name
    if name is None:
        while True:
            name = DialogBuilder().addString("Package Name")\
                .addInstruction("valid package names contain a-z, 0-9 and '_' and start "
                                "with a lower case letter").show()
            complaint = check_name(name)
            if not complaint:
                break
            showWarning(complaint)

    try:
        mod = __import__(name)
    except:
        pass
    else:
        raise Exception("package with name %s already exists: %s" % (name, mod.__file__))

    folder = os.path.join(project_home, name)
    try:
        create_package_scaffold(folder, name)
    except Exception, e:
        raise

    __builtins__["___activate_%s" % name] = lambda: start_work(name)
    print
    print "project scaffold created, enter emzed.project.start_work() to start working on it."
    print
    print "please edit setup.py for your needs"
    os.chdir(folder)
    try:
        # should be set during ipython shell startup
        open_in_spyder(os.path.join(folder, "setup.py"))
    except:
        pass
    start_work(name, project_home)
    __builtins__["___start_work_on_%s" % name] = lambda name=name: start_work(name)


def _get_active_project():
    proj = __builtins__.get("__emzed_project__")
    if not proj:
        raise Exception("no active project set")
    return proj


def _set_active_project(project):
    if project is not None:
        project = os.path.abspath(project)
    __builtins__["__emzed_project__"] = project


def install_builtins():

    __builtins__["___start_work"] = start_work
    __builtins__["___init_new_project"] = init
    __builtins__["___list_my_projects"] = list_projects
    __builtins__["___install_wheel"] = install_wheel
    __builtins__["___update_wheel"] = update_wheel
    __builtins__["___remove_wheel"] = remove_wheel

    for _n in list_projects():
        __builtins__["___start_work_on_%s" % _n] = lambda _n=_n: start_work(_n)


def _install_builtins_after_workon():
    __builtins__["___stop_work"] = stop_work
    __builtins__["___run_tests"] = run_tests
    __builtins__["___build_wheel"] = build_wheel


def _uninstall_builtins_after_stop_work():
    del __builtins__["___stop_work"]
    del __builtins__["___run_tests"]
    del __builtins__["___build_wheel"]


def stop_work():
    """ stops working on current project """

    _set_active_project(None)
    _uninstall_builtins_after_stop_work()

    try:
        import os
        os.chdir(__builtins__["__old_home"])
    except:
        pass

    global_config.set_("last_active_project", "")
    global_config.store()


def run_tests(filter_=None):
    """ runs tests on current project """
    ap = _get_active_project()
    path = os.path.join(ap, "tests")
    if filter_ is not None:
        fexpr = "-k '%s'" % filter_
    else:
        fexpr = ""
    subprocess.call("py.test %s %s" % (fexpr, path), shell=True, stderr=sys.__stderr__,
                    stdout=sys.__stdout__)


def _clean_build_folder(ap):
    build_folder = os.path.join(ap, "build")
    shutil.rmtree(build_folder, ignore_errors=True)

def build_wheel():
    """ creates a wheel for distributing current package """
    ap = _get_active_project()
    now = os.getcwd()

    _clean_build_folder(ap)

    os.chdir(ap)
    try:
        rv = subprocess.call("python setup.py bdist_wheel", shell=True, stderr=sys.__stdout__, stdout=sys.__stdout__)
        print
        print "IF YOU GOT THE MESSAGE THAT THE WHEEL ALREADY EXISTS YOU SHOULD REMOVE THE WHEEL"
        print "OR UPDATE THE VERSION NUMBER IN setup.py"
        print
        dist_folder = os.path.join(ap, "dist")
        wheels = os.listdir(dist_folder)
        for w in wheels:
            shutil.move(os.path.join(dist_folder, w), ".")
        print
        print "FOR DISTRIBUTION:"
        for w in glob.glob("*.whl"):
            print "CREATED", w
        print
    finally:
        os.chdir(now)


def install_wheel(wheel_file=None, _flags=[]):
    from ..gui import askForSingleFile
    if wheel_file is None:
        wheel_file = askForSingleFile(extensions=["whl"])
        if wheel_file is None:
            raise Exception("installation of wheel aborted")
    if not os.path.exists(wheel_file):
        raise Exception("%s not found" % wheel_file)
    __, ext = os.path.splitext(wheel_file)
    if ext.lower() != ".whl":
        raise Exception("wrong extension of %s, expected .whl" % wheel_file)
    args = ["pip", "install"] + _flags + [wheel_file]
    subprocess.call(args, shell=True, stderr=sys.__stdout__, stdout=sys.__stdout__)


def update_wheel(wheel_file=None):
    install_wheel(wheel_file, _flags=["-U"])


def remove_wheel(package_name):
    args = ["pip", "uninstall", "-y", package_name]
    subprocess.call(args, shell=True, stderr=sys.__stdout__, stdout=sys.__stdout__)


def _upload(secret=""):
    """ uploads current project to package store"""
    ap = _get_active_project()
    from ..core.packages import upload_to_emzed_store
    upload_to_emzed_store(ap, secret)


def _remove_from_package_store(version_string, secret=""):
    """ removes version 'version_string' of current project from package store """
    ap = _get_active_project()
    from ..core.packages import delete_from_emzed_store
    import os
    print
    ok = raw_input("ARE YOU SURE TO DELTED VERSION %s OF %s FROM PACKAGE STORE (Y/N) ? ")
    if ok != "Y":
        print
        print "ABORTED"
        return
    __, name = os.path.split(ap)
    delete_from_emzed_store(name, version_string, secret)


def _list_versions(secret=""):
    """ lists available versions of current project on package store """
    ap = _get_active_project()
    from ..core.packages import list_packages_from_emzed_store
    __, name = os.path.split(ap)
    packages = list_packages_from_emzed_store().get(name)
    print
    if not packages:
        print "PACKAGE NOT FOUND ON EMZED PACKAGE STORE"
    else:
        versions = [v for (v, __) in packages]
        print "VERSIONS ON EMZED PACKAGE STORE:"
        print
        for v in versions:
            print "   %s.%s.%s" % v


def start_work(name=None, project_home=None):
    """ activate project 'name' for working on it """
    import os
    from ..core.packages import is_project_folder
    __builtins__["__old_home"] = os.getcwd()
    full_path = None
    if name is None:
        if is_project_folder("."):
            full_path = os.path.abspath(os.getcwd())
            _set_active_project(full_path)
        else:
            raise Exception("either cd to emzed project before you call emzed.project.start_work, "
                            "or provide a project name or a full path")
    else:
        if project_home is None and is_project_folder(name):  # might happen in workbench
            full_path = os.path.join(os.path.abspath(os.getcwd()), name)
            _set_active_project(full_path)
            print "CWD TO", full_path
            os.chdir(full_path)
        else:
            if project_home is None:
                from ..core.config import global_config
                project_home = global_config.get("project_home").strip()
                if not project_home:
                    raise Exception("no project folder configured. please run emzed.config.edit()")
            full_path = os.path.join(project_home, name)
            if is_project_folder(full_path):
                _set_active_project(full_path)
                print "CWD TO", full_path
                os.chdir(full_path)
            else:
                raise Exception("'%s' is not a valid project folder" % name)

    _install_builtins_after_workon()

    import subprocess
    import sys
    subprocess.call(
        "python setup.py develop", shell=True, stderr=sys.__stderr__, stdout=sys.__stdout__)

    from ..core.config import global_config
    global_config.set_("last_active_project", full_path)
    global_config.store()

    proc = subprocess.Popen("pip show %s" % name, shell=True, stdout=subprocess.PIPE)
    stdout, __ = proc.communicate()
    for line in stdout.split("\n"):
        if line.startswith("Requires: "):
            __, __, required_packages = line.partition("Requires: ")
            for p in required_packages.split(","):
                p = p.strip()
                if is_emzed_package(p):
                    activate(p)


def activate_last_project():
    """ checks emzed config for current project and activates this """

    last_active_project = global_config.get("last_active_project")
    project_home = global_config.get("project_home")

    if last_active_project:
        # start_work(last_active_project) # does not work, crashes on win maybe bcause
        # starting pythonin subprocess
        import os
        path_in_project_home = os.path.join(project_home, last_active_project)
        _set_active_project(path_in_project_home)
        print "CWD TO", path_in_project_home
        try:
            os.chdir(path_in_project_home)
        except:
            print "could not find project", last_active_project
        else:
            _install_builtins_after_workon()
