**Prompt per LLM:**

**Obiettivo del Progetto:**
Sviluppare un framework software in Python o JavaScript per la conversione di dati sanitari dal formato HL7 al formato JSON, il successivo salvataggio su un database MongoDB e l'implementazione di una semplice interfaccia web React per l'interazione con il sistema.

**Requisiti Fondamentali del Framework:**

1.  **Parsing HL7 e Conversione in JSON:**

    *   Il framework deve essere in grado di leggere e processare file di input contenenti dati in formato HL7.

    *   Deve supportare specificamente tre tipologie di messaggi HL7:
        1.  **MDM (Medical Document Management):** Es. `MDM^T01` (documento medico con informazioni paziente e metadati).
        2.  **OUL (Unsolicited Laboratory Observation):** Es. `OUL^R22` (risultati di laboratorio con analisi multiple).
        3.  **ORU (Unsolicited Observation Result):** Es. `ORU^R01` (dati di monitoraggio paziente, tipicamente da dispositivi medici).

    *   La logica dettagliata per l'estrazione delle informazioni da ciascun tipo di messaggio HL7 e la sua mappatura in una struttura JSON interpretabile è descritta nel documento `HL7_Parsing_Approach.md`. **È cruciale aderire strettamente alle strutture JSON proposte in quel documento per garantire la corretta interpretazione e interrogazione dei dati.**

    *   L'output del processo di conversione deve essere un file o una stringa JSON per ogni messaggio HL7 processato.

2.  **Integrazione con MongoDB:**

    *   I dati JSON generati devono essere salvati in un database MongoDB.

    *   Utilizzare il seguente URI di connessione a MongoDB:`mongodb+srv://rosariopiognazzo:MO22HSgdEdNdh2fF@cluster0.vim0kda.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0`
           *   All'interno dell'istanza MongoDB, creare un nuovo database denominato `<DATABASE1>`
    *   Per ogni tipologia di dati HL7 (MDM, OUL, ORU), creare una collection MongoDB dedicata all'interno del database `<DATABASE1>`. Ad esempio:
        *   `mdm_documents`
        *   `oul_lab_results`
        *   `oru_patient_monitoring`
    *   Salvare i documenti JSON corrispondenti nelle rispettive collections.

3.  **Sviluppo di una Web Application Semplice:**
    *   **Backend:** Realizzare un semplice backend API in Python(utilizzando Flask) o JavaScript che esponga le funzionalità del framework.
    *   **Frontend:** Sviluppare un'interfaccia utente (UI) in React.
    *   **Funzionalità della Web App:**
        1.  **Caricamento File:** Permettere all'utente di caricare file HL7 (.txt) attraverso l'interfaccia. Il backend processerà questi file, li convertirà in JSON e li salverà su MongoDB.
        2.  **Visualizzazione Dati:** Mostrare in modo chiaro i dati salvati nel database MongoDB. L'utente dovrebbe poter navigare o vedere un elenco dei record nelle diverse collection (MDM, OUL, ORU).
        3.  **Interrogazioni di Base al Database:**
            *   **Eliminazione Dati:** Fornire una funzionalità per eliminare record specifici dal database (ad es., tramite un ID univoco del record o un criterio semplice).
            *   **Ricerca per Campi:** Implementare una semplice funzionalità di ricerca che permetta all'utente di cercare record specifici all'interno di una collection basandosi su valori di determinati campi JSON (es. cercare un paziente per codice fiscale nel PID, o un risultato di laboratorio per nome test).

**Principi Guida e Vincoli:**

*   **Semplicità:** L'intero framework (codice Python o JavaScript, backend API, frontend React) deve essere mantenuto il più semplice possibile. L'obiettivo primario è la funzionalità e la comprensibilità del codice, non la robustezza estrema, la gestione complessa degli errori o l'ottimizzazione delle performance a tutti i costi.
*   **Modularità:** Strutturare il codice in moduli logici (es. un modulo per il parsing HL7, uno per l'interazione con MongoDB, uno per le API).

**Focus Specifico:**
Assicurati che la conversione da HL7 a JSON segua fedelmente la logica e le strutture definite in `HL7_Parsing_Approach.md`. L'etichettatura chiara e intuitiva dei campi nel JSON risultante è fondamentale.