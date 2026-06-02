@echo off
setlocal

set "MODE=%~1"
if "%MODE%"=="" set "MODE=success"
if /I "%MODE%"=="--help" goto :help

set "API_URL=%PRODUCT_COPY_API_URL%"
if "%API_URL%"=="" set "API_URL=http://127.0.0.1:10000/product/ai/product-copy/generate"
if not "%~2"=="" set "API_URL=%~2"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$ErrorActionPreference='Stop';" ^
"$mode='%MODE%'; $url='%API_URL%';" ^
"switch ($mode) {" ^
"  'success' { $body = @{ title='轻薄商务笔记本'; category='电脑办公'; sellingPoints=@('13代酷睿','16GB 内存','高色域屏'); tone='professional' } }" ^
"  'invalid' { $body = @{ title=' '; category='电脑办公'; sellingPoints=@('13代酷睿'); tone='professional' } }" ^
"  'degrade' { $body = @{ title='轻薄商务笔记本'; category='电脑办公'; sellingPoints=@('13代酷睿','16GB 内存','高色域屏'); tone='professional' } }" ^
"  default { throw 'Only success / invalid / degrade are supported' }" ^
"};" ^
"if ($mode -eq 'degrade') { Write-Host '[INFO] Stop ai-services first, or point gulimall.ai.base-url to an unreachable address.'; }" ^
"Write-Host ('[INFO] POST ' + $url);" ^
"$json = $body | ConvertTo-Json -Depth 6;" ^
"try {" ^
"  $response = Invoke-RestMethod -Method Post -Uri $url -ContentType 'application/json' -Body $json;" ^
"  $response | ConvertTo-Json -Depth 10" ^
"} catch {" ^
"  if ($_.Exception.Response) {" ^
"    $stream = $_.Exception.Response.GetResponseStream();" ^
"    $reader = New-Object System.IO.StreamReader($stream);" ^
"    $reader.ReadToEnd()" ^
"  } else {" ^
"    throw" ^
"  }" ^
"}"
exit /b %errorlevel%

:help
echo Usage: scripts\check-product-copy-api.bat [success^|invalid^|degrade] [apiUrl]
echo Example: scripts\check-product-copy-api.bat success
echo Example: scripts\check-product-copy-api.bat invalid http://127.0.0.1:10000/product/ai/product-copy/generate
exit /b 0

