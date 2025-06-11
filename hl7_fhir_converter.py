"""
Framework per conversione dati HL7 ORU -> FHIR -> MongoDB
Progetto Basi di Dati 2
"""

import json
from typing import Dict, List, Optional, Any
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dataclasses import dataclass, field
import uuid

# Modelli dati FHIR
@dataclass
class FHIRIdentifier:
    system: str
    value: str
    extension: Optional[List[Dict]] = None

@dataclass
class FHIRName:
    family: str
    given: List[str]

@dataclass
class FHIRTelecom:
    system: str
    value: str

@dataclass
class FHIRAddress:
    use: str
    line: List[str]
    city: str
    postalCode: str
    country: str
    extension: Optional[List[Dict]] = None

@dataclass
class FHIRContact:
    relationship: List[Dict]
    name: FHIRName
    telecom: List[FHIRTelecom]

@dataclass
class FHIRPatient:
    resourceType: str = "Patient"
    id: str = ""
    meta: Dict = field(default_factory=dict)
    identifier: List[FHIRIdentifier] = field(default_factory=list)
    name: List[FHIRName] = field(default_factory=list)
    telecom: List[FHIRTelecom] = field(default_factory=list)
    gender: str = ""
    birthDate: str = ""
    address: List[FHIRAddress] = field(default_factory=list)
    contact: List[FHIRContact] = field(default_factory=list)
    extension: List[Dict] = field(default_factory=list)

class HL7Parser:
    """Parser per messaggi HL7 v2.5"""
    
    def __init__(self):
        self.field_separator = '|'
        self.component_separator = '^'
        self.repetition_separator = '~'
        self.escape_separator = '\\'
        self.subcomponent_separator = '&'
    
    def parse_message(self, hl7_message: str) -> Dict[str, List[str]]:
        """Parsa un messaggio HL7 e restituisce un dizionario con i segmenti"""
        segments = {}
        lines = hl7_message.strip().split('\n')
        
        for line in lines:
            if line.strip():
                segment_type = line[:3]
                if segment_type not in segments:
                    segments[segment_type] = []
                segments[segment_type].append(line)
        
        return segments
    
    def parse_segment(self, segment: str) -> List[str]:
        """Parsa un singolo segmento HL7"""
        return segment.split(self.field_separator)
    
    def parse_field(self, field: str) -> List[str]:
        """Parsa un campo con componenti multiple"""
        if not field:
            return []
        return field.split(self.component_separator)
    
    def parse_repetition(self, field: str) -> List[str]:
        """Parsa ripetizioni in un campo"""
        if not field:
            return []
        return field.split(self.repetition_separator)

