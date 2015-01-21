for U in *.ui; do
    python /usr/local/Cellar/pyqt/4.11.1/lib/python2.7/site-packages/PyQt4/uic/pyuic.py -w -x $U | grep -v "# Created:" > _${U%.ui}.py
done;
