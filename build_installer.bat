@echo off
echo Building Kitty Installer (PyInstaller)...
python -m pip install "pyinstaller>=6.11,<7" --quiet
python -m PyInstaller --noconfirm --windowed --onedir --name Kitty ^
  --hidden-import "cryptography.fernet" ^
  --hidden-import "cryptography.hazmat.backends.openssl" ^
  --hidden-import "pystray._win32" ^
  --add-data "assets\sprites;assets\sprites" ^
  --add-data "assets\meow.wav;assets" ^
  --icon "assets\sprites\frame_4.png" ^
  src\app.py
echo.
echo Build done: dist\Kitty\Kitty.exe
echo.
echo To make EXE installer, install Inno Setup and run:
echo   iscc installer\kitty.iss
pause
