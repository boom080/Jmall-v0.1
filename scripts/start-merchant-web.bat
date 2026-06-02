@echo off
setlocal

set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%\jrunmall-merchant-web"

if not exist node_modules (
  echo Installing merchant web dependencies...
  npm install
)

echo Starting jrunmall-merchant-web at http://127.0.0.1:5175 ...
npm run dev -- --host 127.0.0.1 --port 5175

