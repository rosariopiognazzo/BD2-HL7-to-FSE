import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Flask, request, jsonify, send_from_directory, render_template
from hl7_fhir_converter import FSEFramework

# Configurazione Flask
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev')

# Configurazione MongoDB Atlas (riusa la stessa del framework)
MONGO_CONN = "mongodb+srv://rosariopiognazzo:MO22HSgdEdNdh2fF@cluster0.vim0kda.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
framework = FSEFramework(MONGO_CONN)

@app.route('/api/patients', methods=['GET'])
def get_patients():
    query = request.args.get('q', '').strip()
    patients = framework.database.get_all_patients()
    for p in patients:
        p.pop('_id', None)
    if query:
        query_lower = query.lower()
        patients = [p for p in patients if
            any(query_lower in (idn.get('value','').lower()) for idn in p.get('identifier', [])) or
            any(query_lower in (n.get('family','').lower()) for n in p.get('name', [])) or
            any(query_lower in (n.get('given',[""])[0].lower()) for n in p.get('name', []))
        ]
    return jsonify(patients)

@app.route('/api/patient/<pid>', methods=['GET'])
def get_patient(pid):
    patient = framework.database.find_patient_by_id(pid)
    if patient:
        patient.pop('_id', None)
        return jsonify(patient)
    return jsonify({'error': 'Paziente non trovato'}), 404

@app.route('/api/patient/<pid>', methods=['DELETE'])
def delete_patient(pid):
    result = framework.database.patients_collection.delete_one({'id': pid})
    if result.deleted_count:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Paziente non trovato'}), 404

@app.route('/api/hl7', methods=['POST'])
def insert_hl7():
    data = request.get_json()
    hl7_message = data.get('hl7_message', '')
    if not hl7_message.strip():
        return jsonify({'success': False, 'error': 'Messaggio HL7 mancante'}), 400
    result = framework.process_hl7_message(hl7_message)
    return jsonify(result)

@app.route('/api/patient/<pid>/lab_results', methods=['GET'])
def get_lab_results(pid):
    results = list(framework.database.lab_results_collection.find({"subject.reference": f"Patient/{pid}"}))
    for r in results:
        r.pop('_id', None)
    return jsonify(results)

