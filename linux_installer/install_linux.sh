#!/bin/bash

function test_if_programm_can_be_called {
    # this is trick from http://stackoverflow.com/questions/592620/
    hash $1 2>/dev/null 1>&2
	if [ $? -ne 0 ]; then
		echo
		echo "command $1 not found"
		echo
		exit $?
	fi
	echo "command $1 found"
}


function test_python_package {

	python2.7 -c "import $1" 2>/dev/null

	if [ $? -ne 0 ]; then
		echo
		echo "python package $1 not found"
		echo
		exit $?
	fi
	echo "python package $1 found"
}

function test_python_install {
	python2.7 -V 2>/dev/null

	if [ $? -ne 0 ]; then
		echo
		echo "python2.7 not found"
		echo
		exit $?
	fi
	echo "python2.7 found"
	test_python_package numpy
	test_python_package scipy
	test_python_package PyQt4
	test_python_package matplotlib
	test_python_package virtualenv
}

function try_and_halt_if_error {
    "$@"
    local status=$?
    if [ $status -ne 0 ]; then
        echo "error with $1"
    fi
    return $status
}


function install_emzed_and_related_packages {
    try_and_halt_if_error source $1/bin/activate
    try_and_halt_if_error easy_install pyopenms
    try_and_halt_if_error pip install cython
    try_and_halt_if_error pip install guidata
    try_and_halt_if_error pip install guiqwt
    try_and_halt_if_error pip install sphinx
    try_and_halt_if_error pip install -r http://emzed.ethz.ch/downloads/requirements.txt
}

function create_shortcut {

    SHORTCUT_FILE=$HOME/Desktop/emzed.workbench.desktop
    cat > $SHORTCUT_FILE <<- EOF
			[Desktop Entry]
			Version=1.0
			Type=Application
			Terminal=false
			Name=emzed.workbench
			Exec=$1/bin/emzed.workbench
			Icon=$1/lib/python2.7/site-packages/emzed/workbench/icon256.xpm
		EOF

    chmod a+x $SHORTCUT_FILE;
    echo
    echo "INSTALLED SHORT CUT"
    echo
}

echo
echo TEST FOR NEEDED INSTALLS
echo

test_python_install

test_if_programm_can_be_called virtualenv

echo
echo INSTALLATIONS OK
echo

DEFAULT_INSTALL_FOLDER=$HOME/emzed2_installation

echo
echo -n "please choose installation folder for emzed. "
echo -n "[empty input installs to $DEFAULT_INSTALL_FOLDER]: "
read INSTALL_FOLDER
echo

if [ -z $INSTALL_FOLDER ]; then
	INSTALL_FOLDER=$DEFAULT_INSTALL_FOLDER
fi

YES_NO=""
while [ ! "$YES_NO" = "y" ]; do
    echo -n "are you shure to install to $INSTALL_FOLDER ? [y/n]: "
    read YES_NO

    if [ "$YES_NO" = "n" ]; then
        echo 
        echo "ABORTED"
        exit;
    fi
done

echo


virtualenv --python=python2.7 --system-site-packages $INSTALL_FOLDER

if [ $? -ne 0 ]; then
    echo
    echo "ERROR: running virtualenv-2.7 failed"
    echo
    exit $?;
fi;

install_emzed_and_related_packages $INSTALL_FOLDER

echo
echo "ALL PYTHON PACKAGES INSTALLED"
create_shortcut $INSTALL_FOLDER
echo
echo "Check your desktop for the emzed icon. You can start emzed with"
echo "$ $INSTALL_FOLDER/bin/emzed.workbench"
echo
