set PYTHONPATH=%1
> run_or_bootstrap.bat (
    @echo set SCRIPTS=%%APPDATA%%\emzed2\Scripts
    @echo call %%SCRIPTS%%\activate ^|^| ^(
    @echo     call install_emzed.bat %PYTHONPATH%
    @echo ^)
    @echo call %%SCRIPTS%%\activate
    @echo call %%SCRIPTS%%\emzed.workbench.exe
)
