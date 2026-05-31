@echo off
cd /d "%~dp0"
python -m pip install -q -r requirements.txt
python build_ethernium.py
python tools\debug_rows.py
python tools\export_atlas.py
echo.
echo Abre preview_font.html para revisar la fuente.
pause
