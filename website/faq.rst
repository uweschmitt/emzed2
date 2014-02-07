.. _faq:

FAQ (Frequently Asked Questions)
================================

1. How can I process SRM/MRM data ?
-----------------------------------

We provide an example workflow ``srm_tool.py`` for exploring and target
extraction of SRM/MRM data in the ``emzed_files/exampled_scripts`` folder which
is located in your home directory. This folder is created when you start
*eMZed* the first time.

2. What does postfix mean ?
----------------------------

In *eMZed* postfixes are strings which appear at the end of column names, in
most cases a postfix has the form ``"__x"``, but even the empty string ``""``
is a valid postfix. Postfixes are created by ``Table.join`` in order to ensure
unique column names. Further the postfix identifies columns of common origin.


3. Which kind of tables can be handled by ``ms.integrate`` ?
------------------------------------------------------------

In general you can pass any kind of *eMZed* table to ``ms.integrate``.
In order to apply peak integration you need column names which start
with ``mzmin``, ``mzmax``, ``rtmin``, ``rtmax`` and ``peakmap`` and share
the same postfix (see quesiton no. 2).
