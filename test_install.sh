#!/bin/sh
#
# 1) virtualenv
# 2) pip install -i http://localhost:8080/simple
# 3) python -c "import emzed.workbench; emzed.workbench.install_core()"
# 3) python -c "import emzed.core"
# 4) startup workbench

# wie repository konfigurieren ???? -> umgebungsvariable

echo
echo 
rm -rvf ../tmp/tmp.*
echo
echo
TMPDIR=$(mktemp -d --tmpdir=../tmp)
virtualenv $TMPDIR
. $TMPDIR/bin/activate
echo 
echo
pip install -i http://localhost:3142/root/dev/+simple emzed.workbench
emzed.worbench
pip install -i http://localhost:3142/root/dev/+simple minimal_extension
python -i -c "import emzed.ext; print dir(emzed.ext)"