class FHIRConverter:
    """Convertitore da HL7 a FHIR"""
    
    def __init__(self):
        self.parser = HL7Parser()
    
    def convert_hl7_to_fhir(self, hl7_message: str) -> FHIRPatient:
        """Converte un messaggio HL7 in una risorsa FHIR Patient"""
        segments = self.parser.parse_message(hl7_message)
        
        # Genera ID univoco
        patient_id = str(uuid.uuid4())
        
        # Crea risorsa FHIR Patient
        patient = FHIRPatient(id=patient_id)
        patient.meta = {
            "profile": ["http://hl7.it/fhir/lab-report/StructureDefinition/patient-it-lab"]
        }
        
        # Processa segmento PID (Patient Identification)
        if 'PID' in segments:
            pid_segment = self.parser.parse_segment(segments['PID'][0])
            patient = self._process_pid_segment(patient, pid_segment)
        else:
            raise ValueError("Messaggio HL7 senza segmento PID: impossibile estrarre dati paziente.")
        # Gli altri segmenti (OBR, OBX, TXA, ecc.) sono ignorati per ora
        return patient
    
    def _process_pid_segment(self, patient: FHIRPatient, pid_fields: List[str]) -> FHIRPatient:
        """Processa il segmento PID"""
        try:
            # PID.3 - Patient Identifier List
            if len(pid_fields) > 3 and pid_fields[3]:
                patient.identifier = self._extract_identifiers(pid_fields[3])
            
            # PID.5 - Patient Name
            if len(pid_fields) > 5 and pid_fields[5]:
                patient.name = self._extract_names(pid_fields[5])
            
            # PID.7 - Date/Time of Birth
            if len(pid_fields) > 7 and pid_fields[7]:
                patient.birthDate = self._convert_hl7_date(pid_fields[7])
            
            # PID.8 - Administrative Sex
            if len(pid_fields) > 8 and pid_fields[8]:
                patient.gender = self._convert_gender(pid_fields[8])
            
            # PID.11 - Patient Address
            if len(pid_fields) > 11 and pid_fields[11]:
                patient.address = self._extract_addresses(pid_fields[11])
            
            # PID.13 - Phone Number - Home
            if len(pid_fields) > 13 and pid_fields[13]:
                patient.telecom = self._extract_telecom(pid_fields[13])
            
        except Exception as e:
            print(f"Errore nel processare PID: {e}")
        
        return patient
    
    def _extract_identifiers(self, identifier_field: str) -> List[FHIRIdentifier]:
        """Estrae gli identificatori dal campo PID.3"""
        identifiers = []
        repetitions = self.parser.parse_repetition(identifier_field)
        
        for rep in repetitions:
            components = self.parser.parse_field(rep)
            if len(components) >= 5:
                id_value = components[0]
                id_system = components[4]
                
                # Mappa i sistemi di identificazione
                if id_system == "CF":
                    system = "http://hl7.it/sid/codiceFiscale"
                elif id_system == "SS":
                    system = "http://hl7.it/sid/tessera-sanitaria"
                else:
                    system = f"http://sistema.locale/{id_system}"
                
                identifiers.append(FHIRIdentifier(
                    system=system,
                    value=id_value
                ))
        
        return identifiers
    
    def _extract_names(self, name_field: str) -> List[FHIRName]:
        """Estrae i nomi dal campo PID.5"""
        names = []
        components = self.parser.parse_field(name_field)
        
        if len(components) >= 2:
            family = components[0]
            given = [components[1]] if components[1] else []
            
            names.append(FHIRName(
                family=family,
                given=given
            ))
        
        return names
    
    def _extract_addresses(self, address_field: str) -> List[FHIRAddress]:
        """Estrae gli indirizzi dal campo PID.11"""
        addresses = []
        repetitions = self.parser.parse_repetition(address_field)
        
        for rep in repetitions:
            components = self.parser.parse_field(rep)
            if len(components) >= 7:
                street = components[0] if components[0] else ""
                city = components[2] if components[2] else ""
                postal_code = components[4] if components[4] else ""
                country = components[6] if components[6] else "IT"
                
                addresses.append(FHIRAddress(
                    use="home",
                    line=[street] if street else [],
                    city=city,
                    postalCode=postal_code,
                    country=country
                ))
        
        return addresses
    
    def _extract_telecom(self, telecom_field: str) -> List[FHIRTelecom]:
        """Estrae i contatti telefonici"""
        telecoms = []
        repetitions = self.parser.parse_repetition(telecom_field)
        
        for rep in repetitions:
            components = self.parser.parse_field(rep)
            if len(components) >= 1:
                phone_number = components[0]
                telecoms.append(FHIRTelecom(
                    system="phone",
                    value=phone_number
                ))
        
        return telecoms
    
    def _convert_hl7_date(self, hl7_date: str) -> str:
        """Converte data HL7 (YYYYMMDD) in formato FHIR (YYYY-MM-DD)"""
        if len(hl7_date) >= 8:
            year = hl7_date[:4]
            month = hl7_date[4:6]
            day = hl7_date[6:8]
            return f"{year}-{month}-{day}"
        return hl7_date
    
    def _convert_gender(self, hl7_gender: str) -> str:
        """Converte codice sesso HL7 in formato FHIR"""
        gender_map = {
            'M': 'male',
            'F': 'female',
            'U': 'unknown',
            'O': 'other'
        }
        return gender_map.get(hl7_gender.upper(), 'unknown')

