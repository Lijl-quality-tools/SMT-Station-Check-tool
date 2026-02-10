@echo off
echo 正在启动SMT首件核对程序，请勿关闭此窗口……
"%~dp0python_embed\python.exe" -m streamlit run "%~dp0app.py"
pause