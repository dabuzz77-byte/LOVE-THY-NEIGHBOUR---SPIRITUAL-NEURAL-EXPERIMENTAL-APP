$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    py -3 -m venv .build-venv
    if ($LASTEXITCODE -ne 0) { throw 'Python virtual environment creation failed.' }
    & '.\.build-venv\Scripts\python.exe' -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    & '.\.build-venv\Scripts\python.exe' -m unittest discover -s . -p 'test_*.py'
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
    & '.\.build-venv\Scripts\python.exe' -m PyInstaller --noconfirm --clean --distpath .build-release --workpath .build FluxBus.spec
    if ($LASTEXITCODE -ne 0) { throw 'Executable build failed.' }
    # Stage separately so PyInstaller cannot replace the user's data folder.
    Copy-Item -Path '.build-release\FluxBus-v2\*' -Destination .. -Recurse -Force
} finally {
    Pop-Location
}
