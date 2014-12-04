#!/bin/sh

platform=$(python -c "import sys; print sys.platform")


if [ $platform = 'linux2' ]; then
    TARGET=/mnt/mickey
    if [ -d $TARGET ]; then
        # on linux
        echo "ok";
        echo;
    else
        echo "/mnt/mickey does not exit";
        echo;
    fi;
else
    TARGET=//mickey.ethz.ch/mz$
fi;

TARGET=/Volumes/mz\$
cd _build/html
cp -v -R . $TARGET
cd ../..
cp -v -R presentation $TARGET
