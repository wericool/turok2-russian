@echo off
rem Builds dist\Turok2_Russian_Setup.exe (needs .NET Framework 4.x, present in Windows 10/11).
rem Build the mod first: python tools\build.py
setlocal
cd /d "%~dp0.."
if not exist dist\Siberian.kpf (
  echo dist\Siberian.kpf not found - run first: python tools\build.py
  exit /b 1
)
set CSC=%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe
if not exist "%CSC%" set CSC=%WINDIR%\Microsoft.NET\Framework\v4.0.30319\csc.exe
"%CSC%" /nologo /target:winexe /codepage:65001 /optimize+ ^
  /win32manifest:installer\app.manifest ^
  /resource:dist\Siberian.kpf,Siberian.kpf ^
  /r:System.Windows.Forms.dll /r:System.Drawing.dll ^
  /out:dist\Turok2_Russian_Setup.exe installer\Installer.cs
if errorlevel 1 exit /b 1
echo Done: dist\Turok2_Russian_Setup.exe
