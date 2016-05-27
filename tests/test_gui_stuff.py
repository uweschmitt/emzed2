# encoding: utf-8
from __future__ import print_function, division, absolute_import

import guidata
from emzed.core.explorers.async_runner import AsyncRunner

import pytest


@pytest.mark.skipif(False, reason="crashes on new mac when qapplication is called")
def test_async(regtest):

    app = guidata.qapplication()  # singleton !

    def f(x):
        return x + 1

    def g(x):
        app.quit()

    def report(msg):
        print(msg, file=regtest)

    runner = AsyncRunner(reporter=report)
    runner.run_async_chained((f, f, f, f, f, g), (0,))
    app.exec_()
