@echo off
setlocal

set "ACTIVITY_ID=%~1"
set "SKU_ID=%~2"
set "STOCK=%~3"

if "%ACTIVITY_ID%"=="" set "ACTIVITY_ID=flash-20260429"
if "%SKU_ID%"=="" set "SKU_ID=14"
if "%STOCK%"=="" set "STOCK=50"

powershell -NoProfile -Command ^
  "$body = @{ activityId = '%ACTIVITY_ID%'; skuId = [int64]%SKU_ID%; stock = [int]%STOCK% } | ConvertTo-Json; " ^
  "Invoke-WebRequest -UseBasicParsing -Method Post -Uri 'http://127.0.0.1:19090/api/seckill/warmup' -ContentType 'application/json' -Body $body | Select-Object -ExpandProperty Content"
