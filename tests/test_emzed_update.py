import pdb
def test_emzed_updater():
    import emzed.updaters
    import emzed.core.config
    emzed.core.config.global_config.set_("pypi_url", "http://pypi.python.org/pypi")
    emzed.core.config.global_config.set_("pypi_index_url", "http://pypi.python.org/simple")

    updater = emzed.updaters.get("emzed_updater")
    emzed.updaters.reset("emzed_updater")
    assert updater.offer_update_lookup() is True
    id_, ts, info, offer_update = updater.query_update_info()
    assert id_ == "emzed_updater"
    assert ts <= 0
    assert isinstance(info, basestring)
