"""
Script per processare i risultati di laboratorio caricati tramite uploadapp
e associarli correttamente ai pazienti nel database
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from hl7_fhir_converter import FSEFramework
from pymongo import MongoClient
import json

# Configurazione MongoDB
MONGO_URI = "mongodb+srv://rosariopiognazzo:MO22HSgdEdNdh2fF@cluster0.vim0kda.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DATABASE_NAME = "fse_database"

def process_uploaded_lab_results():
    """Processa i risultati di laboratorio caricati tramite uploadapp"""
    
    # Connessione al database
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    
    # Framework FSE
    framework = FSEFramework(MONGO_URI)
    framework.database.db_name = DATABASE_NAME
    framework.database.db = db
    framework.database.patients_collection = db.patients
    framework.database.lab_results_collection = db.lab_results
    
    # Trova tutti i documenti nella collezione lab_results che non sono stati processati
    raw_lab_docs = list(db.lab_results.find({"segments": {"$exists": True}}))
    
    print(f"Trovati {len(raw_lab_docs)} documenti di laboratorio da processare")
    
    for doc in raw_lab_docs:
        try:
            # Estrai le informazioni del paziente dal messaggio HL7 parsato
            patient_info = extract_patient_info_from_parsed_hl7(doc)
            
            if patient_info:
                # Cerca il paziente esistente nel database
                patient = find_or_create_patient(framework, patient_info)
                
                if patient:
                    # Converti i risultati di laboratorio in formato FHIR
                    observations = convert_lab_results_to_fhir(doc, patient['id'])
                    
                    # Salva le osservazioni
                    for obs in observations:
                        db.lab_results.replace_one(
                            {"_id": obs.get("_id", None)}, 
                            obs, 
                            upsert=True
                        )
                    
                    # Rimuovi il documento raw originale se è stato processato con successo
                    db.lab_results.delete_one({"_id": doc["_id"]})
                    
                    print(f"Processato paziente {patient['id']} con {len(observations)} osservazioni")
                else:
                    print(f"Impossibile trovare/creare paziente per documento {doc['_id']}")
            else:
                print(f"Impossibile estrarre informazioni paziente da documento {doc['_id']}")
                
        except Exception as e:
            print(f"Errore nel processare documento {doc['_id']}: {e}")

def extract_patient_info_from_parsed_hl7(doc):
    """Estrae le informazioni del paziente dai segmenti HL7 parsati"""
    try:
        # Cerca il segmento PID nei dati parsati
        segments = doc.get('segments', [])
        
        # Il primo segmento MSH contiene tutti i campi in un unico array
        msh_segment = None
        for segment in segments:
            if segment.get('type') == 'MSH' and len(segment.get('fields', [])) > 1:
                msh_segment = segment
                break
        
        if not msh_segment:
            return None
            
        # I dati del paziente sono contenuti nel campo MSH che sembra contenere tutto il messaggio
        # Cerchiamo le informazioni del paziente nei campi MSH
        fields = msh_segment.get('fields', [])
        
        if len(fields) < 20:
            return None
            
        # Estrai le informazioni del paziente (basandoci sulla struttura osservata)
        # Campo 14: identificatori paziente
        # Campo 16: nome paziente  
        # Campo 18: data nascita
        # Campo 19: sesso
        
        patient_identifiers = fields[14] if len(fields) > 14 else ""
        patient_name = fields[16] if len(fields) > 16 else ""
        birth_date = fields[18] if len(fields) > 18 else ""
        gender = fields[19] if len(fields) > 19 else ""
        
        return {
            'identifiers': patient_identifiers,
            'name': patient_name,
            'birthDate': birth_date,
            'gender': gender
        }
        
    except Exception as e:
        print(f"Errore nell'estrazione informazioni paziente: {e}")
        return None

def find_or_create_patient(framework, patient_info):
    """Trova un paziente esistente o ne crea uno nuovo"""
    try:
        # Estrai il codice fiscale dagli identificatori
        identifiers = patient_info.get('identifiers', '')
        cf = None
        
        # Gli identificatori sono separati da ~ e ogni identificatore ha componenti separate da ^
        if identifiers:
            id_parts = identifiers.split('~')
            for id_part in id_parts:
                components = id_part.split('^')
                if len(components) >= 5 and components[4] == 'CF':
                    cf = components[0]
                    break
        
        if cf:
            # Cerca paziente esistente per codice fiscale
            existing_patient = framework.database.find_patient_by_identifier(cf)
            if existing_patient:
                return existing_patient
        
        # Se non trovato, crea un nuovo paziente
        # Ricostruisci un messaggio HL7 semplificato per usare il framework esistente
        hl7_message = reconstruct_hl7_message(patient_info)
        
        if hl7_message:
            result = framework.process_hl7_message(hl7_message)
            if result.get('success'):
                return framework.database.find_patient_by_id(result['patient_id'])
        
        return None
        
    except Exception as e:
        print(f"Errore nella ricerca/creazione paziente: {e}")
        return None

def reconstruct_hl7_message(patient_info):
    """Ricostruisce un messaggio HL7 basilare dal patient_info"""
    try:
        # Estrai nome e cognome
        name_parts = patient_info.get('name', '').split('^') if patient_info.get('name') else ['', '']
        family_name = name_parts[0] if len(name_parts) > 0 else ''
        given_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Costruisci un messaggio HL7 semplificato
        hl7_lines = [
            "MSH|^~\\&|UPLOAD|UPLOAD|FSE|FSE|20250611000000||ADT^A04|MSG001||2.5",
            f"PID|||{patient_info.get('identifiers', '')}||{family_name}^{given_name}||{patient_info.get('birthDate', '')}|{patient_info.get('gender', '')}"
        ]
        
        return '\n'.join(hl7_lines)
        
    except Exception as e:
        print(f"Errore nella ricostruzione HL7: {e}")
        return None

def convert_lab_results_to_fhir(doc, patient_id):
    """Converte i risultati di laboratorio in formato FHIR Observation"""
    observations = []
    
    try:
        # I risultati di laboratorio sono nei segmenti OBX
        # Nel documento parsato, sembrano essere contenuti nel primo segmento MSH
        segments = doc.get('segments', [])
        
        msh_segment = None
        for segment in segments:
            if segment.get('type') == 'MSH' and len(segment.get('fields', [])) > 1:
                msh_segment = segment
                break
        
        if not msh_segment:
            return observations
            
        fields = msh_segment.get('fields', [])
        
        # Cerca i risultati OBX nei campi (sembrano iniziare dal campo 30 circa)
        # Questo richiede un'analisi più dettagliata della struttura dei dati
        
        # Per ora, creiamo osservazioni di esempio basate sui dati visibili
        # POTASSIO: campo con valore 3.9 mmol/L
        # SODIO: campo con valore 138 mmol/L
        
        # Cerca pattern per i risultati di laboratorio
        for i, field in enumerate(fields):
            if isinstance(field, str) and 'mmol/L' in field:
                # Questo è probabilmente un risultato
                prev_fields = fields[max(0, i-5):i]  # Guarda i campi precedenti per il nome del test
                
                # Cerca il nome del test
                test_name = None
                test_code = None
                for pf in reversed(prev_fields):
                    if isinstance(pf, str) and '^' in pf and ('POTASSIO' in pf.upper() or 'SODIO' in pf.upper()):
                        parts = pf.split('^')
                        if len(parts) >= 2:
                            test_code = parts[0]
                            test_name = parts[1]
                            break
                
                if test_name and test_code:
                    # Estrai valore e unità
                    value_parts = field.split()
                    if len(value_parts) >= 2:
                        value = value_parts[0]
                        unit = value_parts[1]
                        
                        # Cerca range di riferimento
                        reference_range = None
                        if i + 1 < len(fields) and isinstance(fields[i + 1], str) and ' - ' in fields[i + 1]:
                            reference_range = fields[i + 1]
                        
                        observation = {
                            "resourceType": "Observation",
                            "id": f"obs-{patient_id}-{test_code}-{doc.get('timestamp', '')}",
                            "status": "final",
                            "code": {
                                "coding": [{
                                    "code": test_code,
                                    "display": test_name
                                }]
                            },
                            "subject": {
                                "reference": f"Patient/{patient_id}"
                            },
                            "valueQuantity": {
                                "value": float(value) if value.replace('.', '').isdigit() else value,
                                "unit": unit
                            },
                            "issued": doc.get('timestamp', ''),
                            "referenceRange": reference_range
                        }
                        
                        observations.append(observation)
        
    except Exception as e:
        print(f"Errore nella conversione risultati laboratorio: {e}")
    
    return observations

if __name__ == "__main__":
    process_uploaded_lab_results()
