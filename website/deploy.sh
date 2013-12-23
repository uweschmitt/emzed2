#!/bin/sh

platform=$(python -c "import sys; print sys.platform")

cd _build/html

if [ $platform = 'linux2' ]; then
    if [ -d /mnt/mickey  ]; then
        # on linux
        cp -v -R . /mnt/mickey
    else
        echo "/mnt/mickey does not exit";
        echo;
    fi;
else
    cp -v -R . //mickey.ethz.ch/mz$
fi;
