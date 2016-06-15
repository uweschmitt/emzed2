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
pip install -U setuptools
@echo.

rem "pip install" will download a binary package if available, but when
rem resolving dependencies pip will download source packages. This causes
rem trouble on most machines having no appropriate microsoft compiler
rem installed.  so we first install all pre compiled binary packages and the
rem final "pip install emzed" will only install source distributed stuff:

pip install pyopenms
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
pip install http://emzed.ethz.ch/downloads/emzed.zip

REM sometimes matplotlib setup is broken, this should fix this:
set MPLCONFIGDIR=%APPDATA%\matplotlib_config
python -c "import matplotlib"
python -c "import matplotlib"

REM boostrap libs:
emzed.workbench.debug
