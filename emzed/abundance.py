
from collections import defaultdict as _defaultdict

_abu = _defaultdict(dict)

from emzed.core.chemistry.elements import (Elements as _Elements,
                                           create_abundance_mapping)

for element, abundances in create_abundance_mapping().items():
    locals()[element] = abundances
    for mass_number, abundance in abundances.items():
        locals()["%s%d" % (element, mass_number)] = abundance
