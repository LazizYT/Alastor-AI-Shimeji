@echo off
echo Stopping Alastor...

taskkill /F /T /IM Alastor.exe >nul 2>&1

powershell -NoProfile -ExecutionPolicy Bypass -Command "$procs = Get-CimInstance Win32_Process | Where-Object { ($_.Name -eq 'Alastor.exe') -or ($_.Name -eq 'pythonw.exe' -and $_.CommandLine -like '*PinkChan*') }; foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1

echo.
echo ===================================
echo [OK] Alastor stopped successfully!
echo ===================================
ping 127.0.0.1 -n 2 >nul
