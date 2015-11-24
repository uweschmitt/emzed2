.. _fix_windows:

Fix broken emzed after update
=============================

We try hard to maintain a stable Windows Version of `emzed` but tracking all
changes in 3rd party libraries is cumbersome and thus automating the installation and update
process is difficult and will hardly never be perfect.

Often resetting all local configuration and package files helps.

This is the recommended procedure:

1. Open Windows Explorer and change to the folder named ``%APPDATA%`` as you can see here:

    .. image:: appdata.png

2. After pressing the ``Enter`` key the folder opens. Among the listed files and folders you should see:

   - ``.spyder2``
   - ``emzed2``

3. Delete those two entries, **make sure that they are fully removed** !

4. Start *emzed*, *emzed* should now re-install all needed 3rd party libraries.

5. Hopefully *emzed* is fixed now.
