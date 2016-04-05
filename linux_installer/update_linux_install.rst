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
