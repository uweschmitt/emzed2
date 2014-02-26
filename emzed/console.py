def main():
    import IPython.Shell
    from emzed.workbench.install import install_emzed
    user_ns = dict()
    install_emzed(user_ns)
    user_ns["__emzed_imported_by"] = "emzed.console"
    shell = IPython.Shell.IPShellQt4(user_ns=user_ns)
    shell.mainloop()
