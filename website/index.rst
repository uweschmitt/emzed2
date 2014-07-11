.. emzed documentation master file, created by
   sphinx-quickstart on Tue Jan 24 18:40:08 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

What is emzed ?
===============

  *emzed* is an open source framework for rapid and interactive development of
  LCMS data analysis workflows in `Python <http://www.python.org>`_.


What does this mean ?
---------------

  *emzed* makes experimenting with new analysis strategies for LCMS data as simple as possible.


Fundamental principles of emzed
---------------

1. Analysis workflows are *Python* scripts composing **emzed modules**.
   Single processing steps are explicit and clear which supports `reproducible research
   <http://reproducibleresearch.net/>`_.

2. We choose **Python** which makes programming with *emzed* `as simple as possible
   <http://xkcd.com/353/>`_.

3. In order to strengthen the trust in analysis results, emzed provides **interactive
   visualization** of input data, as well as inspection of intermediate and final results.

4. *emzed* ships with **emzed workbench** which is an `integrated development environment (IDE) 
   <http://en.wikipedia.org/wiki/Integrated_development_environment#Overview>`_ to
   support the use of *emzed modules* and the overall development process.


Screenshots
---------------

.. fancybox:: welcome2emzed_fig1.png
    :width: 35.2%
    :height: 35.2%

.. fancybox:: welcome2emzed_fig2a.png
    :width: 25.3%
    :height: 25.3%


.. fancybox:: welcome2emzed_fig2b.png
    :width: 26.5%
    :height: 26.5%



Development goals
---------------

* When we started to implement own analysis workflows we found that the software landscape
  was almost divided into two classes:
  On the one side there exist fast and **flexible** frameworks, but in languages as C++ which only
  can be used efficiently by experienced programmers. One the other side there are applications
  with graphical user interfaces which are simple to use and learn but hard to modify for
  special needs.

  Our primary goal has been to develop a framework which combines the positive aspects of the two
  extremes.

* The invention of programming environments as *Matlab* and *R* leveraged the productivity of
  mathematicians and scientists from other fields. We try to introduce this concept for analyzing
  LCMS data.

  *emzed* is based on Spyder [spyderlib]_ for providing the IDE and [guiqwt]_ and [guidata]_ for
  plotting.

* Instead of reinventing the wheel we cherry pick algorithms from established libraries and
  frameworks as [openms]_ and [xcms]_. These are wrapped behind a **consistent application
  programming interface (API)** and thus *emzed* based workflows avoid manual and error prone
  import and export steps.



Website Navigation
~~~~~~~~~~~~~~~~~~

.. toctree::

    :maxdepth: 2

    more
    installation
    credits
    getting_started
    tour
    explorers
    api_ms
    api_batches
    api_tables_expressions
    api_other
    api_mstypes
    faq
    license
    contact

    references





Indexes and tables
~~~~~~~~~~~~~~~~~~

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
