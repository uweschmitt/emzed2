set PYTHONPATH=%1
> run_or_bootstrap.bat (
    @echo set SCRIPTS=%%APPDATA%%\emzed2\Scripts
    @echo call %%SCRIPTS%%\activate ^|^| ^(
    @echo     %PYTHONPATH% -c "import urllib, os; app=os.environ.get('APPDATA'); urllib.urlretrieve('http://emzed.ethz.ch/downloads/install_emzed.bat', os.path.join(app, 'install_emzed.bat'))"
    @echo     call %%APPDATA%%\install_emzed.bat %PYTHONPATH%
    @echo ^)
    @echo call %%SCRIPTS%%\activate
    @echo call %%SCRIPTS%%\emzed.workbench.exe
)
