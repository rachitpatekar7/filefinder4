@echo off
setlocal

rem <-- set your MySQL bin folder here (no trailing backslash)
set "BINPATH=C:\Program Files\MySQL\MySQL Server 8.0\bin"

rem Check folder exists
if not exist "%BINPATH%\mysqld.exe" (
  echo ERROR: mysqld.exe not found in "%BINPATH%"
  echo Please verify the BINPATH at the top of this script.
  pause
  exit /b 1
)

echo ------------------------------------------------------------
echo Stopping MySQL service (MySQL80)...
net stop MySQL80
echo.

echo Starting MySQL in safe mode (skip-grant-tables) in a new window...
start "MySQL Safe Mode" cmd /k ""%BINPATH%\mysqld.exe" --skip-grant-tables --skip-networking"
echo Waiting 6 seconds for server to start...
timeout /t 6 /nobreak >nul
echo.

echo Opening MySQL client in a new window. Run the ALTER USER command there.
start "MySQL Console" cmd /k ""%BINPATH%\mysql.exe" -u root"
echo.
echo When the MySQL console opens, execute these commands (copy-paste):
echo -------------------------------------------------------
echo FLUSH PRIVILEGES;
echo ALTER USER 'root'@'localhost' IDENTIFIED BY 'MyNewPassword@123';
echo FLUSH PRIVILEGES;
echo -------------------------------------------------------
echo After you run the commands, close the two new windows (Safe Mode + Console),
echo then return here and press any key to restart the service.
pause

echo Starting MySQL service (MySQL80) normally...
net start MySQL80
echo Done. Try logging into MySQL Workbench with root and your new password.
pause
endlocal