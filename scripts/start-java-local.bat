@echo off
setlocal EnableDelayedExpansion

if "%~1"=="" (
  echo Usage: %~nx0 member ^| order ^| product
  exit /b 1
)

set "MODULE=%~1"
set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%"

if exist ".env.local" (
  echo Loading environment from .env.local...
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

if /i "%MODULE%"=="member" (
  set "POM_PATH=gulimall-member\pom.xml"
) else if /i "%MODULE%"=="order" (
  set "POM_PATH=gulimall-order\pom.xml"
) else if /i "%MODULE%"=="product" (
  set "POM_PATH=gulimall-product\pom.xml"
) else (
  echo Unsupported module: %MODULE%
  echo Usage: %~nx0 member ^| order ^| product
  exit /b 1
)

echo Starting jrunmall-%MODULE% with local profile...
set "COMMON_JAR=.m2\repository\com\shf\jrunmall\jrunmall-common\0.0.1-SNAPSHOT\jrunmall-common-0.0.1-SNAPSHOT.jar"
set "AI_ADAPTER_JAR=.m2\repository\com\shf\jrunmall\jrunmall-ai-adapter\0.0.1-SNAPSHOT\jrunmall-ai-adapter-0.0.1-SNAPSHOT.jar"

if not exist "%COMMON_JAR%" (
  echo Installing shared common Maven module...
  call mvn -s .mvn\local-settings.xml -pl ":jrunmall-common" -DskipTests install
  if errorlevel 1 exit /b 1
)

if /i "%MODULE%"=="product" (
  echo Refreshing AI adapter Maven module...
  call mvn -s .mvn\local-settings.xml -pl ":jrunmall-ai-adapter" -DskipTests install
  if errorlevel 1 exit /b 1
)

if not exist "%AI_ADAPTER_JAR%" (
  echo Installing AI adapter Maven module...
  call mvn -s .mvn\local-settings.xml -pl ":jrunmall-ai-adapter" -DskipTests install
  if errorlevel 1 exit /b 1
)

call mvn -s .mvn\local-settings.xml -f "%POM_PATH%" clean org.springframework.boot:spring-boot-maven-plugin:2.7.18:run -Dspring-boot.run.profiles=local -Dspring-boot.run.excludeDevtools=true -Dspring-boot.run.jvmArguments=-Dspring.devtools.restart.enabled=false
