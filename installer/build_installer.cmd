@echo off
chcp 65001 >nul
rem Собирает dist\Turok2_Russian_Setup.exe (нужен .NET Framework 4.x — есть в любой Windows 10/11).
rem Перед этим соберите мод: python tools\build.py
setlocal
cd /d "%~dp0.."
if not exist dist\Siberian.kpf (
  echo Нет dist\Siberian.kpf — сначала выполните: python tools\build.py
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
echo Готово: dist\Turok2_Russian_Setup.exe