class FHIRObservation:
    def __init__(self, patient_id, obx_fields, obr_fields=None):
        self.resourceType = "Observation"
        self.subject = {"reference": f"Patient/{patient_id}"}
        self.status = "final"
        self.code = {}
        self.value = None
        self.unit = None
        self.referenceRange = None
        self.issued = None
        # OBR: info esame
        if obr_fields and len(obr_fields) > 4:
            code_comp = obr_fields[4].split("^")
            if len(code_comp) > 1 and code_comp[0] and code_comp[1]:
                self.code = {"coding": [{"code": code_comp[0], "display": code_comp[1]}]}
        # OBX: valore
        if obx_fields and len(obx_fields) > 3:
            code_comp = obx_fields[3].split("^")
            if len(code_comp) > 1 and code_comp[0] and code_comp[1]:
                self.code = {"coding": [{"code": code_comp[0], "display": code_comp[1]}]}
        if obx_fields and len(obx_fields) > 5 and obx_fields[5]:
            self.value = obx_fields[5]
        if obx_fields and len(obx_fields) > 6 and obx_fields[6]:
            self.unit = obx_fields[6]
        if obx_fields and len(obx_fields) > 7 and obx_fields[7]:
            self.referenceRange = obx_fields[7]
        if obx_fields and len(obx_fields) > 14 and obx_fields[14]:
            self.issued = obx_fields[14]

class FSEDatabase:
    """Gestore database MongoDB per FSE"""
    
    def __init__(self, connection_string: str = "mongodb://localhost:27017/", db_name: str = "fse_database"):
        self.client = MongoClient(connection_string, server_api=ServerApi('1'))
        self.db = self.client[db_name]
        self.patients_collection = self.db.patients
        self.lab_results_collection = self.db.lab_results
        
        # Crea indici per performance
        self._create_indexes()
    
    def _create_indexes(self):
        """Crea indici per ottimizzare le query"""
        # Indice su codice fiscale
        self.patients_collection.create_index([("identifier.value", 1)], unique=True)
        # Indice su ID paziente
        self.patients_collection.create_index([("id", 1)], unique=True)
        # Indice su data di nascita
        self.patients_collection.create_index([("birthDate", 1)])
    
    def save_patient(self, patient: FHIRPatient) -> str:
        """Salva un paziente nel database"""
        try:
            patient_dict = self._fhir_to_dict(patient)
            identifier_list = patient_dict.get('identifier', [])
            identifier_value = identifier_list[0]['value'] if identifier_list else None
            existing = self.find_patient_by_identifier(identifier_value) if identifier_value else None
            if existing:
                self.patients_collection.update_one(
                    {"_id": existing["_id"]},
                    {"$set": patient_dict}
                )
                return existing["id"]
            else:
                result = self.patients_collection.insert_one(patient_dict)
                return patient_dict["id"]
        except Exception as e:
            print(f"Errore nel salvare il paziente: {e}")
            return ""
    
    def find_patient_by_identifier(self, identifier_value: str) -> Optional[Dict]:
        """Trova un paziente tramite identificatore"""
        return self.patients_collection.find_one({
            "identifier.value": identifier_value
        })
    
    def find_patient_by_id(self, patient_id: str) -> Optional[Dict]:
        """Trova un paziente tramite ID"""
        return self.patients_collection.find_one({"id": patient_id})
    
    def get_all_patients(self) -> List[Dict]:
        """Restituisce tutti i pazienti"""
        return list(self.patients_collection.find())
    
    def _fhir_to_dict(self, fhir_object) -> Dict:
        """Converte oggetto FHIR in dizionario per MongoDB"""
        if hasattr(fhir_object, '__dict__'):
            result = {}
            for key, value in fhir_object.__dict__.items():
                if value is not None:
                    if isinstance(value, list):
                        result[key] = [self._fhir_to_dict(item) for item in value]
                    elif hasattr(value, '__dict__'):
                        result[key] = self._fhir_to_dict(value)
                    else:
                        result[key] = value
            return result
        else:
            return fhir_object
    
    def save_lab_results(self, patient_id: str, obx_segments: List[List[str]], obr_segments: Optional[List[List[str]]] = None):
        """Salva risultati OBX/OBR come Observation, evitando duplicati per paziente/codice/data"""
        count = 0
        obr_map = {i+1: obr for i, obr in enumerate(obr_segments)} if obr_segments else {}
        for idx, obx in enumerate(obx_segments):
            obr = obr_map.get(idx+1)
            obs = FHIRObservation(patient_id, obx, obr)
            obs_dict = obs.__dict__
            obs_dict["subject"] = obs.subject
            # Criterio di unicità: paziente, codice, data (issued)
            code = obs.code["coding"][0]["code"] if obs.code and "coding" in obs.code and obs.code["coding"] else None
            issued = obs.issued
            # Evita duplicati
            if code:
                exists = self.lab_results_collection.find_one({
                    "subject.reference": f"Patient/{patient_id}",
                    "code.coding.code": code,
                    "issued": issued
                })
                if exists:
                    continue
            self.lab_results_collection.insert_one(obs_dict)
            count += 1
        return count
    
    def fix_lab_results_references(self):
        """Fix per aggiornare i lab_results con subject.reference vuoto usando l'id del paziente."""
        num_patients = self.patients_collection.count_documents({})
        if num_patients == 1:
            patient = self.patients_collection.find_one({})
            patient_id = patient["id"]
            result = self.lab_results_collection.update_many(
                {"subject.reference": "Patient/"},
                {"$set": {"subject.reference": f"Patient/{patient_id}"}}
            )
            print(f"Aggiornati {result.modified_count} lab_results con Patient/{patient_id}")
        else:
            print("Fix automatico non sicuro: ci sono più pazienti nel database. Serve una logica di matching più raffinata.")

