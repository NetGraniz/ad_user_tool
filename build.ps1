# Clean previous builds
if (Test-Path "build") { Remove-Item build -Recurse -Force }
if (Test-Path "dist") { Remove-Item dist -Recurse -Force }

# Activate virtual environment
& ".\.venv\Scripts\Activate.ps1"

# Find iuliia package path
$iuliia = python -c "import pathlib, iuliia; print(pathlib.Path(iuliia.__file__).parent / 'schemas')"

# Build executable
pyinstaller `
    --clean `
    --onefile `
    --noconsole `
    --name "ad_user_tool" `
    --add-data "$iuliia;iuliia/schemas" `
    ad_user_tool.py

Write-Host ""
Write-Host "Build completed successfully." -ForegroundColor Green
Write-Host "Executable: dist\ad_user_tool.exe"