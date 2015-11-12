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


Presentation
------------

You find some slides about emzed and how the story started at |presentation_link|.

.. |presentation_link| raw:: html

   <a href="http://emzed.ethz.ch/presentation" target="_blank">http://emzed.ethz.ch/presentation</a>


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
  can be used efficiently by experienced programmers. On the other hand, there are applications
  with graphical user interfaces that are simple to use and learn but hard to modify for
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


emzed in the press
------------------

Recent publications using emzed for data analysis:

* Peter et al. "Screening and Engineering the Synthetic Potential of Carboxylating Reductases from Central Metabolism and Polyketide Biosynthesis." Angew Chem Int Ed Engl. (2015).
* Kiefer, Patrick, et al. "DynaMet, a fully automated pipeline for dynamic LC-MS data." Analytical Chemistry (2015).
* Ryffel, Florian, et al. "Metabolic footprint of epiphytic bacteria on Arabidopsis thaliana leaves." The ISME journal (2015).
* Müller, Jonas EN, et al. "Core pathways operating during methylotrophy of Bacillus methanolicus MGA3 and induction of a bacillithiol-dependent detoxification pathway upon formaldehyde stress." Molecular microbiology (2015).
* Müller, Jonas EN, et al. "Engineering Escherichia coli for methanol conversion." Metabolic engineering 28 (2015): 190-201.
* Wilson, Micheal C., et al. "An environmental bacterial taxon with a large and distinct metabolic repertoire." Nature 506.7486 (2014): 58-62.
* Erb, Kiefer, et al. "GFAJ-1 is an arsenate-resistant, phosphate-dependent organism", Science (2012).

Website Navigation
---------------

.. toctree::

    :maxdepth: 2

    installation
    credits
    getting_started
    tour
    explorers

    faq
    license
    contact

    references

APIs: Overview
~~~~~~~~~~~~~~
.. toctree::

    :maxdepth: 1
    
    api_overview
    
APIs: Detailed List
~~~~~~~~~~~~~~~~~~~
.. toctree::

    :maxdepth: 2
    
    api_mstypes
    api_io
    api_feature_finders
    api_align
    api_batches
    api_tables_expressions
    api_utils
    api_stats
    api_gui
    api_other
    projects






Indexes and tables
~~~~~~~~~~~~~

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
