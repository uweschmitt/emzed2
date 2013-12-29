.. _installation:

Installation
============


.. _before_you_start:

Before you start
~~~~~~~~~~~~~~~~

If you plan to use *emzed* for more than one user we recommend to provide a
shared folder, which can be accessed by all targeted users. We call this the
*global exchange folder*.  *emzed* will store databases, and *R* related code
there.

You can use *emzed* without such a folder.

Support
~~~~~~~

If you have problems installing *emzed*, please use the discussion group
at http://groups.google.com/group/emzed-users


Installing on 64 bit Windows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For installing *emzed* on Windows please follow **carefully** the stepwise
instructions. **version numbers and file names matter**.

**We recommend to use WinPython as described below. WinPython can be installed next to
an existing Python installation without causing conflicts, unless you register WinPython from its
control panel.**

1. For installing *Python 2.7* first download *WinPython* with version 2.7.5.X
   64 bit or higher from https://code.google.com/p/winpython/. The current
   version of *emzed* is not Python 3 ready.

2. Run the *WinPython* installer. This step only unpacks *WinPython* to a target directory
   you can choose. If you are unsure choose a directory like **C:\WinPython-X.Y.Z**.
   Keep the install target in mind, you will need this path for the next step.

3. Download the installer http://emzed.ethz.ch/downloads/emzed2_setup.exe.
   Run the installer with administator rights.
   The installer asks for the path to the Python interpreter to use.
   This should be a path similar to **C:\WinPython-X.Y.Z\python-x.y.z\python.exe**.

   The installation process needs a few minutes, so stay patient.

4. Now you should find emzed in windows start menu.

5. optional: install **R** if you want to use centwave or any other R library.



Installing on Ubuntu or Debian
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As *numpy*, *scipy* and *matplotlib* are difficult to build, first install
those globally.  *PyQt4* should be installed globally too::

    $ sudo apt-get install python2.7
    $ sudo apt-get install python2.7-numpy python2.7-scipy python2.7-matplotlib python2.7-qt4
    $ sudo apt-get install python2.7-virtualenv

For the following steps we provide an installation script at
http://emzed.ethz.ch/downloads/install_linux.sh which should work on current
Ubuntu and Debian Linux installations. The script asks for an installation directory,
which can be inside your personal users home folder, which is suggested::

    $ wget http://emzed.ethz.ch/downloads/install_linux.sh
    $ bash install_linux.sh

The script should create a short cut on your desktop and print the direct path
for starting emzed from the command line.


Manual installation on Linux
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have a Linux distribution for which the previous instructions failed, you have
to proceed manually as described now:

  1. Install Python 2.7
  2. Install numpy, at least versoin 1.7.0
  3. Install Pyhton packages scipy, matplotlib, PyQt4 and virtualenv

In order to keep your Python installation in a clean and consistent state, we recommend
to install *emzed* using *virtualenv*. This gives you an isolated environment without
version conflicts and avoids cluttering your system.
Now create a virtual environment, we recommend to start in your home directory::

    $ pwd
    /home/uschmitt
    $ virtualenv-2.7 --system-site-packages emzed2
    ....
    $ cd emzed2
    $ source emzed2/bin/activate
    (emzed2) $ easy_install pyopenms
    (emzed2) $ pip install cython
    (emzed2) $ pip install guidata
    (emzed2) $ pip install guiqwt
    (emzed2) $ pip install sphinx
    (emzed2) $ pip install -r http://emzed.ethz.ch/downloads/requirements.txt
    (emzed2) $ deactivate

Now you should be able to start emzed workbench::

    $ ~/emzed2/bin/emzed.workbench
    

Getting the latest development version of emzed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*emzed* is hosted on http://github.com/uweschmitt/emzed2, after installing
``git`` you can check out the latest version using::

    git clone git://github.com/uweschmitt/emzed2.git



