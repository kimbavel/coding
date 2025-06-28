@echo off
REM Backend (FastAPI) and Frontend (Vue) development servers run simultaneously

REM Start Backend (port 8080)
cd backend
start "Backend" cmd /c "uvicorn main:app --host 0.0.0.0 --port 8080 --reload"
cd ..

REM Start Frontend (port 3000)
cd frontend
start "Frontend" cmd /c "npm run dev"
cd ..

REM Wait for user to press any key to stop servers
echo Press any key to stop both servers...
pause

REM Kill backend and frontend processes
REM (User may need to close the spawned terminals manually if not handled automatically)
