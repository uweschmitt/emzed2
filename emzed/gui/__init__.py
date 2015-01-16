from file_dialogs import (askForDirectory, askForSave, askForSingleFile, askForMultipleFiles,
                          chooseConfig)


# order of next two imports is important, as the first patches some items: ###################
from dialog_builder import (showWarning, showInformation, DialogBuilder, RunJobButton,
                            askYesNo, WorkflowFrontend,
                            )
from dialog_builder_items import *
# order of the previous two imports is importang, see remark above  ##########################

from ..core.explorers.inspectors import inspect #, inspectPeakMap, inspectChromatograms
from ..core.explorers import inspectChromatograms


def inspectPeakMap(*a, **kw):
    """DEPRECATED! PLEASE USE inspect INSTEAD!"""
    print "DEPRECIATED ! PLEASE USE inspect INSTEAD !"
    inspect(*a, **kw)

try:
    del inspectors
except:
    pass

try:
    del file_dialogs
except:
    pass

try:
    del dialog_builder
except:
    pass

