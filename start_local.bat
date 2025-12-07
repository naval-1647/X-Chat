@echo off
echo 🚀 Starting Xchat Local Development Environment
echo.
echo Starting Backend API server...
start "Xchat Backend" cmd /k "python simple_app.py"
timeout /t 3 /nobreak >nul

echo Starting Frontend server...
start "Xchat Frontend" cmd /k "python start_frontend.py"

echo.
echo ✅ Both servers are starting!
echo 🌐 Frontend: http://localhost:3001
echo 🔧 Backend API: http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo Press any key to exit...
pause >nul