.. emzed documentation master file, created by
   sphinx-quickstart on Tue Jan 24 18:40:08 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to emzed 2
------------------


Website Navigation
~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 1

   installation
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


About
~~~~~

.. image:: OSI-Approved-License-50x52.png
   :scale: 50 %
   :align: right

*emzed* is an open source framework for analyzing and processing LCMS
data. The framework was developed by D-BIOL (Patrick Kiefer, lab of
Julia Vorholt, Institute of Microbiology, ETH Zurich) and Uwe Schmitt (mineway
GmbH, Germany) with several ideas in mind:

.. image:: emzed_screen.png
   :align: right

* Current frameworks and software are located on one of the following extremes: 

 * Fast and flexible frameworks, but in languages as C++ which only
   can be used efficiently by experienced programmers. Further playing with new
   ideas for analyzing data is hard due to the programming
   effort and slow edit-compile cycles.  

 * Closed black box solutions with graphical user interfaces. These
   are easy to use, but show restricted flexibility.

Our goal was to combine the positive aspects of both extremes: an easy
to learn framework which is flexible and allows inspection and analysis
of data either interactive or by easy to write Python scripts. This is
one of the reasons why we choose Python as programming language.

* The invention of programming environments as Matlab and R
  leveraged the productivity of mathematicians and other scientists. We
  try to introduce this concept for analyzing LCMS data.

  *emzed* is based on Spyder [spyderlib]_ for providing
  the workspace and [guiqwt]_ and [guidata]_ for plotting.

* Instead of reinventing the wheel we cherry picked algorithms from
  other frameworks and libraries. In the current version we use
  algorithms from Open-MS [openms]_ and XCMS [xcms]_.

* In order to avoid imports and exports to other software, we try to
  integrate all needed functionality in one framework.


The current version of *emzed* was developed and tested on 32 and 64 bit Windows XP, 7 and 8 just
as 64 bit Ubuntu Linux.



Credits
~~~~~~~

We make use of the following frameworks and we thank their developers for the
great work:

     * Open-MS [openms]_
     * XCMS [xcms]_
     * spyderlib [spyderlib]_
     * guidata and guiqwt [guidata]_, [guiqwt]_

Personal thanks go to:

     *  Department of Biology, ETH Zurich

     *  Pierre Raybaut

     *  `Julia A Vorholt <http://www.micro.biol.ethz.ch/research/vorholt/jvorholt>`_

     *  Jacques Laville, central IT services ETH Zurich.

     *  `Jonas Grossmann <http://www.fgcz.ch/people/jgrossmann>`_

     *  `Peter Zoltan Kunszt <http://www.systemsx.ch/projects/systemsxch-projects/sybit/>`_

     *  `Lars Gustav Malström <http://www.imsb.ethz.ch/researchgroup/malars>`_






Indexes and tables
~~~~~~~~~~~~~~~~~~

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
