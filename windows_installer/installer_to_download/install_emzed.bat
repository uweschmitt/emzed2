set PYTHONHOME=%~dp1
set INSTALLTARGET=%APPDATA%\emzed2
@echo.

%PYTHONHOME%\python.exe ez_setup.py
@echo.

rem on some machines we find the python script on others the exe, so we try both:
%PYTHONHOME%\python.exe -m pip install virtualenv

@echo.
%PYTHONHOME%\python.exe -m virtualenv --system-site-packages %INSTALLTARGET%
@echo.
call %INSTALLTARGET%\Scripts\activate
@echo.
@echo.

rem newer setuptools will not install ipython==0.10 below
pip install setuptools==28.0

rem "pip install" will download a binary package if available, but when
rem resolving dependencies pip will download source packages. This causes
rem trouble on most machines having no appropriate microsoft compiler
rem installed.  so we first install all pre compiled binary packages and the
rem final "pip install emzed" will only install source distributed stuff:

rem upate numpy first, then scipy, pyopenms needs new numpy to work and
rem scipy depends on numpy:
pip install http://emzed.ethz.ch/downloads/numpy-1.11.1+mkl-cp27-cp27m-win_amd64.whl
pip install http://emzed.ethz.ch/downloads/scipy-0.17.0-cp27-none-win_amd64.whl
@echo.
pip install pyopenms==2.0.1
@echo.
python -c "import pyopenms"
@echo.
pip install emzed_optimizations
@echo.
pip install -U ipython==0.10
@echo.
pip install -U dill
@echo.
pip install "pycryptodome<=3.3"
@echo.

:: create unique url to bypass potential cache:
set always_different_id=%RANDOM%%RANDOM%%RANDOM%
pip install http://emzed.ethz.ch/downloads/emzed.zip?%always_different_id%

REM sometimes matplotlib setup is broken, this should fix this:
set MPLCONFIGDIR=%APPDATA%\matplotlib_config
python -c "import matplotlib"
python -c "import matplotlib"

REM boostrap libs:
emzed.workbench.debug
