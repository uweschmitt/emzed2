.. _installation:

Installation
------------

The current version of *emzed* was developed and tested on 32 and 64 bit Windows XP, 7 and 8 just
as 64 bit Ubuntu Linux and Mac OS X.
The current version of *emzed* relies on Python 2.7.X and is not Python 3 ready.



.. note::

    If you have problems installing *emzed*, please use the discussion group
    at http://groups.google.com/group/emzed-users




Installing on 64 bit Windows
----------------------------

.. caution::
    For installing *emzed* on Windows please follow carefully the stepwise
    instructions. Version numbers and file names matter.


1. Download and install *Microsoft Visual C++ 2008 SP1 Redistributable Package
   (x64)* from http://www.microsoft.com/en-us/download/details.aspx?id=2092

2. Download the latest *WinPython* version 2.7.6.X
   for 64 bit from http://winpython.sourceforge.net/.

   .. note::
      Do not confuse *WinPython* with the official Python for windows release from
      http://www.python.org.

3. Run the *WinPython* installer. This step only unpacks *WinPython* to a target directory
   you can choose. If you are unsure choose a directory like **C:\\WinPython-x.y.z**.

   .. note::
      keep the install target in mind, you will need this path for the next step.

4. Download the installer http://emzed.ethz.ch/downloads/emzed2_setup.exe.
   and run it wit administator rights.

   The installer asks for the path to the Python interpreter to use.
   You will find it inside the **python-x.y.z** subfolder of the installation
   from the previous step.
   If you folllowed the recommandation from step 3, the path to the Python interpreter
   should be similar to **C:\\WinPython-x.y.z\\python-x.y.z\\python.exe**.

   The installation process needs a few minutes, so stay patient.

4. Now you should find *emzed* in Windows start menu.

5. optional: install **R** if you want to use XCMS or any other R library.



Installing on Ubuntu or Debian
------------------------------

1. *numpy*, *scipy* and *matplotlib* are difficult to build, first install
   those globally.  *PyQt4* should be installed globally too::

    $ sudo apt-get install python2.7
    $ sudo apt-get install python2.7-numpy python2.7-scipy python2.7-matplotlib python2.7-qt4
    $ sudo apt-get install python-qwt5-qt4
    $ sudo apt-get install python2.7-virtualenv

2. For the final installation download the installation script from
   http://emzed.ethz.ch/downloads/install_emzed2.sh.
   Running the script you are asked for the 
   target folder, we recommend to use the proposed default value.::

    $ bash install_emzed2.sh

3. In case of success the script prints the direct path
   for starting *emzed* from the command line. Further you should find the *emzed* icon
   on your desktop.


Manual installation on Linux
--------------------------

If you have a Linux distribution for which the previous instructions failed, you have
to proceed manually as described now:

1. Install Python 2.7.

2. Install numpy, at least versoin 1.7.0.

3. Install Python packages scipy, matplotlib, PyQt4 and virtualenv.

.. note::
    In order to keep your Python installation in a clean and consistent state, we recommend
    to install *emzed* using *virtualenv*.  This gives you an isolated environment without
    version conflicts and avoids cluttering your system.

To create such a virtual environment, we recommend to start in your home directory::

    $ cd
    $ virtualenv-2.7 --system-site-packages emzed2
    ....
    $ cd emzed2
    $ source bin/activate
    (emzed2)$ easy_install pyopenms
    (emzed2)$ pip install cython
    (emzed2)$ pip install guidata
    (emzed2)$ pip install guiqwt
    (emzed2)$ pip install sphinx
    (emzed2)$ pip install -r http://emzed.ethz.ch/downloads/requirements.txt
    (emzed2)$ deactivate

Now you should be able to start *emzed workbench*::

    $ source ~/emzed2/bin/activate
    $ emzed.workbench


Getting the latest development version of emzed
-----------------------------------------------

*emzed* is hosted on http://github.com/uweschmitt/emzed2, after installing
``git`` you can check out the latest version using::

    git clone git://github.com/uweschmitt/emzed2.git



