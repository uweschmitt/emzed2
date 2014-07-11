set INSTALLTARGET=%APPDATA%\emzed2
set PYTHONPATH=%1
> run_or_bootstrap.bat (
    @echo call %INSTALLTARGET%\Scripts\activate ^|^| ^(
    @echo     call install_emzed.bat %PYTHONPATH%
    @echo ^)
    @echo call %INSTALLTARGET%\Scripts\activate
    @echo call %INSTALLTARGET%\Scripts\emzed.workbench.exe
)
