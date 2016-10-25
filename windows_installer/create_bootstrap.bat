set PYTHONPATH=%1
> run_or_bootstrap.bat (
    @echo set SCRIPTS=%%APPDATA%%\emzed2\Scripts
    @echo call %%SCRIPTS%%\activate ^|^| ^(
    @echo     %PYTHONPATH% -c "import urllib; urllib.urlretrieve('http://emzed.ethz.ch/downloads/install_emzed.bat', 'install_emzed.bat')"
    @echo     call install_emzed.bat %PYTHONPATH%
    @echo ^)
    @echo call %%SCRIPTS%%\activate
    @echo call %%SCRIPTS%%\emzed.workbench.exe
)
