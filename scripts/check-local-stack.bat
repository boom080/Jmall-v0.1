@echo off
setlocal

echo ==== Toolchains ====
where java
java -version
where mvn
mvn -version
where node
node -v
where npm
npm -v
where python
python --version
where go
go version

echo.
echo ==== Expected Ports ====
for %%P in (3306 5432 6379 8000 9000 10301 18080 19090 5174 5175) do (
  powershell -NoProfile -Command ^
    "$c = Get-NetTCPConnection -LocalPort %%P -State Listen -ErrorAction SilentlyContinue; if ($c) { Write-Host 'LISTEN %%P' } else { Write-Host 'MISS   %%P' }"
)

echo.
echo ==== Quick HTTP Checks ====
powershell -NoProfile -Command ^
  "try { (Invoke-WebRequest -UseBasicParsing http://127.0.0.1:18080/health -TimeoutSec 3).StatusCode } catch { $_.Exception.Message }"
powershell -NoProfile -Command ^
  "try { (Invoke-WebRequest -UseBasicParsing http://127.0.0.1:19090/health -TimeoutSec 3).StatusCode } catch { $_.Exception.Message }"

echo.
echo Done.