class FSEFramework:
    """Framework principale per gestione FSE"""
    
    def __init__(self, mongo_connection: str = "mongodb://localhost:27017/"):
        self.converter = FHIRConverter()
        self.database = FSEDatabase(mongo_connection)
    
    def process_hl7_message(self, hl7_message: str) -> Dict[str, Any]:
        """Processa un messaggio HL7 completo"""
        try:
            # Converte HL7 in FHIR
            fhir_patient = self.converter.convert_hl7_to_fhir(hl7_message)
            
            # Salva in database
            patient_id = self.database.save_patient(fhir_patient)
            
            # Estrai segmenti OBX/OBR
            parser = self.converter.parser
            segments = parser.parse_message(hl7_message)
            obx_segments = [parser.parse_segment(s) for s in segments.get('OBX',[])]
            obr_segments = [parser.parse_segment(s) for s in segments.get('OBR',[])]
            n_obs = self.database.save_lab_results(patient_id, obx_segments, obr_segments)
            return {
                "success": True,
                "patient_id": patient_id,
                "lab_results": n_obs,
                "message": f"Paziente e {n_obs} risultati processati con successo"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Errore nel processare il messaggio HL7"
            }
    
    def get_patient_fse(self, identifier: str) -> Optional[Dict]:
        """Recupera FSE paziente tramite identificatore"""
        return self.database.find_patient_by_identifier(identifier)
    
    def export_patient_fhir(self, patient_id: str) -> Optional[str]:
        """Esporta paziente in formato FHIR JSON"""
        patient = self.database.find_patient_by_id(patient_id)
        if patient:
            # Rimuove _id di MongoDB per esportazione pulita
            patient.pop('_id', None)
            return json.dumps(patient, indent=2, ensure_ascii=False)
        return None

# Esempio di utilizzo
if __name__ == "__main__":
    # Inizializza framework
    fse_framework = FSEFramework()
    
    # Messaggio HL7 di esempio (dal tuo file)
    hl7_sample = r"""MSH|^~\&|XXX|XXX|YYY|YYY|20250530154128||OUL^R22|1768820250530154128||2.5
PID|||383378^^^CS^SS~46630100^^^ZZZ^ZZZ~630110^^^PI^BDA~CODICEFISCALE^^^CF^NN||COGNOME^NOME||19780319|F|||VIA DI RESIDENZA^^DESC.COMUNE^^CAP^^L^^COD.COMUNE~^^COD.COMUNE^^^^^^COD.COMUNE||RECAPITO TEL^PRN^PH^^^^^^^^RECAPITO TEL^y|||||CPDICEFISCALE|383378||||COD.COMUNE|||CITTADINANZA||||N|N"""
    
    # Processa messaggio
    result = fse_framework.process_hl7_message(hl7_sample)
    print("Risultato processamento:", result)
    
    # Esempio query
    if result["success"]:
        # Recupera paziente
        patient_fse = fse_framework.get_patient_fse("CODICEFISCALE")
        if patient_fse:
            print("FSE trovato per paziente")
            
            # Esporta in FHIR
            fhir_export = fse_framework.export_patient_fhir(patient_fse["id"])
            print("Export FHIR:", fhir_export[:200] + "..." if fhir_export else "Nessun export")
