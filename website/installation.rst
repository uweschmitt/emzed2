.. _installation:

Installation
============


.. _before_you_start:

Before you start
~~~~~~~~~~~~~~~~

If you plan to use *eMZed* for more than one user we recommend to provide a
shared folder, which can be accessed by all targeted users. We call this the
*global exchange folder*.  *eMZed* will store databases, and *R* related code
there.  Further you can use this folder to exchange scripts and configuration
settings.

You can use *eMZed* without such a folder. Then data is stored per user and
sharing of scripts will not work.

If you decide to make use of the global exchange folder,
**at least one of the users needs write access to this folder and should be the
first user who starts eMZed. Else eMZed will not be able to work correctly.**

For support
~~~~~~~~~~~

If you have problems installing *eMZed*, please use the discussion group
at http://groups.google.com/group/emzed-users


Updating on Windows
~~~~~~~~~~~~~~~~~~~

If you update from an older *eMZed* version based on *PythonXY*, the
recommeded way is to uninstall *PythonXY* and *pyOpenMS* first and to
install from scratch as described below.

Installing on 64 bit Windows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We changed the installing instructions for the 64 bit Windows version of 
*eMZed* and do not rely on *Python XY* any more.
Further we updated *eMZed* to the newest version of *pyopenms*.

The current version of *eMZed* is not available for 32 bit Windows.

For installing *eMZed* on Windows please follow **carefully** the stepwise
instructions. **version numbers and file names matter**.

1. Download *WinPython* 2.7.4.X 64 bit from https://code.google.com/p/winpython/

2. Run the installer. We propose to run the installer with administator rights
   and to choose a target directory. We recommend **C:\\WinPython-64bit-2.7.4.X** 
   as installation target, but you can use a sub folder of **C:\\Programmm Files** 
   or something similar.

3. Start *WinPython Control Panel* in the chosen installation directory.

4. Register *WinPython* by choosing the menu item *"Advanced->Register Distribution"*

5. Now you should be able to run *"All Programs -> WinPython -> WinPython Commmand Prompt"*
   from your Windows Start Button. Run this prompt with administration rights.

6. Run the command::

    pip install http://emzed.ethz.ch/downloads/setup_python_packages.zip

7. If you do not have *R* installed on your system, first **download**
   http://cran.r-project.org/bin/windows/base/R-3.0.0-win.exe
   and **run it with administration rights**, else you might get problems
   using R functionalities from eMZed.

   R with latest major version 2.X.Y should work too.

8. Download, unzip and install the latest version of *eMZed* from 
   http://emzed.ethz.ch/downloads/emzed_1.3.8_for_windows.zip
   Now you should have a start icon on your Desktop.

9. Start *eMZed*.

10. At the first start you are asked for the *global exchange folder*. 
   See :ref:`before_you_start`.

   **If you do not want to use an global exchange folder, you can leave the input field empty.**

11. *eMZed* will now retrieve or update a metabolomics related subset of the *PubChem* database 
   from the web.
   If you have a global exchange folder the full download will be stored there.
   Checking for update is done each time you start *eMZed*.

   **If you provided a global exchange folder and have no write permissions to it, this step wil be skipped**.

   **eMZed might freeze for some minutes during download. This is a known problem
   which we will fix with the next version**


12. *eMZed* will install or update the *XMCS*-code if needed. If you have a global exchange folder
   an *XCMS* [xcms]_ related code will be stored there, so further starts of *eMZed*  by local users
   will be much faster.

   **If you provided a global exchange folder and have no write permissions to it, this step wil be skipped**.


Installing on Ubuntu or Debian
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To get all needed packages for running *eMZed* download

     http://emzed.ethz.ch/downloads/install_contrib_linux.sh

Depending on your systems current setup you should look into this file
and adapt it for your needs.

Executing this script with ``sudo`` will download and install 
everything that is needed, including the *eMZed* files
in ``emzed_files_1.X.Y.zip``.  Start ``python emzed.py`` in the extracted
folder and follow the windows instruction above, beginning at item no. 10.

Getting the latest development version of eMZed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*eMZed* is hosted on http://github.com/uweschmitt/emzed, after installing
``git`` you can check out the latest version using::

    git clone git://github.com/uweschmitt/emzed.git



