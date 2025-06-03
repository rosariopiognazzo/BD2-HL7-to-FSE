"""
Script di configurazione e test per FSE Framework
Include setup database, test unitari e esempi d'uso
"""

import json
import unittest
from datetime import datetime
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from typing import List, Dict
import uuid

# Import FSE Framework components
try:
    from hl7_fhir_converter import FSEFramework, FHIRConverter, HL7Parser
except ImportError:
    print("FSE Framework non trovato. Impossibile eseguire i test.")
    import sys
    sys.exit(1)

# Configurazione
CONFIG = {
    "mongodb": {
        "connection_string": "mongodb+srv://rosariopiognazzo:MO22HSgdEdNdh2fF@cluster0.vim0kda.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
        "database_name": "fse_test_database",
        "collections": {
            "patients": "patients",
            "lab_results": "lab_results",
            "documents": "documents"
        }
    },
    "fhir": {
        "base_url": "http://hl7.it/fhir/lab-report/",
        "profiles": {
            "patient": "StructureDefinition/patient-it-lab"
        }
    },
    "logging": {
        "level": "INFO",
        "file": "fse_framework.log"
    }
}

def setup_database():
    """Setup iniziale del database MongoDB"""
    try:
        client = MongoClient(CONFIG["mongodb"]["connection_string"], server_api=ServerApi('1'))
        db = client[CONFIG["mongodb"]["database_name"]]
        
        # Crea collezioni se non esistono
        collections = ["patients", "lab_results", "documents", "audit_log"]
        for collection_name in collections:
            if collection_name not in db.list_collection_names():
                db.create_collection(collection_name)
                print(f"Collezione '{collection_name}' creata")
        
        # Crea indici
        patients_collection = db.patients
        patients_collection.create_index([("identifier.value", 1)], unique=True)
        patients_collection.create_index([("id", 1)], unique=True)
        patients_collection.create_index([("birthDate", 1)])
        patients_collection.create_index([("name.family", 1), ("name.given", 1)])
        
        lab_results_collection = db.lab_results
        lab_results_collection.create_index([("subject.reference", 1)])
        lab_results_collection.create_index([("effectiveDateTime", 1)])
        
        print("Database setup completato con successo")
        return True
        
    except Exception as e:
        print(f"Errore nel setup database: {e}")
        return False

class TestFSEFramework(unittest.TestCase):
    """Test suite per FSE Framework"""
    
    @classmethod
    def setUpClass(cls):
        cls.framework = FSEFramework(CONFIG["mongodb"]["connection_string"])
        cls.converter = FHIRConverter()
        cls.parser = HL7Parser()
        # Pulisci le collezioni di test
        db = cls.framework.database.db
        db.patients.delete_many({})
        db.lab_results.delete_many({})
    
    def setUp(self):
        self.sample_hl7 = r"""MSH|^~\&|XXX|XXX|YYY|YYY|20250530154128||OUL^R22|1768820250530154128||2.5
PID|||383378^^^CS^SS~46630100^^^ZZZ^ZZZ~630110^^^PI^BDA~RSSMRA71E01F205E^^^CF^NN||ROSSI^MARIA||19710501|F|||VIA DELLA LIBERTA 52^^MILANO^^20100^^IT||3331245678^PRN^PH|||||RSSMRA71E01F205E|383378||||MILANO|||ITALIANA||||N|N
SPM|1|312713635143||SI^Siero|||||||||||||20250530150000
OBR|1||3127136351^DN^1-3127136351-20250530150000|0017^POTASSIO^V^0017@1^^DN|||20250530150000||||G|||||||||||||ZZZ-1|I||^^^20250530150000
OBX|1|CE|0017^POTASSIO^V^0017@1^^DN||3.9|mmol/L|3.5 - 5.3|N|||I|||20250530153700||"""
    
    def test_hl7_parsing(self):
        """Test parsing messaggi HL7"""
        segments = self.parser.parse_message(self.sample_hl7)
        
        self.assertIn('MSH', segments)
        self.assertIn('PID', segments)
        self.assertIn('OBR', segments)
        self.assertIn('OBX', segments)
        
    def test_fhir_conversion(self):
        """Test conversione HL7 -> FHIR"""
        patient = self.converter.convert_hl7_to_fhir(self.sample_hl7)
        
        self.assertEqual(patient.resourceType, "Patient")
        self.assertIsNotNone(patient.id)
        self.assertIsNotNone(patient.identifier)
        self.assertIsNotNone(patient.name)
        
    def test_database_operations(self):
        """Test operazioni database"""
        # Test inserimento
        patient = self.converter.convert_hl7_to_fhir(self.sample_hl7)
        patient_id = self.framework.database.save_patient(patient)
        self.assertIsNotNone(patient_id, "Salvataggio paziente fallito")
        
        # Test ricerca
        found_patient = self.framework.database.find_patient_by_id(patient.id)
        self.assertIsNotNone(found_patient, f"Paziente con id {patient.id} non trovato nel database")
        
    def test_complete_workflow(self):
        """Test workflow completo"""
        result = self.framework.process_hl7_message(self.sample_hl7)
        
        self.assertTrue(result["success"])
        self.assertIsNotNone(result["patient_id"])

