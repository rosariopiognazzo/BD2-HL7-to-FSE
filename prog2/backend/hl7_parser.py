import re
from datetime import datetime
import json

class HL7Parser:
    """
    Parser per convertire messaggi HL7 in JSON seguendo le strutture definite in HL7_Parsing_Approach.md
    """
    
    def __init__(self):
        self.field_separator = '|'
        self.component_separator = '^'
        self.subcomponent_separator = '&'
        self.repetition_separator = '~'
        self.escape_character = '\\'
        
    def parse_hl7_message(self, hl7_text):
        """
        Parse un messaggio HL7 completo e restituisce JSON
        """
        segments = hl7_text.strip().split('\r\n')
        if not segments:
            return {"error": "Nessun segmento trovato"}
            
        # Identifica il tipo di messaggio dal segmento MSH
        msh_segment = segments[0] if segments else ""
        message_type = self._get_message_type(msh_segment)
        
        print(f"Debug - Tipo di messaggio identificato: '{message_type}'")
        
        if message_type == "MDM":
            print("Debug - chiamando _parse_mdm_message")
            return self._parse_mdm_message(segments)
        elif message_type == "OUL":
            print("Debug - chiamando _parse_oul_message")
            return self._parse_oul_message(segments)
        elif message_type == "ORU":
            print("Debug - chiamando _parse_oru_message")
            return self._parse_oru_message(segments)
        else:
            return {"error": f"Tipo di messaggio non supportato: {message_type}"}
        
    def _get_message_type(self, msh_segment):
        """Estrae il tipo di messaggio dal segmento MSH"""
        fields = msh_segment.split(self.field_separator)
        
        # Debug: stampa tutti i campi per capire la struttura
        print(f"Debug - Numero di campi MSH: {len(fields)}")
        for i, field in enumerate(fields):
            print(f"Campo {i}: '{field}'")
        
        # Il tipo di messaggio può essere in MSH-9 (indice 8) o MSH-10 (indice 9)
        # Controlla prima MSH-9
        if len(fields) > 8 and fields[8] and '^' in fields[8]:
            message_type_field = fields[8]
            components = message_type_field.split(self.component_separator)
            message_type = components[0] if components else ""
            print(f"Debug - Tipo messaggio da MSH-9: '{message_type}'")
            return message_type
        
        # Controlla MSH-10 se MSH-9 è vuoto
        if len(fields) > 9 and fields[9] and '^' in fields[9]:
            message_type_field = fields[9]
            components = message_type_field.split(self.component_separator)
            message_type = components[0] if components else ""
            print(f"Debug - Tipo messaggio da MSH-10: '{message_type}'")
            return message_type
        
        # Cerca in tutti i campi che contengono ^
        for i, field in enumerate(fields):
            if field and '^' in field:
                components = field.split(self.component_separator)
                if components[0] in ['MDM', 'OUL', 'ORU', 'ADT', 'ORM', 'ACK']:
                    print(f"Debug - Tipo messaggio trovato nel campo {i}: '{components[0]}'")
                    return components[0]
        
        # Ultimo tentativo: cerca pattern direttamente
        for i, field in enumerate(fields):
            if field:
                for msg_type in ['MDM', 'OUL', 'ORU']:
                    if field.startswith(msg_type):
                        print(f"Debug - Tipo messaggio trovato per pattern nel campo {i}: '{msg_type}'")
                        return msg_type
        
        print(f"Debug - Nessun tipo di messaggio trovato")
        return ""
    
    def _parse_field(self, field):
        """Parse un campo HL7 gestendo componenti e subcomponenti"""
        if not field:
            return ""
        
        # Gestisce ripetizioni
        repetitions = field.split(self.repetition_separator)
        if len(repetitions) > 1:
            return [self._parse_components(rep) for rep in repetitions]
        
        return self._parse_components(field)
    
    def _parse_components(self, field):
        """Parse i componenti di un campo"""
        components = field.split(self.component_separator)
        if len(components) == 1:
            return field
        
        result = {}
        for i, component in enumerate(components):
            if component:
                subcomponents = component.split(self.subcomponent_separator)
                if len(subcomponents) > 1:
                    result[f"component_{i+1}"] = subcomponents
                else:
                    result[f"component_{i+1}"] = component
        
        return result if result else field
    
    def _parse_mdm_message(self, segments):
        """Parse messaggio MDM secondo la struttura definita"""
        result = {
            "message_metadata": {},
            "event_information": {},
            "patient_identification": {},
            "patient_visit": {},
            "document_header": {}
        }
        
        for segment in segments:
            segment_type = segment[:3] if len(segment) >= 3 else ""
            fields = segment.split(self.field_separator)
            
            if segment_type == "MSH":
                result["message_metadata"] = self._parse_msh_segment(fields)
            elif segment_type == "EVN":
                result["event_information"] = self._parse_evn_segment(fields)
            elif segment_type == "PID":
                result["patient_identification"] = self._parse_pid_segment(fields)
            elif segment_type == "PV1":
                result["patient_visit"] = self._parse_pv1_segment(fields)
            elif segment_type == "TXA":
                result["document_header"] = self._parse_txa_segment(fields)
        
        return result
    
    def _parse_oul_message(self, segments):
        """Parse messaggio OUL secondo la struttura definita"""
        result = {
            "message_metadata": {},
            "patient_identification": {},
            "specimens": []
        }
        
        current_specimen = None
        current_observation_request = None
        
        for segment in segments:
            segment_type = segment[:3] if len(segment) >= 3 else ""
            fields = segment.split(self.field_separator)
            
            print(f"Debug - Processando segmento: {segment_type}")
            
            if segment_type == "MSH":
                result["message_metadata"] = self._parse_msh_segment(fields)
            elif segment_type == "PID":
                result["patient_identification"] = self._parse_pid_segment(fields)
            elif segment_type == "SPM":
                current_specimen = self._parse_spm_segment(fields)
                # Inizializza la lista delle observation_requests per questo specimen
                current_specimen["observation_requests"] = []
                result["specimens"].append(current_specimen)
            elif segment_type == "OBR":
                current_observation_request = self._parse_obr_segment(fields)
                # Inizializza la lista delle observations per questa request
                current_observation_request["observations"] = []
                # Se abbiamo uno specimen corrente, aggiungi la request ad esso
                if isinstance(current_specimen, dict) and "observation_requests" in current_specimen and isinstance(current_specimen["observation_requests"], list):
                    current_specimen["observation_requests"].append(current_observation_request)
                else:
                    # Se non c'è uno specimen, crea una sezione generale
                    if "observation_requests" not in result or not isinstance(result["observation_requests"], list):
                        result["observation_requests"] = []
                    result["observation_requests"].append(current_observation_request)
            elif segment_type == "ORC":
                # Parsing del segmento ORC (Order Common)
                orc_data = self._parse_orc_segment(fields)
                if current_observation_request:
                    current_observation_request["order_common"] = orc_data
            elif segment_type == "TQ1":
                # Parsing del segmento TQ1 (Timing/Quantity)
                tq1_data = self._parse_tq1_segment(fields)
                if current_observation_request:
                    current_observation_request["timing_quantity"] = tq1_data
            elif segment_type == "OBX":
                obx_data = self._parse_obx_segment(fields)
                if current_observation_request:
                    if "observations" not in current_observation_request or not isinstance(current_observation_request["observations"], list):
                        current_observation_request["observations"] = []
                    current_observation_request["observations"].append(obx_data)
                else:
                    # Se non c'è una observation_request corrente, crea una sezione generale
                    if "observations" not in result:
                        result["observations"] = []
                    result["observations"].append(obx_data)
        
        return result
    
    def _parse_tq1_segment(self, fields):
        """Parse del segmento TQ1"""
        return {
            "set_id": fields[1] if len(fields) > 1 else "",
            "quantity": fields[2] if len(fields) > 2 else "",
            "repeat_pattern": fields[3] if len(fields) > 3 else "",
            "explicit_time": fields[4] if len(fields) > 4 else "",
            "relative_time": fields[5] if len(fields) > 5 else "",
            "service_duration": fields[6] if len(fields) > 6 else "",
            "start_date_time": fields[7] if len(fields) > 7 else "",
            "end_date_time": fields[8] if len(fields) > 8 else "",
            "priority": fields[9] if len(fields) > 9 else "",
            "condition_text": fields[10] if len(fields) > 10 else ""
        }
        
    def _parse_oru_message(self, segments):
        """Parse messaggio ORU secondo la struttura definita"""
        result = {
            "message_metadata": {},
            "patient_identification": {},
            "patient_visit": {},
            "observation_report": []
        }
        
        current_observation_request = None
        
        for segment in segments:
            segment_type = segment[:3] if len(segment) >= 3 else ""
            fields = segment.split(self.field_separator)
            
            if segment_type == "MSH":
                result["message_metadata"] = self._parse_msh_segment(fields)
            elif segment_type == "PID":
                result["patient_identification"] = self._parse_pid_segment(fields)
            elif segment_type == "PV1":
                result["patient_visit"] = self._parse_pv1_segment(fields)
            elif segment_type == "OBR":
                current_observation_request = self._parse_obr_segment(fields)
                result["observation_report"].append(current_observation_request)
            elif segment_type == "OBX":
                obx_data = self._parse_obx_segment(fields)
                if current_observation_request:
                    if "observations" not in current_observation_request or not isinstance(current_observation_request["observations"], list):
                        current_observation_request["observations"] = []
                    current_observation_request["observations"].append(obx_data)
        
        return result
    
    def _parse_msh_segment(self, fields):
        """Parse del segmento MSH"""
        return {
            "sending_application": fields[2] if len(fields) > 2 else "",
            "sending_facility": fields[3] if len(fields) > 3 else "",
            "receiving_application": fields[4] if len(fields) > 4 else "",
            "receiving_facility": fields[5] if len(fields) > 5 else "",
            "date_time_of_message": fields[6] if len(fields) > 6 else "",
            "message_type": fields[8] if len(fields) > 8 else "",
            "message_control_id": fields[9] if len(fields) > 9 else "",
            "processing_id": fields[10] if len(fields) > 10 else "",
            "version_id": fields[11] if len(fields) > 11 else ""
        }
    
    def _parse_evn_segment(self, fields):
        """Parse segmento EVN (Event Type)"""
        return {
        "event_type_code": fields[1] if len(fields) > 1 else "",
        "recorded_date_time": fields[2] if len(fields) > 2 else ""
    }
    
    def _parse_pid_segment(self, fields):
        """Parse segmento PID (Patient Identification)"""
        return {
        "patient_id": fields[3] if len(fields) > 3 else "",
        "patient_name": fields[5] if len(fields) > 5 else "",
        "date_of_birth": fields[7] if len(fields) > 7 else "",
        "sex": fields[8] if len(fields) > 8 else "",
        "address": fields[11] if len(fields) > 11 else ""
    }
    
    def _parse_pv1_segment(self, fields):
        """Parse segmento PV1 (Patient Visit)"""
        return {
        "patient_class": fields[2] if len(fields) > 2 else "",
        "assigned_patient_location": fields[3] if len(fields) > 3 else "",
        "visit_number": fields[19] if len(fields) > 19 else ""
    }
    
    def _parse_txa_segment(self, fields):
        """Parse segmento TXA (Document Header)"""
        result = {
            "set_id": fields[1] if len(fields) > 1 else "",
            "document_type": fields[2] if len(fields) > 2 else "",
            "activity_datetime": fields[6] if len(fields) > 6 else "",
            "originators": [],
            "unique_document_number": fields[12] if len(fields) > 12 else "",
            "document_completion_status": fields[16] if len(fields) > 16 else "",
            "document_confidentiality_status": fields[17] if len(fields) > 17 else "",
            "document_availability_status": fields[19] if len(fields) > 19 else "",
            "unique_document_filename": fields[22] if len(fields) > 22 else ""
        }
        
        # TXA-9: Originators
        if len(fields) > 9 and fields[9]:
            originator_components = fields[9].split(self.component_separator)
            if len(originator_components) >= 2:
                result["originators"].append({
                    "id": originator_components[0],
                    "name": originator_components[1]
                })
        
        return result
    
    def _parse_spm_segment(self, fields):
        """Parse segmento SPM (Specimen)"""
        return {
        "set_id": fields[1] if len(fields) > 1 else "",
        "specimen_id": fields[2] if len(fields) > 2 else "",
        "specimen_type": fields[4] if len(fields) > 4 else "",
        "collection_date_time": fields[17] if len(fields) > 17 else ""
    }
    
    def _parse_obr_segment(self, fields):
        """Parse segmento OBR (Observation Request)"""
        return {
        "set_id": fields[1] if len(fields) > 1 else "",
        "placer_order_number": fields[2] if len(fields) > 2 else "",
        "filler_order_number": fields[3] if len(fields) > 3 else "",
        "universal_service_id": fields[4] if len(fields) > 4 else "",
        "observation_date_time": fields[7] if len(fields) > 7 else "",
        "result_status": fields[25] if len(fields) > 25 else ""
    }
    
    def _parse_obx_segment(self, fields):
        """Parse segmento OBX (Observation/Result)"""
        return {
        "set_id": fields[1] if len(fields) > 1 else "",
        "value_type": fields[2] if len(fields) > 2 else "",
        "observation_identifier": fields[3] if len(fields) > 3 else "",
        "observation_value": fields[5] if len(fields) > 5 else "",
        "units": fields[6] if len(fields) > 6 else "",
        "reference_range": fields[7] if len(fields) > 7 else "",
        "observation_result_status": fields[11] if len(fields) > 11 else "",
        "date_time_of_observation": fields[14] if len(fields) > 14 else ""
    }
    
    def _parse_orc_segment(self, fields):
        """Parse segmento ORC (Common Order)"""
        return {
            "order_control": fields[1] if len(fields) > 1 else "",
            "placer_order_number": fields[2] if len(fields) > 2 else "",
            "filler_order_number": fields[3] if len(fields) > 3 else "",
            "order_status": fields[5] if len(fields) > 5 else "",
            "transaction_datetime": fields[9] if len(fields) > 9 else ""
        }
