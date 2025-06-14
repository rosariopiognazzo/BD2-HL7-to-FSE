# 🧪 Guida al Testing del Framework HL7

## Test Rapido del Parser

Per verificare che il parser HL7 funzioni correttamente con i file di esempio:

```bash
python quick_test.py
```

Questo comando testera il parsing dei tre file di esempio:
- `datiORB1.txt` (MDM - Medical Document Management)
- `datiORB2.txt` (OUL - Laboratory Results) 
- `datiORB3_DOM.txt` (ORU - Patient Monitoring)

## Test Completo del Framework

Per testare tutto il framework incluso MongoDB:

```bash
python test_framework.py
```

## Avvio Manuale del Framework

### 1. Backend (Flask)
```bash
cd backend
pip install -r requirements.txt
python app.py
```
Il server sarà disponibile su: http://localhost:5000

### 2. Frontend (React)
```bash
cd frontend
npm install
npm start
```
L'interfaccia web sarà disponibile su: http://localhost:3000

## Avvio Automatico

### Windows
```bash
start.bat
```

### Linux/Mac
```bash
./start.sh
```

## Test degli Endpoint API

Con il backend in esecuzione, puoi testare gli endpoint API:

### 1. Health Check
```bash
curl http://localhost:5000/api/health
```

### 2. Upload File HL7
```bash
curl -X POST -F "file=@datiORB1.txt" http://localhost:5000/api/upload
```

### 3. Visualizza Documenti MDM
```bash
curl http://localhost:5000/api/documents/MDM
```

### 4. Statistiche Database
```bash
curl http://localhost:5000/api/stats
```

## Test dell'Interfaccia Web

1. Vai su http://localhost:3000
2. Usa la sezione "📤 Carica File HL7" per caricare i file di esempio
3. Esplora i documenti caricati nella sezione "📋 Visualizza Documenti"
4. Prova la funzionalità di ricerca nella sezione "🔍 Ricerca"
5. Controlla le statistiche nella sezione "📊 Statistiche"

## File di Esempio Inclusi

- **datiORB1.txt**: Messaggio MDM^T01 - Documento medico con informazioni paziente
- **datiORB2.txt**: Messaggio OUL^R22 - Risultati di laboratorio multipli
- **datiORB3_DOM.txt**: Messaggio ORU^R01 - Dati di monitoraggio paziente

## Risoluzione Problemi

### Errore MongoDB
Se vedi errori di connessione MongoDB, verifica:
- Connessione Internet attiva
- Credenziali MongoDB corrette nel codice

### Errore Dipendenze Python
```bash
cd backend
pip install flask flask-cors pymongo python-dotenv
```

### Errore Dipendenze Node.js
```bash
cd frontend
npm install react react-dom axios react-router-dom
```

## Struttura del Database

Il framework crea automaticamente:
- **Database**: `DATABASE1`
- **Collections**:
  - `mdm_documents` (per messaggi MDM)
  - `oul_lab_results` (per messaggi OUL)
  - `oru_patient_monitoring` (per messaggi ORU)
