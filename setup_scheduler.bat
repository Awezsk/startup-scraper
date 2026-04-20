@echo off
:: ============================================================
::  India Startup & Grants Digest — Windows Task Scheduler Setup
::  Run as Administrator (right-click -> Run as administrator)
:: ============================================================

SET PYTHON=C:\Users\awez7\AppData\Local\Programs\Python\Python312\python.exe
SET DIR=C:\Users\awez7\OneDrive\Desktop\Scraper incubin

echo.
echo  ====================================================
echo   India Startup Digest - Task Scheduler Setup
echo  ====================================================
echo.

:: Delete old tasks if they exist (ignore errors)
schtasks /delete /tn "IndiaDigest_Scrape"     /f >nul 2>&1
schtasks /delete /tn "IndiaDigest_Email"      /f >nul 2>&1
schtasks /delete /tn "IndiaDigest_Dashboard"  /f >nul 2>&1

:: ── Task 1: Scrape at 9:00 AM daily ──────────────────────────────
schtasks /create ^
  /tn "IndiaDigest_Scrape" ^
  /tr "\"%PYTHON%\" \"%DIR%\scraper.py\"" ^
  /sc DAILY ^
  /st 09:00 ^
  /ru "%USERNAME%" ^
  /rl HIGHEST ^
  /f

echo [1/2] Scrape task created: 9:00 AM daily

:: ── Task 2: Send Email at 10:00 AM daily ─────────────────────────
schtasks /create ^
  /tn "IndiaDigest_Email" ^
  /tr "\"%PYTHON%\" \"%DIR%\emailer.py\"" ^
  /sc DAILY ^
  /st 10:00 ^
  /ru "%USERNAME%" ^
  /rl HIGHEST ^
  /f

echo [2/2] Email task created:  10:00 AM daily

echo.
echo  ====================================================
echo   DONE! Both tasks are registered.
echo.
echo   IndiaDigest_Scrape   ->  9:00 AM  (scrape + dashboard)
echo   IndiaDigest_Email    -> 10:00 AM  (send Gmail digest)
echo.
echo   View/edit in: Task Scheduler -> Task Scheduler Library
echo  ====================================================
echo.
pause
