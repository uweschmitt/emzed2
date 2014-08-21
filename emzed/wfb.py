# encoding: utf-8

"""emzed workflow builder module
"""

import pacer


class CacheBuilder(pacer.CacheBuilder):

    def __init__(self, project_folder):
        super(CacheBuilder, self).__init__(project_folder)

        def _get_origin(o):
            return o.meta.get("_origin")

        def _set_origin(o, origin):
            o.meta["_origin"] = origin
            return o

        from .core.data_types import Table, PeakMap
        from .io import loadTable, loadPeakMap, storeTable, storePeakMap
        self.register_handler(Table,
                              lambda t: t.uniqueId(),
                              ".table",
                              loadTable,
                              lambda t, p: storeTable(t, p, True),
                              _get_origin,
                              _set_origin)

        self.register_handler(PeakMap,
                              lambda t: t.uniqueId(),
                              ".mzML",
                              loadPeakMap,
                              storePeakMap,
                              _get_origin,
                              _set_origin)

from pacer import apply, join, summarize, Engine, files_from
del pacer