def create_sample_data():
    """Crea dati di esempio per test"""
    samples = [
        {
            "hl7_message": r"""MSH|^~\&|LAB|OSPEDALE1|FSE|REGIONE|20250601120000||OUL^R22|MSG001||2.5
PID|||12345^^^CS^SS~RSSMRA85M01H501Z^^^CF^NN||ROSSI^MARIO||19850801|M|||VIA ROMA 10^^ROMA^^00100^^IT||0612345678^PRN^PH|||||RSSMRA85M01H501Z||||||||||||
OBR|1||LAB001|CBC^EMOCROMO COMPLETO|||20250601100000||||||||||||||||F||^^^20250601100000
OBX|1|NM|WBC^LEUCOCITI||7.2|10*3/uL|4.0-11.0|N|||F|||20250601110000||""",
            "description": "Paziente maschio con emocromo"
        },
        {
            "hl7_message": r"""MSH|^~\&|LAB|OSPEDALE2|FSE|REGIONE|20250601130000||OUL^R22|MSG002||2.5
PID|||67890^^^CS^SS~VRDGNN90A41F205S^^^CF^NN||VERDI^GIOVANNA||19900401|F|||VIA MILANO 25^^TORINO^^10100^^IT||0114567890^PRN^PH|||||VRDGNN90A41F205S||||||||||||
OBR|1||LAB002|GLUC^GLICEMIA|||20250601110000||||||||||||||||F||^^^20250601110000
OBX|1|NM|GLUC^GLUCOSIO||95|mg/dL|70-110|N|||F|||20250601120000||""",
            "description": "Paziente femmina con glicemia"
        }
    ]
    return samples

def run_performance_test():
    """Test performance con molti messaggi"""
    from time import time
    
    framework = FSEFramework(CONFIG["mongodb"]["connection_string"])
    samples = create_sample_data()
    
    # Test con 100 messaggi
    start_time = time()
    
    for i in range(100):
        for sample in samples:
            result = framework.process_hl7_message(sample["hl7_message"])
            if not result["success"]:
                print(f"Errore nel messaggio {i}: {result['error']}")
    
    end_time = time()
    
    print(f"Processati 200 messaggi in {end_time - start_time:.2f} secondi")
    print(f"Media: {(end_time - start_time) / 200:.4f} secondi per messaggio")

def generate_fhir_bundle(patient_ids: List[str]) -> Dict:
    """Genera un Bundle FHIR con più pazienti"""
    bundle = {
        "resourceType": "Bundle",
        "id": str(uuid.uuid4()),
        "type": "collection",
        "timestamp": datetime.now().isoformat(),
        "entry": []
    }
    
    framework = FSEFramework(CONFIG["mongodb"]["connection_string"])
    
    for patient_id in patient_ids:
        patient = framework.database.find_patient_by_id(patient_id)
        if patient:
            patient.pop('_id', None)  # Rimuove _id MongoDB
            bundle["entry"].append({
                "fullUrl": f"Patient/{patient_id}",
                "resource": patient
            })
    
    return bundle

def export_to_file(data: Dict, filename: str):
    """Esporta dati in file JSON"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Dati esportati in {filename}")
    except Exception as e:
        print(f"Errore nell'esportazione: {e}")

def main():
    """Funzione principale per setup e test"""
    print("=== Setup FSE Framework ===")
    
    # Setup database
    if setup_database():
        print("✓ Database configurato")
    else:
        print("✗ Errore configurazione database")
        return
    
    # Test framework
    print("\n=== Test Framework ===")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Crea dati di esempio
    print("\n=== Creazione dati di esempio ===")
    framework = FSEFramework(CONFIG["mongodb"]["connection_string"])
    samples = create_sample_data()
    patient_ids = []
    
    for sample in samples:
        result = framework.process_hl7_message(sample["hl7_message"])
        if result["success"]:
            patient_ids.append(result["patient_id"])
            print(f"✓ {sample['description']} - ID: {result['patient_id']}")
        else:
            print(f"✗ Errore: {result['error']}")
    
    # Genera bundle FHIR
    if patient_ids:
        print("\n=== Generazione Bundle FHIR ===")
        bundle = generate_fhir_bundle(patient_ids)
        export_to_file(bundle, "fse_bundle_example.json")
    
    # Test performance
    print("\n=== Test Performance ===")
    run_performance_test()
    
    print("\n=== Setup completato ===")

if __name__ == "__main__":
    main()
