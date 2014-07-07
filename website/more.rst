
Why did we develop emzed ?
~~~~~~~~~~~~~~~~~~~~~~~~~~

When we started to develop LCMS analysis workflows we discovered that most of the exisiting
frameworks and software belong to one of the following opposite categories:

* Our goal was to develop a framework which combines the positive aspects of two extremes:
  One the one side there exist fast and **flexible** frameworks, but in languages as C++ which only
  can be used efficiently by experienced programmers. One the other side *GUI* based applications
  are simple to use and learn but hard to adapt.

* The invention of programming environments as *Matlab* and *R* leveraged the productivity of
  mathematicians and scientists from other fields. We try to introduce this concept for analyzing
  LCMS data.

  *emzed* is based on Spyder [spyderlib]_ for providing the IDE and [guiqwt]_ and [guidata]_ for
  plotting.

* Instead of reinventing the wheel we cherry pick algorithms from established libraries and
  frameworks as [OpenMS]_ and [XCMS]_. These are wrapped behind a **consistent application
  programming interface (API)** and thus *emzed* based workflows reduce manual and error prone
  import and export steps.




Credits
~~~~~~~

We make use of the following frameworks and we thank their developers for the great work:

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
