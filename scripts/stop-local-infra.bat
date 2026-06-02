@echo off
setlocal

set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%"

if not exist "docker\local\.env.local" (
  echo Missing docker\local\.env.local
  echo Copy docker\local\.env.example to docker\local\.env.local and fill required values first.
  exit /b 1
)

docker compose --env-file docker\local\.env.local -f docker-compose.local.yml down

