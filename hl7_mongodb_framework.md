# Framework HL7 to MongoDB - Specifica Tecnica

## 1. Architettura del Sistema

### 1.1 Componenti Principali
- **Parser HL7**: Modulo per l'analisi e parsing dei file HL7 v2.x
- **Data Transformer**: Convertitore da struttura HL7 a documento MongoDB
- **Database Manager**: Gestione delle operazioni CRUD su MongoDB
- **Web Interface**: Interfaccia web semplice per upload e visualizzazione

### 1.2 Stack Tecnologico Suggerito
- **Backend**: Node.js con Express.js
- **Database**: MongoDB con driver nativo o Mongoose
- **Frontend**: HTML/CSS/JavaScript vanilla o framework leggero
- **Parser HL7**: Libreria dedicata (es. node-hl7-parser) o implementazione custom

## 2. Logica di Parsing HL7

### 2.1 Struttura di Input
I file HL7 v2.x sono testi ASCII con delimitatori specifici:
- **Separatore segmenti**: Carriage Return (0x0D)
- **Separatore campi**: Pipe (|)
- **Separatore componenti**: Caret (^)
- **Separatore ripetizioni**: Tilde (~)
- **Separatore escape**: Backslash (\)

### 2.2 Algoritmo di Parsing

```javascript
function parseHL7Message(hl7Text) {
    const segments = hl7Text.split('\r');
    const message = {
        messageHeader: null,
        segments: [],
        rawMessage: hl7Text,
        parsedAt: new Date()
    };
    
    segments.forEach(segment => {
        if (segment.trim()) {
            const parsedSegment = parseSegment(segment);
            if (parsedSegment.type === 'MSH') {
                message.messageHeader = parsedSegment;
            }
            message.segments.push(parsedSegment);
        }
    });
    
    return message;
}

function parseSegment(segmentText) {
    const fields = segmentText.split('|');
    const segmentType = fields[0];
    
    return {
        type: segmentType,
        fields: fields.slice(1).map((field, index) => ({
            position: index + 1,
            value: field,
            components: field.includes('^') ? field.split('^') : null,
            repetitions: field.includes('~') ? field.split('~') : null
        })),
        raw: segmentText
    };
}
```

## 3. Strategia di Trasformazione per MongoDB

### 3.1 Schema Documento MongoDB

```javascript
{
    _id: ObjectId,
    messageId: String,           // Da MSH-10 (Control ID)
    messageType: String,         // Da MSH-9 (Message Type)
    timestamp: Date,             // Da MSH-7 (Date/Time)
    sendingApplication: String,  // Da MSH-3
    receivingApplication: String, // Da MSH-5
    
    patient: {
        id: String,              // Da PID-3
        name: {
            family: String,      // Da PID-5 componente 1
            given: String,       // Da PID-5 componente 2
            full: String         // Nome completo
        },
        birthDate: Date,         // Da PID-7
        gender: String,          // Da PID-8
        address: {
            street: String,      // Da PID-11
            city: String,
            postalCode: String,
            country: String
        },
        identifiers: [           // Da PID-3 (ripetizioni)
            {
                value: String,
                type: String,
                system: String
            }
        ]
    },
    
    visit: {                     // Da PV1
        class: String,
        location: String,
        department: String
    },
    
    orders: [                    // Da OBR/ORC
        {
            orderId: String,
            orderNumber: String,
            procedure: {
                code: String,
                description: String,
                system: String
            },
            orderDateTime: Date,
            status: String,
            observations: [      // Da OBX
                {
                    valueType: String,
                    identifier: {
                        code: String,
                        description: String
                    },
                    value: String,
                    units: String,
                    referenceRange: String,
                    abnormalFlags: String,
                    observationDateTime: Date
                }
            ]
        }
    ],
    
    documents: [                 // Da TXA (se presente)
        {
            documentType: String,
            creationDate: Date,
            author: String,
            status: String
        }
    ],
    
    specimens: [                 // Da SPM (se presente)
        {
            specimenId: String,
            type: String,
            collectionDateTime: Date
        }
    ],
    
    rawSegments: [              // Backup dei segmenti originali
        {
            type: String,
            position: Number,
            content: String,
            fields: Array
        }
    ],
    
    metadata: {
        originalFileName: String,
        uploadDate: Date,
        processingDate: Date,
        version: String,
        errors: Array,
        warnings: Array
    }
}
```

### 3.2 Logica di Mappatura

