# About

This folder (except the "installer_to_download/ subfolder) contains the files
needed to build the windows installer.

The windows installer is minimalistic: When run the installer queries the setup
of Winpython and executes "create_bootstrap.bat" so that a file
"run_or_bootstrap.bat" is created in "C:\Programs (x86)".

When starting emzed this "run_or_boostrap.bat" is executed. Then

- if the virtualenv %APPDATA%\emzed is not present the file install_emzed.bat
  is downloaded from emzed.ethz.ch/downloads and executed. This installs all
  needed extra Python packages plus the latest officially published version of
  emzed.

- else: the virtualenv is activated and "emzed.workbench" (then present in
  %PATH%) is run.


# Why so complicated ?

- The WinPython distribution has the benefit not to interfer with other Python
  installations but the drawback is that it is not registered in Windows
  registry. So the installer needs to handle this (manual selectino + dynamic
  creation of run_or_bootstrap.bat)

- To install emzed on managed computers of ETH DBIOL a special "app kiosk"
  version of emzed must be created. This is cumbersome and introduces delays in
  case of bug fixes. Fetching "install_emzed.bat" from the emzed website
  introduces in indirection which allows fixing the actual installer without
  creating a new "app kiosk" version.
