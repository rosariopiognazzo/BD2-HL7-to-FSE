#!/bin/bash

echo "🚀 Avvio HL7 Framework..."

# Controlla se Python è installato
if ! command -v python &> /dev/null; then
    echo "❌ Python non trovato. Installa Python 3.8+ e riprova."
    exit 1
fi

# Controlla se Node.js è installato
if ! command -v node &> /dev/null; then
    echo "❌ Node.js non trovato. Installa Node.js 16+ e riprova."
    exit 1
fi

echo "📦 Installazione dipendenze backend..."
cd backend
pip install -r requirements.txt

echo "🖥️ Avvio backend Flask..."
python app.py &
BACKEND_PID=$!

cd ../frontend

echo "📦 Installazione dipendenze frontend..."
npm install

echo "🌐 Avvio frontend React..."
npm start &
FRONTEND_PID=$!

echo "✅ Framework avviato!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend: http://localhost:5000"
echo ""
echo "💡 Premi Ctrl+C per terminare..."

# Attendi l'interruzione
trap "echo '🛑 Arresto framework...'; kill $BACKEND_PID $FRONTEND_PID; exit 0" INT
wait
