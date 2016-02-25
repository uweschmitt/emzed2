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
set MPLCONFIGDIR=.

pip install "pycryptodome<=3.3"

easy_install emzed

REM boostrap libs:
emzed.workbench.debug

