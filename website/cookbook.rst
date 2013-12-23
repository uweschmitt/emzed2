.. _cookbook:

Cookbook -- Solutions for common problems
=========================================

How do I get all files in a given directory with given file extension ?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. pycon::
   import glob
   print glob.glob("examples\\*.mzXML") !noexec
   print ["examples/data1.mzXML", "examples/data2.mzXML"] !onlyoutput
   


