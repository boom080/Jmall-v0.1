@echo off
setlocal EnableDelayedExpansion

set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%"

if exist ".env.local" (
  echo Loading environment from .env.local...
  for /f "usebackq tokens=1* delims==" %%A in (".env.local") do (
    set "ENV_KEY=%%A"
    if not "!ENV_KEY!"=="" if not "!ENV_KEY:~0,1!"=="#" set "%%A=%%B"
  )
)

if not defined JRUNMALL_SECKILL_ADDR set "JRUNMALL_SECKILL_ADDR=127.0.0.1:19090"
if not defined JRUNMALL_SECKILL_STREAM set "JRUNMALL_SECKILL_STREAM=jrunmall:seckill:orders"
if not defined JRUNMALL_SECKILL_KEY_PREFIX set "JRUNMALL_SECKILL_KEY_PREFIX=jrunmall:seckill"
if not defined JRUNMALL_SECKILL_ORDER_TOKEN_PREFIX set "JRUNMALL_SECKILL_ORDER_TOKEN_PREFIX=SEC"

if not defined JRUNMALL_SECKILL_REDIS_URL (
  if defined GULIMALL_REDIS_HOST (
    if defined GULIMALL_REDIS_PORT (
      set "JRUNMALL_SECKILL_REDIS_URL=redis://!GULIMALL_REDIS_HOST!:!GULIMALL_REDIS_PORT!/0"
    )
  )
)

cd /d "%ROOT_DIR%\jrunmall-seckill-go"

echo Starting jrunmall-seckill-go at http://%JRUNMALL_SECKILL_ADDR% ...
echo Redis URL: %JRUNMALL_SECKILL_REDIS_URL%
go run .\cmd\server
