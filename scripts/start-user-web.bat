@echo off
setlocal

set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%\jrunmall-user-web"

if not exist node_modules (
  echo Installing user web dependencies...
  npm install
)

echo Starting jrunmall-user-web at http://127.0.0.1:5174 ...
npm run dev -- --host 127.0.0.1 --port 5174

