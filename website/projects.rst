emzed Projects
==============

Create your own emzed project
-----------------------------

Before you start on your own emzed project, make sure that the emzed project folder is configured::

    import emzed.config   # not needed if working in workbench
    emzed.config.edit()

All project related commands in ``emzed`` workbench start with three underscores ``___`` which
helps to use command completion with ``TAB`` when working on projects.

Alternatives for initializing a new package ``demo_package``::

    ___init_new_project()                # asks for name
    ___init_new_project("demo_package")  # only a-z, 0-9 and '_' are allowed


Outside the workbench you can use::

    emezd.project.init()                 # asks for name
    emezd.project.init("demo_package") 


This sets up a folder scaffold for your project inside the configured emzed project folder
and changes the current working directory to it.

You should edit these files:

- ``LICENSE``: at least edit *year* and *name of author* and give a one line description
  in the marked places.

- ``README`` is the place to describe your project.

- ``setup.py`` is the configuration file which is needed for installation and distribution
  of your package:

  - If you set ``IS_EXTENSION`` to ``True`` your package can be imported in emzed as
    ``emzed.ext.demo_package``.

  - If you set ``APP_MAIN`` your extension is installed below ``emzed.app`` and can be started
  as ``emzed.app.demo_package()``. The value of ``APP_MAIN`` hints to the Python file and function
  in this file which is started in the end.

  - You should fill out author information ``AUTHOR``, ``AUTHOR_EMAIL`` and ``AUTHOR_URL`` with
  your name, email adress and website.

  - ``DESCRIPTION`` and ``LONG_DESCRIPTION`` will be shown as information on Pythons Package
  Index if you upload your packae.

  - Check that the value of ``LICENSE`` fits your needs.

  - **DO NOT TOUCH THE LINES BELOW UNLESS YOU KNOW WHAT YOU ARE DOING**

Further the following folders are created below the project folder:

- ``demo_package`` for the Python modules of your package. Study the files inside this
  folder in order to understand how to setup these files. If you are new to Python you first
  should learn about implementation of Python modules and packages.

- ``tests`` for unit tests. It is important that the files in this folder and the test
  functions in these files start with ``test_``. You find demo files there.

Working on your project
-----------------------

The ``IPython`` prompt in the workbench console shows the active project. You can change
or set this using two alternative abbreviations::

    ___start_work_on()                # asks for name
    ___start_work_and_demo_packabe()

Outside the workbench you can use one of::

    emzed.project.activate_last_project()
    emzed.project.activate("demo_package")


Starting  ``emzed.workbench`` the last package you worked on is activated by default.


Writing and running tests
-------------------------

As said ``tests`` contains should contain tests for your package. It is important that the files in
this folder and the test functions in these files start with ``test_``. You find demo files there.

To run the tests start::

    ___run_tests()

Or::

    emzed.project.run_tests()

Distributing your package
-------------------------

Either::

    ___build_wheel()

or::

    emzed.project.build_wheel()

create a file with extension ``.whl`` in your project folder. You can send this file to
colleagues which can install it using::

    ___install_wheel()                                   # asks for whl file
    ___install_wheel("/tmp/downloads/demo_package.whl")  # you can also provide a path

or::

    emzed.project.install_wheel()                        # asks for whl file
    emzed.project.install_wheel("/tmp/downloads/demo_package.whl")