```javascript
function transformHL7ToMongoDB(parsedHL7) {
    const document = {
        messageId: extractMessageId(parsedHL7),
        messageType: extractMessageType(parsedHL7),
        timestamp: extractTimestamp(parsedHL7),
        sendingApplication: extractSendingApp(parsedHL7),
        receivingApplication: extractReceivingApp(parsedHL7),
        patient: extractPatientInfo(parsedHL7),
        visit: extractVisitInfo(parsedHL7),
        orders: extractOrders(parsedHL7),
        documents: extractDocuments(parsedHL7),
        specimens: extractSpecimens(parsedHL7),
        rawSegments: preserveRawSegments(parsedHL7),
        metadata: {
            processingDate: new Date(),
            version: "1.0",
            errors: [],
            warnings: []
        }
    };
    
    return validateAndCleanDocument(document);
}

function extractPatientInfo(parsedHL7) {
    const pidSegment = findSegmentByType(parsedHL7, 'PID');
    if (!pidSegment) return null;
    
    const nameField = pidSegment.fields[4]; // PID-5
    const nameComponents = nameField?.components || [];
    
    return {
        id: extractPatientId(pidSegment.fields[2]), // PID-3
        name: {
            family: nameComponents[0] || '',
            given: nameComponents[1] || '',
            full: `${nameComponents[1]} ${nameComponents[0]}`.trim()
        },
        birthDate: parseHL7Date(pidSegment.fields[6]?.value), // PID-7
        gender: pidSegment.fields[7]?.value, // PID-8
        address: extractAddress(pidSegment.fields[10]), // PID-11
        identifiers: extractIdentifiers(pidSegment.fields[2]) // PID-3
    };
}
```

## 4. Gestione Database MongoDB

### 4.1 Collezioni
- **messages**: Documenti HL7 trasformati
- **upload_logs**: Log degli upload e processing
- **metadata**: Metadati di sistema e configurazioni

### 4.2 Operazioni CRUD

```javascript
class HL7DatabaseManager {
    constructor(mongoUrl, dbName) {
        this.mongoUrl = mongoUrl;
        this.dbName = dbName;
        this.db = null;
    }
    
    async insertMessage(document) {
        try {
            // Verifica duplicati basata su messageId
            const existing = await this.db.collection('messages')
                .findOne({ messageId: document.messageId });
            
            if (existing) {
                throw new Error(`Message with ID ${document.messageId} already exists`);
            }
            
            const result = await this.db.collection('messages').insertOne(document);
            return result.insertedId;
        } catch (error) {
            throw new Error(`Insert failed: ${error.message}`);
        }
    }
    
    async searchMessages(criteria) {
        const query = buildSearchQuery(criteria);
        return await this.db.collection('messages')
            .find(query)
            .sort({ timestamp: -1 })
            .toArray();
    }
    
    async updateMessage(messageId, updates) {
        return await this.db.collection('messages')
            .updateOne({ messageId }, { $set: updates });
    }
    
    async deleteMessage(messageId) {
        return await this.db.collection('messages')
            .deleteOne({ messageId });
    }
}
```

## 5. Web Application

### 5.1 Funzionalità Core
- **Upload File**: Drag & drop o selezione file HL7
- **Lista Messaggi**: Visualizzazione tabulare con paginazione
- **Dettaglio Messaggio**: Vista gerarchica del documento
- **Ricerca**: Filtri per paziente, data, tipo messaggio
- **Operazioni**: Cancellazione, esportazione

### 5.2 API Endpoints

```javascript
// Upload e processing
POST /api/upload - Upload file HL7
GET /api/messages - Lista messaggi con filtri
GET /api/messages/:id - Dettaglio messaggio
PUT /api/messages/:id - Aggiorna messaggio
DELETE /api/messages/:id - Cancella messaggio

// Ricerca e analytics
GET /api/search - Ricerca avanzata
GET /api/stats - Statistiche generali
GET /api/export/:id - Esporta messaggio (JSON/HL7)
```

## 6. Gestione Errori e Validazione

### 6.1 Validazione Input
- Verifica formato HL7 valido
- Controllo presenza segmenti obbligatori (MSH)
- Validazione date e formati numerici
- Sanificazione input utente

### 6.2 Error Handling
```javascript
class ValidationError extends Error {
    constructor(message, field, value) {
        super(message);
        this.field = field;
        this.value = value;
        this.type = 'VALIDATION_ERROR';
    }
}

function validateHL7Document(document) {
    const errors = [];
    const warnings = [];
    
    // Validazioni obbligatorie
    if (!document.messageId) {
        errors.push(new ValidationError('Missing message ID', 'messageId', null));
    }
    
    if (!document.patient?.id) {
        errors.push(new ValidationError('Missing patient ID', 'patient.id', null));
    }
    
    // Validazioni opzionali (warnings)
    if (!document.patient?.name?.family) {
        warnings.push('Missing patient family name');
    }
    
    return { errors, warnings, isValid: errors.length === 0 };
}
```

## 7. Considerazioni Implementative

### 7.1 Performance
- Implementare indexing su campi frequentemente ricercati (messageId, patient.id, timestamp)
- Paginazione per liste grandi
- Caching per query frequenti

### 7.2 Sicurezza
- Validazione e sanificazione input
- Controllo dimensione file upload
- Rate limiting per API

### 7.3 Scalabilità
- Struttura modulare per estensioni future
- Configurazione flessibile per nuovi tipi di segmenti
- Supporto per batch processing

Questo framework mantiene la semplicità richiesta mentre preserva tutte le informazioni critiche dei messaggi HL7, fornendo una base solida per operazioni CRUD efficaci in ambiente NoSQL.