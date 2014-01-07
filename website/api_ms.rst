API utils Module
================

.. automodule:: emzed.utils


I/O
~~~

.. autofunction:: emzed.io.loadPeakMap
.. autofunction:: emzed.io.storePeakMap

.. autofunction:: emzed.io.loadCSV
.. autofunction:: emzed.io.storeCSV

.. autofunction:: emzed.io.loadTable
.. autofunction:: emzed.io.storeTable


Inspecting Tables and Peak maps
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: emzed.gui.inspectPeakMap
.. autofunction:: emzed.gui.inspect

For more information about using these Explorers see :ref:`explorers`. 


MZ Alignment
~~~~~~~~~~~~

.. autofunction:: emzed.align.mzAlign


RT Alignment
~~~~~~~~~~~~

For an example see :ref:`rtalign_example`

.. autofunction:: emzed.align.rtAlign


Integrating Peaks
~~~~~~~~~~~~~~~~~

.. autofunction:: emzed.utils.integrate

Generating Formulas for given mass range
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: emzed.utils.formulaTable


Working with molecular formulas
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: emzed.utils.formula

.. autofunction:: emzed.utils.addmf


Simulating Isotope Distributions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: emzed.utils.isotopeDistributionTable



.. autofunction:: emzed.utils.plotIsotopeDistribution


Statistics
~~~~~~~~~~

.. autofunction:: emzed.stats.oneWayAnova
.. autofunction:: emzed.stats.kruskalWallis

see :ref:`statistics_example` for example usage

.. autofunction:: emzed.stats.oneWayAnovaOnTables
.. autofunction:: emzed.stats.kruskalWallisOnTables


Helpers
~~~~~~~

.. autofunction:: emzed.utils.mergeTables
.. autofunction:: emzed.utils.toTable

Simple Dialogs
~~~~~~~~~~~~~~

.. autofunction:: emzed.gui.askForDirectory
.. autofunction:: emzed.gui.askForSave
.. autofunction:: emzed.gui.askForSingleFile
.. autofunction:: emzed.gui.askForMultipleFiles
.. autofunction:: emzed.gui.showWarning
.. autofunction:: emzed.gui.showInformation


DialogBuilder
~~~~~~~~~~~~~

For an example see  :ref:`dialogbuilder_example`

.. autoclass:: emzed.gui.DialogBuilder



