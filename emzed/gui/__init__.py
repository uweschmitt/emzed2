from file_dialogs import (askForDirectory, askForSave, askForSingleFile, askForMultipleFiles,
                          chooseConfig)


from dialog_builder import (showWarning, showInformation, DialogBuilder, RunJobButton,
                            WorkflowFrontend)

from ..core.explorers.inspectors import inspect #, inspectPeakMap, inspectChromatograms
from ..core.explorers import inspectChromatograms


def inspectPeakMap(obj):
    print "DEPRECIATED ! PLEASE USE inspect INSTEAD !"
    inspect(obj)

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

