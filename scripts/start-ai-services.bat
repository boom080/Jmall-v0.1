@echo off
setlocal EnableDelayedExpansion

if /I "%~1"=="--help" goto :help

set "FORCE_INSTALL=false"
if /I "%~1"=="--install" (
  set "FORCE_INSTALL=true"
  shift
)

set "AI_SERVICE_HOST=127.0.0.1"
set "AI_SERVICE_PORT=18080"

if not "%~1"=="" set "AI_SERVICE_HOST=%~1"
if not "%~2"=="" set "AI_SERVICE_PORT=%~2"

cd /d "%~dp0.."

if exist ".env.local" (
  echo [INFO] Loading environment from .env.local...
  for /f "usebackq eol=# tokens=1* delims==" %%A in (".env.local") do (
    set "ENV_KEY=%%A"
    set "ENV_VALUE=%%B"
    if /i "!ENV_KEY:~0,7!"=="export " set "ENV_KEY=!ENV_KEY:~7!"
    for /f "tokens=* delims= " %%K in ("!ENV_KEY!") do set "ENV_KEY=%%K"
    for /f "tokens=* delims= " %%V in ("!ENV_VALUE!") do set "ENV_VALUE=%%V"
    if "!ENV_VALUE:~0,1!"=="^"" if "!ENV_VALUE:~-1!"=="^"" set "ENV_VALUE=!ENV_VALUE:~1,-1!"
    if "!ENV_VALUE:~0,1!"=="'" if "!ENV_VALUE:~-1!"=="'" set "ENV_VALUE=!ENV_VALUE:~1,-1!"
    if not "!ENV_KEY!"=="" if not "!ENV_KEY:~0,1!"=="#" set "!ENV_KEY!=!ENV_VALUE!"
  )
)

if not defined DEEPSEEK_API_KEY if defined JRUNMALL_AI_DEEPSEEK_API_KEY set "DEEPSEEK_API_KEY=%JRUNMALL_AI_DEEPSEEK_API_KEY%"
if not defined QWEN_API_KEY if defined JRUNMALL_AI_QWEN_API_KEY set "QWEN_API_KEY=%JRUNMALL_AI_QWEN_API_KEY%"
if not defined DEEPSEEK_BASE_URL if defined JRUNMALL_AI_DEEPSEEK_BASE_URL set "DEEPSEEK_BASE_URL=%JRUNMALL_AI_DEEPSEEK_BASE_URL%"
if not defined DEEPSEEK_MODEL if defined JRUNMALL_AI_DEEPSEEK_MODEL set "DEEPSEEK_MODEL=%JRUNMALL_AI_DEEPSEEK_MODEL%"
if not defined QWEN_BASE_URL if defined JRUNMALL_AI_QWEN_BASE_URL set "QWEN_BASE_URL=%JRUNMALL_AI_QWEN_BASE_URL%"
if not defined QWEN_CHAT_MODEL if defined JRUNMALL_AI_QWEN_MODEL set "QWEN_CHAT_MODEL=%JRUNMALL_AI_QWEN_MODEL%"

cd /d "%~dp0..\ai-services"

if not exist ".venv\Scripts\python.exe" (
  echo [INFO] ai-services\.venv not found. Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 exit /b 1
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 exit /b 1

if /I "%FORCE_INSTALL%"=="true" (
  echo [INFO] Installing ai-services dependencies...
  python -m pip install -r requirements.txt
  if errorlevel 1 exit /b 1
) else (
  echo [INFO] Reusing existing ai-services virtual environment. Use --install for first-time dependency install.
)

echo [INFO] Starting ai-services: http://%AI_SERVICE_HOST%:%AI_SERVICE_PORT%
python -m uvicorn app.main:app --reload --host %AI_SERVICE_HOST% --port %AI_SERVICE_PORT%
exit /b %errorlevel%

:help
echo Usage: scripts\start-ai-services.bat [--install] [host] [port]
echo Example: scripts\start-ai-services.bat --install 127.0.0.1 18080
exit /b 0

