API ms Module
=============

.. automodule:: ms

MZ Alignment
~~~~~~~~~~~~

.. autofunction:: ms.mzAlign


RT Alignment
~~~~~~~~~~~~

For an example see :ref:`rtalign_example`

.. autofunction:: ms.rtAlign
   


Inspecting Tables and Peak maps
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. autofunction:: ms.inspectPeakMap
.. autofunction:: ms.inspect

For more information about using these Explorers see :ref:`explorers`. 


Integrating Peaks
~~~~~~~~~~~~~~~~~

.. autofunction:: ms.integrate

Generating Formulas for given mass range
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: ms.formulaTable


Working with molecular formulas
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: ms.formula

.. autofunction:: ms.addmf


Simulating Isotope Distributions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: ms.isotopeDistributionTable



.. autofunction:: ms.plotIsotopeDistribution


Statistics
~~~~~~~~~~

.. autofunction:: ms.oneWayAnova
.. autofunction:: ms.kruskalWallis

see :ref:`statistics_example` for example usage

.. autofunction:: ms.oneWayAnovaOnTables
.. autofunction:: ms.kruskalWallisOnTables


Helpers
~~~~~~~

.. autofunction:: ms.mergeTables
.. autofunction:: ms.toTable
.. autofunction:: ms.openInBrowser

Simple Dialogs
~~~~~~~~~~~~~~

.. autofunction:: ms.askForDirectory
.. autofunction:: ms.askForSave
.. autofunction:: ms.askForSingleFile
.. autofunction:: ms.askForMultipleFiles
.. autofunction:: ms.showWarning
.. autofunction:: ms.showInformation


DialogBuilder
~~~~~~~~~~~~~

For an example see  :ref:`dialogbuilder_example`

.. autoclass:: ms.DialogBuilder

I/O
~~~

.. autofunction:: ms.loadPeakMap
.. autofunction:: ms.storePeakMap

.. autofunction:: ms.loadCSV
.. autofunction:: ms.storeCSV

.. autofunction:: ms.loadTable
.. autofunction:: ms.storeTable


