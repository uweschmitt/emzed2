.. _api_overview:


Overview over APIs
==================

 The most important features of *emzed* are briefly explained on this page, grouped according to the modules they belong to.
 
 
Representation of Mass-spectrometry Data
----------------
Details of objects in emzed which can hold mass spectrometry-related data, as wel as their member functions, can be found on :ref:`api_mstypes`.

Loading and Saving
----------------
The *emzed.io* module allows to read data from files, or to save data to files. It is describen on :ref:`api_io`

Peak Detection Algorithms
----------------
The three peak detection algorithms of *emzed* can be found in the feature finder module *emzed.ff*, see :ref:`api_feature_finders`
To execute them in batches, the *emzed.batches* module is useful, see :ref:`api_batches`
The process of centroiding data is also described there.

Alignment
----------------
It is often necesary to align the data from two or more mass spectrometry experiments which shall be compared. This can be done as explained in :ref:`api_align`.

Tables & Expressions
----------------
Tables hold information which can be organised into rows of the same length. Expressions arise from operations such as addition or comparison. For details check :ref:`api_tables_expressions`.

Statistical Analysis
--------------
To perform a statistical analysis of your data, please refer to :ref:`api_stats`.

Inspecting Tables & Peak Maps and Building Graphical User Interfaces
----------------------
The page :ref:`api_gui` contains the following information:

* First, the work with tables and peak maps is described there.
* Additionally, the page explains how you can build your own graphical items, such as dialogs, as is also examplified in :ref:`dialogbuilder_example2`.

Helper Modules
----------------------
Finally, there are so called helper modules, which give masses and abundances of elements or data of adducts. See :ref:`api_other` for details.