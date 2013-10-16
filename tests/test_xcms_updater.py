def test_xcms_updater():
    import emzed.core.config
    import emzed.updaters

    emzed.updaters.setup_updaters()

    updater = emzed.updaters.get("xcms_updater")
    emzed.updaters.reset("xcms_updater")
    assert updater.offer_update_lookup() is True
    id_, ts, info, offer_update = updater.query_update_info()
    assert id_ == "xcms_updater"
    assert ts <= 0
    assert isinstance(info, basestring)
    rv = updater.do_update()
    assert rv == (True, "ok")