@app.route('/api/raw_lab_data', methods=['GET'])
def get_raw_lab_data():
    """Recupera i dati di laboratorio raw non ancora processati"""
    try:
        # Cerca documenti con struttura di messaggi HL7 parsati
        raw_docs = list(framework.database.lab_results_collection.find({
            "segments": {"$exists": True}
        }).limit(10))
        
        for doc in raw_docs:
            # Mantieni l'ID nel suo formato originale, convertendo solo ObjectId in stringa
            if hasattr(doc['_id'], 'binary'):  # È un ObjectId
                doc['_id'] = str(doc['_id'])
            # Se è già stringa o intero, lascialo così com'è
        
        return jsonify(raw_docs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process_lab_document', methods=['POST'])
def process_lab_document():
    """Processa manualmente un documento di laboratorio"""
    try:
        data = request.get_json()
        doc_id = data.get('document_id')
        patient_id = data.get('patient_id')
        
        if not doc_id or not patient_id:
            return jsonify({'error': 'document_id e patient_id sono richiesti'}), 400
        
        # Trova il documento
        doc = framework.database.lab_results_collection.find_one({"_id": doc_id})
        if not doc:
            return jsonify({'error': 'Documento non trovato'}), 404
        
        # Verifica che il paziente esista
        patient = framework.database.find_patient_by_id(patient_id)
        if not patient:
            return jsonify({'error': 'Paziente non trovato'}), 404
        
        # Qui dovremmo processare i risultati di laboratorio e associarli al paziente
        # Per ora restituiamo successo
        
        return jsonify({
            'success': True,
            'message': f'Documento {doc_id} associato al paziente {patient_id}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/raw_lab_data/<doc_id>', methods=['GET'])
def get_raw_lab_detail(doc_id):
    """Recupera i dettagli di un singolo documento di laboratorio"""
    try:
        from bson import ObjectId
        
        # Prova diversi formati di ID
        doc = None
        
        # 1. Prova con stringa diretta
        doc = framework.database.lab_results_collection.find_one({"_id": doc_id})
        
        # 2. Se non trovato, prova con ObjectId
        if not doc:
            try:
                doc = framework.database.lab_results_collection.find_one({"_id": ObjectId(doc_id)})
            except:
                pass
        
        # 3. Se ancora non trovato, prova come intero
        if not doc:
            try:
                doc = framework.database.lab_results_collection.find_one({"_id": int(doc_id)})
            except:
                pass
        
        if not doc:
            return jsonify({'error': f'Documento con ID {doc_id} non trovato'}), 404
        
        # Estrai i dettagli dal documento
        details = extract_lab_details_from_document(doc)
        
        return jsonify(details)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def extract_lab_details_from_document(doc):
    """Estrae i dettagli dei test di laboratorio dal documento parsato"""
    details = {
        'document_id': str(doc.get('_id', '')),
        'timestamp': doc.get('timestamp', ''),
        'message_type': doc.get('messageType', ''),
        'sending_application': doc.get('sendingApplication', ''),
        'receiving_application': doc.get('receivingApplication', ''),
        'patient_info': {},
        'lab_results': []
    }
    
    try:
        # Estrai informazioni dal primo segmento MSH che contiene tutti i dati
        segments = doc.get('segments', [])
        msh_segment = None
        
        for segment in segments:
            if segment.get('type') == 'MSH' and len(segment.get('fields', [])) > 1:
                msh_segment = segment
                break
        
        if msh_segment and len(msh_segment.get('fields', [])) > 20:
            fields = msh_segment.get('fields', [])
            
            # Estrai informazioni paziente
            if len(fields) > 14:
                details['patient_info'] = {
                    'identifiers': fields[14] if len(fields) > 14 else '',
                    'name': fields[16] if len(fields) > 16 else '',
                    'birth_date': fields[18] if len(fields) > 18 else '',
                    'gender': fields[19] if len(fields) > 19 else '',
                    'address': fields[20] if len(fields) > 20 else '',
                    'phone': fields[22] if len(fields) > 22 else ''
                }
            
            # Estrai risultati di laboratorio
            lab_results = []
            
            # Cerca pattern per i risultati (basandoci sulla struttura osservata)
            i = 0
            while i < len(fields):
                field = fields[i]
                
                # Cerca pattern di test di laboratorio con codice^nome^V^codice2
                if isinstance(field, str) and '^' in field and ('POTASSIO' in field.upper() or 'SODIO' in field.upper() or 'EMOLISI' in field.upper() or 'ITTERO' in field.upper() or 'LIPEMIA' in field.upper()):
                    parts = field.split('^')
                    if len(parts) >= 2:
                        test_code = parts[0]
                        test_name = parts[1]
                        
                        # Cerca il valore nei campi successivi
                        value = None
                        unit = None
                        reference_range = None
                        
                        # Guarda i prossimi campi per valore, unità e range
                        for j in range(i + 1, min(i + 10, len(fields))):
                            next_field = fields[j]
                            
                            # Se troviamo un numero seguito da unità
                            if isinstance(next_field, str) and next_field.replace('.', '').replace('-', '').isdigit():
                                value = next_field
                                
                                # Controlla se il campo successivo è l'unità
                                if j + 1 < len(fields) and isinstance(fields[j + 1], str) and ('mmol/L' in fields[j + 1] or 'mg/dL' in fields[j + 1] or 'g/L' in fields[j + 1]):
                                    unit = fields[j + 1]
                                
                                # Controlla se c'è un range di riferimento
                                if j + 2 < len(fields) and isinstance(fields[j + 2], str) and (' - ' in fields[j + 2] or '>' in fields[j + 2] or '<' in fields[j + 2]):
                                    reference_range = fields[j + 2]
                                
                                break
                        
                        lab_result = {
                            'test_code': test_code,
                            'test_name': test_name,
                            'value': value,
                            'unit': unit,
                            'reference_range': reference_range,
                            'status': 'final'
                        }
                        
                        lab_results.append(lab_result)
                
                i += 1
            
            details['lab_results'] = lab_results
            
    except Exception as e:
        print(f"Errore nell'estrazione dettagli: {e}")
    
    return details

@app.route('/', methods=['GET'])
def serve_home_page():
    """Endpoint per servire la homepage della webapp."""
    return render_template('app.html')

@app.route('/app.html', methods=['GET'])
def serve_app_page():
    """Endpoint per servire la pagina HTML principale della webapp."""
    return render_template('app.html')

if __name__ == '__main__':
    app.run(debug=True)
