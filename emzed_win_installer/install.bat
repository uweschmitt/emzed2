set PYTHONHOME=%~dp1
set INSTALLTARGET=%APPDATA%\emzed2
@echo.

%PYTHONHOME%\python.exe ez_setup.py
@echo.
%PYTHONHOME%\python.exe %PYTHONHOME%\Scripts\easy_install-script.py virtualenv
@echo.
%PYTHONHOME%\python.exe %PYTHONHOME%\Scripts\virtualenv-script.py --system-site-packages %INSTALLTARGET%
@echo.
call %INSTALLTARGET%\Scripts\activate
@echo.
easy_install -U "guiqwt>=2.3.1"
@echo.
easy_install -U "guidata>=1.6.0"
@echo.
easy_install pyopenms==1.11
@echo.
python -c "import pyopenms"
@echo.
easy_install emzed_optimizations
@echo.
easy_install -U ipython==0.10
@echo.
easy_install -U spyder==2.1.13
@echo.
easy_install emzed

