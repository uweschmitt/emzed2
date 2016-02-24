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

easy_install http://www.voidspace.org.uk/python/pycrypto-2.6.1/pycrypto-2.6.1.win32-py2.7.exe

easy_install emzed
