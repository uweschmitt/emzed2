

def init(name=None):
    from ..core.config import global_config
    from ..gui import DialogBuilder, showWarning
    project_home = global_config.get("project_home").strip()
    if not project_home:
        raise Exception("no project folder configured. please run emzed.config.edit()")

    import re
    if name is None:
        while True:
            name = DialogBuilder().addString("Package Name")\
                    .addInstruction("valid package names contain a-z, 0-9 and '_' and start " \
                    "with a lower case letter").show()
            if name.lower() != name:
                showWarning("only lower case characters allowed in package name")
                continue
            if re.match("[a-z][a-z0-9_]*$", name) is None:
                showWarning("invalid chars in package name")
                continue
            break

    import os
    folder = os.path.join(project_home, "package_%s" % name)
    from ..core.packages import create_package_scaffold
    try:
        create_package_scaffold(folder, name)
    except Exception ,e:
        showWarning(str(e))
        return

    print
    print "project scaffold created, enter emzed.project.activate() to start working on it"





