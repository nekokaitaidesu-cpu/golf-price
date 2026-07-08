@echo off
rem honmei sniper: single scan (register in Task Scheduler, every 15-30 min)
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
python notify_honmei.py >> notify.log 2>&1
