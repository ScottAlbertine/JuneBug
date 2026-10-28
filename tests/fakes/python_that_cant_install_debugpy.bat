@echo off
:: Fake python interpreter for testing debugpy installation failures on Windows.
:: When called with `-c "import debugpy"`, it fails (simulating no debugpy).
:: When called with `-m pip install debugpy`, it fails with specific output.

if "%1"=="-c" (
  :: Simulate failing to import debugpy
  exit /b 1
) else if "%2"=="pip" (
  :: Simulate pip install failing with specific output
  <nul set /p "=sample stdout"
  <nul set /p "=sample stderr" 1>&2
  exit /b 1
) else (
  exit /b 1
)
