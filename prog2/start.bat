@echo off
echo 🚀 Avvio HL7 Framework...

REM Controlla se Python è installato
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python non trovato. Installa Python 3.8+ e riprova.
    pause
    exit /b 1
)

REM Controlla se Node.js è installato
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js non trovato. Installa Node.js 16+ e riprova.
    pause
    exit /b 1
)

echo 📦 Installazione dipendenze backend...
cd backend
pip install -r requirements.txt

echo 🖥️ Avvio backend Flask...
start "HL7 Backend" cmd /k "python app.py"

cd ..\frontend

echo 📦 Installazione dipendenze frontend...
call npm install

echo 🌐 Avvio frontend React...
start "HL7 Frontend" cmd /k "npm start"

echo ✅ Framework avviato!
echo 📱 Frontend: http://localhost:3000
echo 🔧 Backend: http://localhost:5000
echo.
echo 💡 Chiudi le finestre del terminale per terminare il framework.
pause
