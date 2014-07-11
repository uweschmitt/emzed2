.. _getting_started:

====================================
Getting started with emzed workbench
====================================

Before you start
----------------

*emzed* helps you to develop work flows by two means:

* a supportive development environment which we name *workbench* and

* a collection of *emzed modules* for typical
tasks which provide building blocks for an LCMS analysis work flows.

The following instructions help you to get started with the *workbench*,
:ref:`getting_started_with_emzed_modules` gives a first impression of
the functionalities provided by *emzed modules*.

We recommend to exercise the tutorial below before following
:ref:`getting_started_with_emzed_modules`.

The emzed workbench
-------------------

If you start *emzed* workbench the first time the user interface should look
like the following screen shot.  The window is divided into an editor for
*Python* code at the left, and a *variable explorer* above a *IPython console*
with an input prompt at the right.  You can resize and reorder them using your
mouse. This configuration is stored if you close *emzed* and if you start
*emzed* again, it will be restored.

.. fancybox:: emzed_workbench_overview.png
   :width: 50 %
   :height: 50 %



How to change the working directory?
------------------------------------

Like a Linux command line *emzed* has the concept of a *working directory*,
this is the location where the editor opens new files, and where scripts are
started when using the *IPython* shell.


.. fancybox:: emzed_working_dir.png
   :width: 65 %
   :height: 65 %

To change the working directory look at the labeled buttons in the screen
shot and follow theses instructions:

1. Press the "choose folder" button of *emzed* task bar (1.) and choose directory.

2. Press "set" button (2.) to set the current working directory to the chosen one.

After pressing the "set button" the command to change to the new working
directory is displayed in the IPython console.

If you you change to the ``emzed_files/example_files``
directory, which is located inside your home directory, you see that
a statement similar to the following one is executed in your *IPython* shell:

.. fancybox:: emzed_working_dir_cwd.png

This folder was created during the first startup of emzed.

You can verify the current working directory by typing ``pwd`` in the IPython
console. Press ``Enter``, type ``pwd`` and press ``Enter`` again.

.. fancybox:: emzed_working_dir_pwd.png

You can display the content of the current working directory by submitting
the ``ls`` command.

.. fancybox:: emzed_working_dir_ls.png
    :width: 40%
    :height: 40%


We will create now a new folder ``first_steps`` in the ``emzed_files``
directory. You can do that by clicking again the "choose folder button". Then
make a new folder called ``first_steps``, select it, and press again the "set"
button. We will use that folder later on during this tutorial.

.. fancybox:: emzed_working_dir_temp_folder.png


How to to work with the IPython console?
----------------------------------------

You can directly execute *Python*
commands in the provided IPython shell [ipython]_. If you follow the examples
below, this is the place to input and execute the demonstrated commands.

Here is a very simple example how to use the console:

.. fancybox:: ipython_code.png

The command creates a string object called ``welcome``. With the print command
the content of ``welcome`` is displayed in the console. The console provides
command completion and automatic dialog boxes showing a list of possible
methods which can be applied to the object ``welcome``. In the same way,
available methods on any type of object are shown automatically. You can
activate command completion after any character by pressing the ``Tab`` key.
All methods which can be applied to the object are displayed in the console by
typing the name of the object followed by a "``.``".  For given example:

.. fancybox:: ipython_object_operations.png

We will now apply the function ``capitalize`` to the string ``welcome``. You
get the documentation of ``capitalize`` by typing:

.. fancybox:: ipython_object_function_documentation.png

We can now to apply the function ``capitalize`` to the object ``welcome``:

.. fancybox:: ipython_apply_function.png

The result of the last command executed in the IPython console is always
accessible via underscore ``"_"``.  In case you forgot to assign a variable
name to a result you can do that afterwards by using the underscore ``"_"``.

.. fancybox:: ipython_working_with__.png

Further you can  navigate through commands you entered before using
the ``Cursor-Up`` and ``Cursor-Down`` keys. For more information about
using *IPython* [ipython]_ see the Introduction at [ipython_introduction]_ .

To get online help on IPython console type ``help()``.

You can find a more detailed IPython tutorial here_.

.. _here: http://ipython.org/ipython-doc/stable/interactive/tutorial.html





How to use emzed modules?
-------------------------


As an *example* we determine the isotope distribution of molecular formula
*C6H13O9P*. It can be calculated using the method *isotopeDistributionTable* of
the main *emzed* module *ms*. After typing ``ms.`` the auto completion shows
all methods of the module *ms*.

.. fancybox:: ipython_autocompletion.png

You can reduce the number of methods by typing ``ms.i`` and pressing the ``Tab``
key.

.. fancybox:: ipython_tab_button.png


To get help on the function type ``ms.isotopeDistributionTable?`` or
``help(ms.isotopeDistributionTable)`` and press ``Enter``.

.. fancybox:: emzed_modules_help.png

To execute the function type with default parameter settings type
``isotopes = ms.isotopeDistributionTable("C6H13O9P")`` and press ``Enter``.

.. fancybox:: ipython_execute_function.png


How to inspect objects?
-----------------------

.. _below:

The variable explorer provides an easy way to inspect all kinds of Python
objects. All object names and their properties are listed in the variable
explorer.  Here an example:

.. fancybox:: variable_explorer.png

To visualize the content of the variable ``isotopes`` double click the row and
a new window with the table explorer opens:

.. fancybox:: table_explorer.png

Some objects like e.g. tables have a print method. Type ``.print_()`` after
a table object and you can directly print the result in the console.

.. fancybox:: table_print().png

How to run scripts ?
--------------------

*emzed* work flows are Python scripts generally using functionalities provided
by *emzed* modules but also individual functions created by the user.


To build your own work flows you can use the *Editor* to write scripts and
functions which can be executed in the IPython console.

Here is a very simple example which implements a function that calculates the
mass of water using the module `mass`:

.. fancybox:: using_editor_code.png

Type the code into the editor and save it as ``using_editor.py``
into the working directory ``.../emzed_files/first_steps`` which we
set above.

There are two possibilities to run scripts in *emzed*.

1. You can execute the script currently displayed in the Editor  by simply
pressing the ``F5`` key. When the ``F5`` key is used the first
time a dialog box will open. Choose the first option "Execute in current
IPython or Python interpreter".

    .. fancybox:: run_script.png

When running the script you see that the ``print`` statement in the
last line of the example code is executed. Further the function
``mass_of_water`` is now available in the
*IPython* console. To call this function type the name of the function
followed by ``()`` and press ``Enter``.

    .. fancybox:: run_script_executing.png


2. You can also use the command ``runfile`` immediately. For given example:

.. fancybox:: run_script_alternative.png

If the script is not located in the working directory you have to add the path
of the script to its name like  ``runfile(".../folder/filename.py")``.



Next
----

Continue with :ref:`getting_started_with_emzed_modules`

