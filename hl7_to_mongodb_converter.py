import json
from datetime import datetime

def parse_hl7_message(hl7_text):
    """Parsa un messaggio HL7 e lo converte in un dizionario."""
    segments = hl7_text.split('\r')
    parsed_message = {
        "messageHeader": None,
        "parsedAt": datetime.now().isoformat(),
        "segments": []
    }

    for segment in segments:
        if segment.strip():
            fields = segment.split('|')
            segment_type = fields[0]
            parsed_message["segments"].append({
                "type": segment_type,
                "fields": fields
            })

            if segment_type == "MSH":
                parsed_message["messageHeader"] = {
                    "sendingApplication": fields[2],
                    "receivingApplication": fields[4],
                    "timestamp": fields[6],
                    "messageType": fields[8],
                    "messageId": fields[9]
                }

    # Separazione dei segmenti concatenati
    new_segments = []
    for segment in parsed_message["segments"]:
        for i, field in enumerate(segment["fields"]):
            if '\n' in field:
                extra_segments = field.split('\n')
                segment["fields"][i] = extra_segments[0]
                for extra_segment in extra_segments[1:]:
                    fields = extra_segment.split('|')
                    new_segments.append({
                        "type": fields[0],
                        "fields": fields
                    })
    parsed_message["segments"].extend(new_segments)

    return parsed_message

def transform_hl7_to_mongodb(parsed_hl7):
    """Trasforma un messaggio HL7 parsato in un documento MongoDB."""
    document = {
        "_id": parsed_hl7["messageHeader"]["messageId"],
        "messageType": parsed_hl7["messageHeader"]["messageType"],
        "timestamp": parsed_hl7["messageHeader"]["timestamp"],
        "sendingApplication": parsed_hl7["messageHeader"]["sendingApplication"],
        "receivingApplication": parsed_hl7["messageHeader"]["receivingApplication"],
        "segments": parsed_hl7["segments"],
        "metadata": {
            "parsedAt": parsed_hl7["parsedAt"],
            "warnings": []
        }
    }

    return document

def convert_hl7_file_to_json(file_path):
    """Legge un file HL7 e lo converte in JSON per MongoDB."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            hl7_text = file.read()
            parsed_hl7 = parse_hl7_message(hl7_text)
            mongodb_document = transform_hl7_to_mongodb(parsed_hl7)
            return json.dumps(mongodb_document, indent=4)
    except Exception as e:
        print(f"Errore durante la conversione del file {file_path}: {e}")
        return None

if __name__ == "__main__":
    # Esempio di utilizzo
    file_paths = [
        "c:\\Users\\nunzi\\Documents\\BD2-HL7-to-FSE\\dati\\datiORB1.txt",
        "c:\\Users\\nunzi\\Documents\\BD2-HL7-to-FSE\\dati\\datiORB2.txt",
        "c:\\Users\\nunzi\\Documents\\BD2-HL7-to-FSE\\dati\\datiORB3_DOM.txt"
    ]

    for file_path in file_paths:
        json_output = convert_hl7_file_to_json(file_path)
        if json_output:
            output_file = file_path.replace('.txt', '.json')
            with open(output_file, 'w', encoding='utf-8') as json_file:
                json_file.write(json_output)
            print(f"File JSON generato: {output_file}")
