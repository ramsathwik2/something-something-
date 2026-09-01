@echo off
echo Building Kitty Installer (PyInstaller)...
python -m pip install pyinstaller --quiet
python -m PyInstaller --noconfirm --windowed --onedir --name Kitty ^
  --add-data "assets\sprites;assets\sprites" ^
  --icon "assets\sprites\frame_4.png" ^
  src\app.py
echo.
echo Build done: dist\Kitty\Kitty.exe
echo.
echo To make EXE installer, install Inno Setup and run:
echo   iscc installer\kitty.iss
pause
