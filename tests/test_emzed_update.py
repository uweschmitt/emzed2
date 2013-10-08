def test_emzed_updater():
    import emzed.updaters
    import emzed.core.config
    emzed.core.config.global_config.set_("pypi_url", "http://testpypi.python.org/pypi")
    emzed.core.config.global_config.set_("pypi_index_url", "http://testpypi.python.org/simple")

    updater = emzed.updaters.get("emzed_updater")
    emzed.updaters.reset("emzed_updater")
    assert updater.offer_update_lookup() is True
    id_, ts, info, offer_update = updater.query_update_info()
    assert id_ == "emzed_updater"
    assert ts <= 0
    assert info == "new emzed version 3.1375178237.93 available"
    assert offer_update
    rv = updater.do_update()
    assert rv == (True, "ok")

    import subprocess
    exit_code = subprocess.call("pip uninstall -y emzed", shell=True)
    assert exit_code == 0
