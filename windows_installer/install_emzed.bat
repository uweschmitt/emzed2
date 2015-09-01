set PYTHONHOME=%~dp1
set INSTALLTARGET=%APPDATA%\emzed2
@echo.

%PYTHONHOME%\python.exe ez_setup.py
@echo.

rem on some machines we find the python script on others the exe, so we try both:
%PYTHONHOME%\python.exe %PYTHONHOME%\Scripts\easy_install-script.py virtualenv
%PYTHONHOME%\python.exe %PYTHONHOME%\Scripts\easy_install.exe virtualenv

@echo.
%PYTHONHOME%\python.exe %PYTHONHOME%\Scripts\virtualenv-script.py --system-site-packages %INSTALLTARGET%
@echo.
call %INSTALLTARGET%\Scripts\activate
@echo.
easy_install -U setuptools
@echo.
pip install pyopenms
@echo.
python -c "import pyopenms"
@echo.
easy_install emzed_optimizations
@echo.
easy_install -U ipython==0.10
@echo.
easy_install -U dill
@echo.
set MPLCONFIGDIR=.
easy_install emzed
