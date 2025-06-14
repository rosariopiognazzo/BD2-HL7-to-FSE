# HL7 Framework

Un framework completo per la conversione di dati sanitari dal formato HL7 al formato JSON, con salvataggio su MongoDB e interfaccia web React.

## 🎯 Caratteristiche Principali

- **Parsing HL7**: Supporta messaggi MDM, OUL e ORU secondo le specifiche HL7 v2.x
- **Conversione JSON**: Trasforma i dati HL7 in strutture JSON ben organizzate
- **Database MongoDB**: Salvataggio automatico in collections dedicate
- **Interfaccia Web**: Frontend React moderno e intuitivo
- **API REST**: Backend Flask con endpoint completi

## 📋 Tipi di Messaggio Supportati

### 1. MDM (Medical Document Management)
- **Scopo**: Gestione documenti medici e referti
- **Struttura**: `MDM^T01^MDM_T01`
- **Collection**: `mdm_documents`

### 2. OUL (Unsolicited Laboratory Observation)  
- **Scopo**: Risultati di laboratorio
- **Struttura**: `OUL^R22`
- **Collection**: `oul_lab_results`

### 3. ORU (Unsolicited Observation Result)
- **Scopo**: Dati di monitoraggio paziente da dispositivi medici
- **Struttura**: `ORU^R01^ORU_R01`
- **Collection**: `oru_patient_monitoring`

## 🏗️ Architettura del Sistema

```
HL7 Framework/
├── backend/                 # API Flask
│   ├── app.py              # Server principale
│   ├── hl7_parser.py       # Parser HL7
│   ├── mongodb_manager.py  # Gestione database
│   └── requirements.txt    # Dipendenze Python
├── frontend/               # Interfaccia React
│   ├── src/
│   │   ├── components/     # Componenti React
│   │   ├── App.js         # Componente principale
│   │   └── index.js       # Entry point
│   └── package.json       # Dipendenze Node.js
└── dati*.txt              # File di esempio HL7
```

## 🚀 Installazione e Avvio

### Prerequisiti
- Python 3.8+
- Node.js 16+
- Accesso a MongoDB (già configurato)

### Backend (Flask)

1. **Installazione dipendenze**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Avvio del server**:
```bash
python app.py
```
Il backend sarà disponibile su `http://localhost:5000`

### Frontend (React)

1. **Installazione dipendenze**:
```bash
cd frontend
npm install
```

2. **Avvio dell'interfaccia**:
```bash
npm start
```
Il frontend sarà disponibile su `http://localhost:3000`

## 📚 Utilizzo del Framework

### 1. Caricamento File HL7
- Accedi alla sezione "📤 Carica File HL7"
- Trascina o seleziona un file `.txt` contenente dati HL7
- Il sistema processerà automaticamente il file e lo salverà nel database

### 2. Visualizzazione Documenti
- Vai alla sezione "📋 Visualizza Documenti"
- Seleziona il tipo di messaggio (MDM, OUL, ORU)
- Esplora i documenti salvati e visualizza i dettagli JSON

### 3. Ricerca Documenti
- Utilizza la sezione "🔍 Ricerca" 
- Cerca per ID paziente, tipo documento, nome test, ecc.
- I risultati saranno evidenziati secondo i criteri di ricerca

### 4. Statistiche Database
- Consulta la sezione "📊 Statistiche"
- Visualizza il numero di documenti per tipo
- Monitora lo stato delle collections MongoDB

## 🔧 API Endpoints

### Gestione File
- `POST /api/upload` - Carica e processa file HL7
- `GET /api/health` - Stato dell'API

### Gestione Documenti
- `GET /api/documents/{type}` - Recupera documenti per tipo
- `DELETE /api/documents/{type}/{id}` - Elimina documento specifico
- `POST /api/search/{type}` - Cerca documenti con criteri

### Statistiche
- `GET /api/stats` - Statistiche database

## 🗄️ Struttura Database MongoDB

### Database: `DATABASE1`

**Collection: `mdm_documents`**
```json
{
  "message_metadata": { ... },
  "event_information": { ... },
  "patient_identification": { ... },
  "patient_visit": { ... },
  "document_header": { ... },
  "_inserted_at": "2025-06-14T..."
}
```

**Collection: `oul_lab_results`**
```json
{
  "message_metadata": { ... },
  "patient_identification": { ... },
  "specimens": [
    {
      "specimen_id": "...",
      "observation_requests": [
        {
          "observations": [ ... ]
        }
      ]
    }
  ],
  "_inserted_at": "2025-06-14T..."
}
```

**Collection: `oru_patient_monitoring`**
```json
{
  "message_metadata": { ... },
  "patient_identification": { ... },
  "patient_visit": { ... },
  "observation_report": [
    {
      "observations": [ ... ]
    }
  ],
  "_inserted_at": "2025-06-14T..."
}
```

## 📝 Esempi di File HL7

Il framework include file di esempio:
- `datiORB1.txt` - Messaggio MDM^T01
- `datiORB2.txt` - Messaggio OUL^R22  
- `datiORB3_DOM.txt` - Messaggio ORU^R01

## 🎓 Note Tecniche

### Parsing HL7
- I delimitatori seguono lo standard HL7: `|` (field), `^` (component), `&` (subcomponent), `~` (repetition)
- Il parsing è basato sulla posizione dei campi secondo le specifiche HL7 v2.x
- Gestione automatica di campi vuoti e strutture opzionali

### Conversione JSON
- Strutture JSON semanticamente meaningful
- Nomi dei campi basati sulla terminologia HL7 standard
- Preservazione della gerarchia dei dati originali

### Database
- Ogni documento include timestamp di inserimento
- ID MongoDB automatici per l'identificazione univoca
- Indicizzazione automatica per performance ottimali

## 🐛 Troubleshooting

### Problemi Comuni

1. **Errore di connessione MongoDB**
   - Verifica la stringa di connessione
   - Controlla la connettività di rete

2. **File HL7 non riconosciuto**
   - Verifica che il file sia in formato testo
   - Controlla che contenga segmenti HL7 validi

3. **Errori di parsing**
   - Verifica che il tipo di messaggio sia supportato (MDM/OUL/ORU)
   - Controlla la struttura del messaggio HL7

## 👥 Progetto

Questo framework è stato sviluppato come progetto per il corso di Basi di Dati 2, con focus su:
- Integrazione di sistemi eterogenei
- Gestione di dati sanitari strutturati
- Architetture web moderne
- Database NoSQL per dati semi-strutturati
