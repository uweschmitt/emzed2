.. _installation:

Installation
------------

**Your current Windows Installation is broken ???** Goto :ref:`fix_windows` !!!.

The current version of *emzed* was developed and tested on 32 and 64 bit Windows XP, 7 and 8 as well
as 64 bit Ubuntu Linux and Mac OS X.
The current version of *emzed* relies on Python 2.7.X and is not Python 3 ready.



.. note::

    If you have problems installing *emzed*, please use the discussion group
    at http://groups.google.com/group/emzed-users




Installation on 64 bit Windows
~~~~~~~~~~

.. warning::
    For installing *emzed* on Windows please follow the stepwise
    instructions carefully. Version numbers and file names matter.


1. Download and install *Microsoft Visual C++ 2008 SP1 Redistributable Package
   (x64)* from http://www.microsoft.com/en-us/download/details.aspx?id=2092

2. Download *WinPython* version **2.7.9.5 (no other version !!!)**
   for **64 bit** from http://downloads.sourceforge.net/project/winpython/WinPython_2.7/2.7.9.5/WinPython-64bit-2.7.9.5.exe

   .. note::
      Do not confuse *WinPython* with the official Python for windows release from
      http://www.python.org.

      Take care to install the 64 bit version.

3. Run the *WinPython* installer. This step only unpacks *WinPython* to a target directory
   you can choose. We recommend to use **C:\\WinPython-2.7.9.5** unless you have some
   special reasons.

   .. note::
      Keep the install target in mind, you will need this path for the next step.

4. Download the installer http://emzed.ethz.ch/downloads/emzed2_setup.exe.
   and run it with administator rights.

   The installer asks for the path to the Python interpreter to use.

   If you folllowed the recommandation from step 3, the path to the Python interpreter
   is **C:\\WinPython-2.7.9.5\\python-2.7.9.amd64\\python.exe**.
   Else you will find the **python.exe** inside the **python-2.7.9.amd64**
   subfolder of the installation target from the previous step.

   The installation process opens a terminal window and runs for a few minutes, so stay patient.

4. Now you should find *emzed* in your Windows start menu.

5. optional: install `R <http://www.r-project.org/>`_ if you want to use *XCMS* or any other *R*
   library.



Installation on Ubuntu Linux
~~~~~~~~~~

The following package names are for Ubuntu 14.04 LTS**, for other distributions the names
may sligthly differ (for example `python2.7-matplotlib` instead of `python-matplotlib`).
If needed you can eg use `$ apt-cache search matplotlib` to lookup exact names on your machine.

1. First, you should install *numpy*, *scipy* and *matplotlib* globally as they
   are difficult to build. *PyQt4* should be installed globally too::

    $ sudo apt-get install python2.7
    $ sudo apt-get install python-numpy python-scipy python-matplotlib python-qt4
    $ sudo apt-get install python-pandas python-scikits-learn
    $ sudo apt-get install libncurses-dev
    $ sudo apt-get install python-qwt5-qt4
    $ sudo apt-get install python-virtualenv

2. For the final installation download the installation script from
   http://emzed.ethz.ch/downloads/install_emzed2.sh.
   The script will ask for the 
   target folder, we recommend to use the proposed default value.::

    $ bash install_emzed2.sh

3. After successful installation the script prints the direct path
   for starting *emzed* from the command line. Further, you should find the *emzed* icon
   on your desktop.

4. optional: install `R <http://www.r-project.org/>`_ if you want to use *XCMS* or any other *R*
   library::

    $ sudo apt-get install r-base

Manual Installation on Linux
~~~~~~~~~~

If you have a Linux distribution for which the previous instructions failed, you can install *emzed*
manually as described now:

1. Install Python 2.7.

2. Install numpy, at least version 1.7.0.

3. Install Python packages scipy, matplotlib, PyQt4 and virtualenv.

4. We recommend to install *emzed* using *virtualenv* as described below.

   .. note::
        *virtualenv* is a Python tool to create *virtual environments* which keep your Python
        installation in a clean and consistent state.
        *virtualenv* creates a local Python installation in a given folder  without version
        conflicts to parallell installations and avoids cluttering your system.

   Execute the listed statements, they will install *emzed* inside the folder ``emzed2`` in your
   home directory::

        $ cd
        $ virtualenv-2.7 --system-site-packages emzed2
        ....
        $ cd emzed2
        $ source bin/activate
        (emzed2)$ easy_install pyopenms==2.0
        (emzed2)$ pip install cython
        (emzed2)$ pip install "guiqwt<2.4.0" --allow-external guiqwt --allow-unverified guiqwt
        (emzed2)$ pip install "guidata<1.7.0" --allow-external guidata --allow-unverified guidata
        (emzed2)$ pip install sphinx
        (emzed2)$ easy_innstall ipython==0.10
        (emzed2)$ pip install emzed
        (emzed2)$ deactivate

   Now you should be able to start *emzed workbench*::

        $ source ~/emzed2/bin/activate
        $ emzed.workbench

4. optional: install `R <http://www.r-project.org/>`_ if you want to use *XCMS* or any other *R*
   library.

Getting the latest development version of emzed
~~~~~~~~~~

*emzed* is hosted on http://github.com/uweschmitt/emzed2, after installing
``git`` you can check out the latest version using::

    git clone git://github.com/uweschmitt/emzed2.git
